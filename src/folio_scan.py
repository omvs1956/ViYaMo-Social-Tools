#!/usr/bin/env python3
"""folio_scan.py — find printed page numbers (folios) stored inside question or answer text.

Why: Class 9 stored the answer page's folio, often followed by the next question's opening
words, inside 43 answers ("…is called sublimation. 56 What is sublim…"). Word-presence content
checks cannot see it, because the folio IS printed on the page. (Procedure §14, full read step 6.)

Only numbers that appear INSIDE a question's stored text are examined; nothing else is touched.

Method, per question:
  0. SPAN: around each of the question's locators (question and answer), the page before and the
     two pages after — an answer may run on for up to three pages.
     A unit whose questions carry no locators is an ERROR (exit 2) — never a clean pass.
  1. TEXT: every 1-3 digit number in any stored text field — text, text_as_printed, options,
     answer (value, parts, pairs, sequence, criteria), answer_as_printed, solution_steps — that
     equals the printed folio of a page in the span is a candidate.
  2. POSITION: the number is looked up on the pages of the span (pdftotext -bbox).
       · printed in the body beside the same neighbouring token as in the stored text (the token
         before it; at the start of a field, the token after it, never a numbered item "56.")
                                                              → CONTENT (passes)
       · printed in the folio band of its page, and nowhere in that page's body except as a
         numbered item                                          → FOLIO   (a defect: file it)
       · anything else                                           → UNCLEAR (rendered for a person)
     The folio band is LEARNED per book: where the expected folio is actually printed on its
     pages (header or footer), with a small tolerance. If fewer than 5 pages teach it, the
     fixed 8% bands are used and the report says so.
     Single-digit candidates are FOLIO only when their page prints no plain body occurrence at all.
  3. RENDER: each UNCLEAR candidate's page is rendered at 100 dpi with every occurrence boxed
     (red = folio band, blue = body) — PNGs in --renders. A person decides.

Usage:
    python3 folio_scan.py --pdf <LBA.pdf> --out report.md [--renders DIR] <unit.json | unit dir> ...
Exit 0 = no FOLIO and no UNCLEAR · 1 = something to file or to look at · 2 = unreadable input or
no locators. Needs pdftotext/pdftoppm (poppler); Pillow only for --renders.
"""
import argparse, glob, html, json, os, re, subprocess, sys
from collections import Counter, defaultdict

FALLBACK = 0.08
# a number glued to a unit or a letter ("50kg", "24m") or joined by a dash ("45–55") is content, never a folio
# …or joined to an operator ("boy=50", "x10", "50×") — a calculation, never a folio
NUM = re.compile(r"(?<![\d.,/\-–—\w=+×*^])(\d{1,3})(?![\d.,/%°\-–—=+×*^]|[A-Za-z])")
TEXT_KEYS = ("text", "text_as_printed", "answer_as_printed")


def words_by_page(pdf):
    out = subprocess.run(["pdftotext", "-bbox", pdf, "-"], capture_output=True, text=True).stdout
    pages, cur = [], None
    for line in out.split("\n"):
        m = re.search(r'<page width="([\d.]+)" height="([\d.]+)"', line)
        if m:
            cur = {"h": float(m[2]), "w": []}
            pages.append(cur)
            continue
        m = re.search(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*)</word>', line)
        if m and cur is not None:
            cur["w"].append((float(m[1]), float(m[2]), float(m[3]), float(m[4]), html.unescape(m[5])))
    return pages


def strings(x, path):
    """every string under x, with a field path"""
    if isinstance(x, str):
        yield path, x
    elif isinstance(x, dict):
        for k, v in x.items():
            if k in ("id", "option_id", "kind", "left", "right") and not isinstance(v, (dict, list)):
                if k in ("left", "right"):
                    yield f"{path}.{k}", str(v)
                continue
            yield from strings(v, f"{path}.{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from strings(v, f"{path}[{i}]")


def texts(q):
    out = []
    for k in TEXT_KEYS:
        if isinstance(q.get(k), str):
            out.append((k, q[k]))
    for o in q.get("options") or []:
        if isinstance(o, dict):
            out.append((f"option {o.get('id')}", str(o.get("text") or "")))
    out += list(strings(q.get("answer") or {}, "answer"))
    out += list(strings(q.get("solution_steps") or [], "solution_steps"))
    return out


def neighbours(s, start, end):
    p = re.search(r"(\w+)\W*$", s[:start])
    n = re.match(r"\W*(\w+)", s[end:])
    # compare like the page side: a token's word characters only ("m/s" -> "m")
    return (p[1].lower() if p else None, n[1].lower() if n else None)


def is_num_token(tok, n):
    return bool(re.fullmatch(r"[\(\[]?0*%d[\.\):\]]?" % n, tok) or re.match(r"0*%d(?=[\.\)][A-Za-z])" % n, tok))


def learn_band(P, offset):
    top, bot = [], []
    for i, pg in enumerate(P, 1):
        f = i - offset
        if f < 1:
            continue
        hits = [w for w in pg["w"] if re.fullmatch(r"[\(\[]?%d[\)\]]?" % f, w[4])]
        hits = [w for w in hits if w[1] < pg["h"] * 0.2 or w[3] > pg["h"] * 0.8]
        if len(hits) == 1:
            w = hits[0]
            (top if w[1] < pg["h"] * 0.5 else bot).append((w[1] / pg["h"], w[3] / pg["h"]))
    if len(top) + len(bot) < 5:
        return (FALLBACK, 1 - FALLBACK, f"fixed {int(FALLBACK*100)}% bands (only {len(top)+len(bot)} pages taught)")
    t = max(y1 for _, y1 in top) + 0.01 if top else 0.0
    b = min(y0 for y0, _ in bot) - 0.01 if bot else 1.0
    return (t, b, f"learned from {len(bot)} footer / {len(top)} header folios: top < {t:.3f}, bottom > {b:.3f} of page height")


def occurrences(page, n, band):
    ws = page["w"]
    out = []
    for i, w in enumerate(ws):
        if is_num_token(w[4], n):
            inband = w[3] / page["h"] <= band[0] or w[1] / page["h"] >= band[1]
            # nearest word-bearing token on each side ("v = 24 m/s": the neighbours are "v" and "m")
            pw = next((re.sub(r"\W", "", ws[j][4]).lower() for j in range(i - 1, -1, -1) if re.search(r"\w", ws[j][4])), None)
            nw = next((re.sub(r"\W", "", ws[j][4]).lower() for j in range(i + 1, len(ws)) if re.search(r"\w", ws[j][4])), None)
            out.append(dict(box=w[:4], margin=inband, prev=pw, next=nw,
                            numbered=bool(re.search(r"[\.\)]", w[4]))))
    return out


def render(pdf, pno, occ, path):
    from PIL import Image, ImageDraw
    base = path[:-4]
    subprocess.run(["pdftoppm", "-r", "100", "-f", str(pno), "-l", str(pno), "-png", "-singlefile", pdf, base], check=True)
    im = Image.open(base + ".png").convert("RGB")
    d = ImageDraw.Draw(im)
    k = 100 / 72
    for o in occ:
        x0, y0, x1, y1 = [v * k for v in o["box"]]
        d.rectangle([x0 - 3, y0 - 3, x1 + 3, y1 + 3], outline=(220, 0, 0) if o["margin"] else (0, 80, 220), width=3)
    im.save(base + ".png")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--renders")
    ap.add_argument("units", nargs="+")
    a = ap.parse_args()
    files = []
    for u in a.units:
        files += sorted(glob.glob(os.path.join(u, "*_questions_*.json"))) if os.path.isdir(u) else [u]
    if not files or not os.path.exists(a.pdf):
        print("ERROR: no units or no pdf"); sys.exit(2)
    P = words_by_page(a.pdf)
    if not P:
        print("ERROR: the pdf has no text layer — nothing can be decided"); sys.exit(2)
    units, offsets, errors = [], Counter(), []
    for f in files:
        try:
            u = json.load(open(f, encoding="utf-8"))
        except Exception as e:  # noqa
            print(f"ERROR: unreadable {f}: {e}"); sys.exit(2)
        qs = u.get("questions", [])
        noloc = [q["id"] for q in qs if not any(l.get("role") == "question" for l in q.get("locators") or [])]
        if qs and len(noloc) == len(qs):
            errors.append(f"{os.path.basename(f)}: no question carries a locator — this scan cannot run on it "
                          f"(contract {u.get('contract_version')}); nothing was checked")
        elif noloc:
            errors.append(f"{os.path.basename(f)}: {len(noloc)} question(s) without a locator were not checked: "
                          + ", ".join(noloc[:8]) + (" …" if len(noloc) > 8 else ""))
        for q in qs:
            for l in q.get("locators") or []:
                offsets[l["pdf_page"] - l["printed_page"]] += 1
        units.append((f, u))
    if not offsets:
        for e in errors:
            print("ERROR:", e)
        sys.exit(2)
    offset = offsets.most_common(1)[0][0]
    band = learn_band(P, offset)
    rows, counts = [], Counter()
    for f, u in units:
        for q in u.get("questions", []):
            locs = q.get("locators") or []
            if not locs:
                continue
            # around each locator: the page before (a stem or key that starts at the foot of a page)
            # and two pages after (an answer that runs on) — never the pages BETWEEN a question and its key
            span = sorted({p for l in locs for p in range(l["pdf_page"] - 1, l["pdf_page"] + 3) if 1 <= p <= len(P)})
            folio_page = {p - offset: p for p in span if p - offset >= 1}
            qn = str(int(re.search(r"q(\d{3})", q["id"])[1]))
            for field, s in texts(q):
                for m in NUM.finditer(s):
                    n = int(m[1])
                    if n not in folio_page:
                        continue
                    pg = folio_page[n]
                    pv, nv = neighbours(s, m.start(), m.end())
                    allocc = [(p, o) for p in span for o in occurrences(P[p - 1], n, band)]
                    body_ctx = [o for _, o in allocc if not o["margin"] and (
                        (pv and o["prev"] == pv) or (not pv and nv and o["next"] == nv and not o["numbered"]))]
                    if field.startswith("answer") and s.strip() == str(n):
                        body_ctx += [o for _, o in allocc if not o["margin"] and o["prev"] == qn]
                    occ = [o for p, o in allocc if p == pg]
                    inband = [o for o in occ if o["margin"]]
                    plain_body = [o for o in occ if not o["margin"] and not o["numbered"]]
                    if body_ctx:
                        verdict = "CONTENT"
                    elif inband and not plain_body:
                        verdict = "FOLIO"
                    else:
                        verdict = "UNCLEAR"
                    counts[verdict] += 1
                    ctx = s[max(0, m.start() - 30):m.end() + 25].replace("\n", " ")
                    png = ""
                    if verdict == "UNCLEAR" and a.renders:
                        os.makedirs(a.renders, exist_ok=True)
                        png = os.path.join(a.renders, f"{q['id']}_{re.sub(r'[^A-Za-z0-9]', '', field)}_{n}_p{pg}.png")
                        try:
                            render(a.pdf, pg, occ, png)
                        except Exception as e:  # noqa
                            png = f"render failed: {e}"
                    rows.append((verdict, q["id"], field, n, pg, len(inband), len(occ) - len(inband), ctx, png))
    rows.sort(key=lambda r: (["FOLIO", "UNCLEAR", "CONTENT"].index(r[0]), r[1], r[2]))
    md = [f"# folio_scan — {os.path.basename(a.pdf)}", "",
          f"units: {len(files)} · candidates: {len(rows)} · FOLIO {counts['FOLIO']} · UNCLEAR {counts['UNCLEAR']} · "
          f"CONTENT {counts['CONTENT']} · errors {len(errors)} · questions with a FOLIO: "
          f"{len({r[1] for r in rows if r[0] == 'FOLIO'})}", "",
          f"offset pdf−printed: {offset} · folio band: {band[2]}", ""]
    md += [f"- ERROR: {e}" for e in errors] + ([""] if errors else [])
    md += ["| verdict | question | field | number | pdf page | in band | in body | stored context | render |",
           "|---|---|---|---|---|---|---|---|---|"]
    md += [f"| {v} | {i} | {fl} | {n} | {p} | {mg} | {bd} | …{c.replace('|', '/')}… | {png} |"
           for v, i, fl, n, p, mg, bd, c, png in rows]
    open(a.out, "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(md[2]); print(md[4])
    for e in errors:
        print("ERROR:", e)
    if any("no question carries a locator" in e for e in errors):
        sys.exit(2)
    sys.exit(1 if counts["FOLIO"] or counts["UNCLEAR"] or errors else 0)


if __name__ == "__main__":
    main()
