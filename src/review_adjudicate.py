#!/usr/bin/env python3
"""review_adjudicate.py — stage 3 of review method v1.4: the verifier's packets, checks and reference test.

    build  --class N --staging <viyamo-staging> --record <viyamo-record> --out <Devs>/_review [--reference <Devs>/_reference]
        From <record>/review/class-N/merge.json, one packet per unit at <out>/c<N>/verify/<unit>.json holding
          task "key"   every question routed stage3: is the stored key right? (the reads' verdicts and reasons are
                       NOT included — the verifier judges blind)
          task "stem"  a stage-4 question whose ONLY reason is a read's stem_defect, and whose reads otherwise
                       accepted the key: is the question text itself defective on the page?
          task "both"  the same, but a read (or the 2026-09-21 full read) also doubted the key: the stem
                       first, then the key if the stem is sound
        Each item: id, task, type, marks, stem, options/match, the stored key, the LBA pages of the question and
        of its printed key (from its locators), and the class's textbook files. Items keep unit order.

    check  <verdict.json> --packet <packet.json> [--reference <Devs>/_reference]
        Every item exactly once; outcome from the task's set; the fields each outcome needs:
          key:  KEEP | CORRECT | HOLD
                KEEP and CORRECT need `reference`: {kind:"textbook", file, pdf_page, quote} or
                {kind:"computation", working}. CORRECT also needs `new_key` (text) and, for an option question,
                `new_option_id` naming an existing option. HOLD needs `reason`.
          stem: STEM_OK | STEM_DEFECT, with `reason` (and the LBA pdf_page it read) either way.
          both: `stem_outcome` STEM_OK | STEM_DEFECT with `stem_reason`; then `outcome` as for key —
                STEM_DEFECT requires outcome HOLD.
        With --reference, every textbook quote is looked up: on its cited PDF page (and the next), then anywhere
        in the book. Found on another page → PASS with a note (the page is metadata; the quote is the evidence).
        Nowhere in the book → FAIL, unless the cited page's text layer cannot be read (under 60 words, or
        undecodable ligatures) → WARN for a coordinator render.
Standard library + poppler (pdftotext). Exit 0 PASS, 1 FAIL.
"""
import argparse, glob, json, os, re, subprocess, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from review_common import TAGS, units_at, unit_name, options_of, render_key, match_sides

KEY_OUT = {"KEEP", "CORRECT", "HOLD"}
TASKS = {"key", "stem", "both"}
STEM_OUT = {"STEM_OK", "STEM_DEFECT"}


def load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def textbooks(ref, cls):
    return sorted(os.path.basename(p) for p in glob.glob(os.path.join(ref, f"class-{cls}", "textbook", "*.pdf")))


def lba(ref, cls):
    got = sorted(glob.glob(os.path.join(ref, f"class-{cls}", "*.pdf")))
    return os.path.basename(got[0]) if got else None


def build(a):
    m = load(os.path.join(a.record, "review", f"class-{a.cls}", "merge.json"))
    want = {}
    for q in m["questions"]:
        if q["route"] == "stage3":
            want[q["id"]] = "key"
        elif (q["route"] == "stage4" and not q.get("register") and "CONTAMINATED" not in (q.get("full_read") or [])):
            vs = [x["verdict"] for x in (q.get("A"), q.get("B")) if x]
            clean = all(v == "CORRECT" for v in vs) and not (q.get("full_read") or [])
            want[q["id"]] = "stem" if clean else "both"
    tb, src = textbooks(a.reference, a.cls), lba(a.reference, a.cls)
    n = {"key": 0, "stem": 0, "both": 0}
    for path, unit in units_at(a.staging, TAGS[a.cls]):
        un = unit_name(unit)
        items = []
        for q in unit["questions"]:
            t = want.get(q["id"])
            if not t:
                continue
            it = {"id": q["id"], "task": t, "type": q["type"], "stem": q.get("text") or "", "key": render_key(q)}
            if q.get("marks") is not None:
                it["marks"] = q["marks"]
            if options_of(q):
                it["options"] = [{"id": o.get("id"), "text": o.get("text", "")} for o in options_of(q)]
            left, right = match_sides(q)
            if left or right:
                it["match"] = {"left": left, "right": right}
            it["lba_pages"] = {l["role"]: l["pdf_page"] for l in q.get("locators") or []}
            items.append(it)
            n[t] += 1
        if not items:
            continue
        pk = {"packet": "review-verify", "packet_version": 2, "paths": "relative to the Devs folder", "class": a.cls, "unit": un, "tag": TAGS[a.cls],
              "chapter_ref": (unit["questions"][0].get("source_ref") or "").rsplit(" ", 1)[0],
              "lba": f"_reference/class-{a.cls}/{src}", "textbooks": [f"_reference/class-{a.cls}/textbook/{t}" for t in tb],
              "items": items}
        d = os.path.join(a.out, f"c{a.cls}", "verify")
        os.makedirs(os.path.join(d, "verdicts"), exist_ok=True)
        with open(os.path.join(d, f"{un}.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(pk, fh, ensure_ascii=False, indent=1); fh.write("\n")
    print(f"class {a.cls}: key {n['key']} · stem {n['stem']} · both {n['both']} · textbooks {len(tb)} · lba {src}")


def norm(s):
    s = unicodedata.normalize("NFKC", s).lower()
    s = re.sub(r"[‐-―−]", "-", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


_page_cache = {}
# Some KTBS textbook pages carry a glyph-shifted text layer: every character is stored 29 code points low
# ("WKH\x03PLGGOH" for "the middle"; the space is \x03). Such tokens are decoded for a second comparison.


def is_garbled(t):
    return (len(t) >= 2 and all(3 <= ord(c) <= 93 for c in t) and not any(c.islower() for c in t)
            and any(c.isupper() or ord(c) < 32 for c in t))


def decode_token(t):
    return "".join(chr(ord(c) + 29) for c in t)


def page_text(pdf, page, span=2):
    """(normalised text, space-free decoded text, ligature count, word count) for pdf pages page..page+span-1."""
    k = (pdf, page, span)
    if k not in _page_cache:
        # prefer the prepared page texts (textbook_text.py: decoded layer, OCR where the layer is empty) —
        # the same files the agents are told to quote from
        tdir = os.path.join(os.path.dirname(pdf), "text", os.path.splitext(os.path.basename(pdf))[0])
        files = [os.path.join(tdir, f"p{q:04d}.txt") for q in range(page, page + span)]
        if os.path.isdir(tdir) and all(os.path.exists(f) for f in files if int(f[-8:-4]) <= pages_of(pdf)):
            class _R: pass
            r = _R(); r.stdout = "\n".join(open(f, encoding="utf-8").read() for f in files if os.path.exists(f))
        else:
            r = subprocess.run(["pdftotext", "-f", str(page), "-l", str(page + span - 1), pdf, "-"],
                               capture_output=True, text=True)
        toks = re.split(r"[ \t\n\r\f\v]+", r.stdout)
        bad = [t for t in toks if is_garbled(t)]
        dec = " ".join(decode_token(t) if is_garbled(t) else t for t in toks)
        # ligatures in shifted runs come out as stray code points (U+0880-U+08FF: "ࢆOOHG" = "filled");
        # they cannot be decoded, so a quote across one cannot be matched by code
        lig = sum(1 for c in r.stdout if 0x0880 <= ord(c) <= 0x08FF)
        _page_cache[k] = (norm(r.stdout), norm(dec).replace(" ", ""), lig, len(r.stdout.split()))
    return _page_cache[k]


_pages = {}


def pages_of(pdf):
    if pdf not in _pages:
        r = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
        m = re.search(r"^Pages:\s+(\d+)", r, re.M)
        _pages[pdf] = int(m[1]) if m else 0
    return _pages[pdf]


def gapped(text, q, max_gap=3):
    """True when the words of q occur in order in text with at most max_gap stray tokens between any two of them
    (the KTBS watermark's letters land as short stray tokens between the lines of a sentence)."""
    tw = re.findall(r"[a-z0-9]+", text.lower())
    qw = re.findall(r"[a-z0-9]+", q.lower())
    if len(qw) < 4:
        return False
    starts = [i for i, w in enumerate(tw) if w == qw[0]]
    for s in starts:
        i, ok = s, True
        for w in qw[1:]:
            j = i + 1
            while j < len(tw) and j <= i + 1 + max_gap and tw[j] != w:
                j += 1
            if j >= len(tw) or j > i + 1 + max_gap or tw[j] != w:
                ok = False
                break
            i = j
        if ok:
            return True
    return False


def find_quote(pdf, page, q):
    """('cited'|'cited-gapped'|<other page>|None, cited-page (words, ligatures))"""
    qs = q.replace(" ", "")
    raw, dec, lig, words = page_text(pdf, page)
    if q in raw or qs in raw.replace(" ", "") or qs in dec:
        return "cited", (words, lig)
    if gapped(raw, q):
        return "cited-gapped", (words, lig)
    for p in range(1, pages_of(pdf) + 1):
        r2, d2, _, _ = page_text(pdf, p, 1)
        if q in r2 or qs in r2.replace(" ", "") or qs in d2:
            return p, (words, lig)
    return None, (words, lig)


def check(vf, pf, ref=None):
    errs, notes = [], []
    try:
        v, pk = load(vf), load(pf)
    except Exception as e:  # noqa
        return [f"unreadable: {e}"], notes
    items = {it["id"]: it for it in pk["items"]}
    got = v.get("items") if isinstance(v.get("items"), list) else None
    if got is None:
        return ["items missing"], notes
    ids = [g.get("id") for g in got]
    if sorted(ids) != sorted(items) or len(ids) != len(set(ids)):
        errs.append(f"ids differ from the packet: missing {sorted(set(items) - set(ids))[:4]}, extra {sorted(set(ids) - set(items))[:4]}")
    for g in got:
        it = items.get(g.get("id"))
        if not it:
            continue
        o, i = g.get("outcome"), g["id"]
        if it["task"] == "stem":
            if o not in STEM_OUT: errs.append(f"{i}: outcome {o!r} not in {sorted(STEM_OUT)}")
            if not str(g.get("reason") or "").strip(): errs.append(f"{i}: no reason")
            continue
        if it["task"] == "both":
            so = g.get("stem_outcome")
            if so not in STEM_OUT: errs.append(f"{i}: stem_outcome {so!r} not in {sorted(STEM_OUT)}")
            if not str(g.get("stem_reason") or "").strip(): errs.append(f"{i}: no stem_reason")
            if so == "STEM_DEFECT" and o != "HOLD": errs.append(f"{i}: STEM_DEFECT requires outcome HOLD")
        if o not in KEY_OUT:
            errs.append(f"{i}: outcome {o!r} not in {sorted(KEY_OUT)}"); continue
        if o == "HOLD":
            if not str(g.get("reason") or "").strip(): errs.append(f"{i}: HOLD without reason")
            continue
        r = g.get("reference") or {}
        if r.get("kind") == "textbook":
            for f in ("file", "pdf_page", "quote"):
                if not r.get(f): errs.append(f"{i}: textbook reference without {f}")
            if r.get("file") and ref and r.get("pdf_page") and r.get("quote"):
                pdf = os.path.join(ref, f"class-{pk['class']}", "textbook", os.path.basename(r["file"]))
                if not os.path.exists(pdf):
                    errs.append(f"{i}: textbook {r['file']!r} not found")
                else:
                    q = norm(r["quote"])
                    if len(q) < 20:
                        errs.append(f"{i}: quote shorter than 20 characters — not a reference")
                    else:
                        where, (words, lig) = find_quote(pdf, int(r["pdf_page"]), q)
                        if where == "cited":
                            notes.append(f"{i}: quote found")
                        elif where == "cited-gapped":
                            notes.append(f"{i}: quote found across watermark fragments on the cited page")
                        elif where:
                            notes.append(f"{i}: quote found — PAGE: cited p{r['pdf_page']}, printed on p{where}")
                        elif words < 60 or lig:
                            notes.append(f"{i}: quote not found; cited page unreadable by code ({words} words, {lig} ligatures) — GARBLED, coordinator renders p{r['pdf_page']}")
                        else:
                            errs.append(f"{i}: quote NOT FOUND in {r['file']} (cited p{r['pdf_page']})")
        elif r.get("kind") == "computation":
            if not str(r.get("working") or "").strip(): errs.append(f"{i}: computation without working")
        else:
            errs.append(f"{i}: {o} needs a reference of kind textbook or computation")
        if o == "CORRECT":
            if not str(g.get("new_key") or "").strip(): errs.append(f"{i}: CORRECT without new_key")
            if it.get("options"):
                if g.get("new_option_id") not in {x["id"] for x in it["options"]}:
                    errs.append(f"{i}: CORRECT on an option question needs new_option_id from its options")
    for k in ("actor", "agent"):
        if not v.get(k): errs.append(f"{k} missing (the thread adds it with review_merge.py stamp)")
    return errs, notes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    b = sp.add_parser("build")
    b.add_argument("--class", dest="cls", type=int, required=True, choices=sorted(TAGS))
    b.add_argument("--staging", required=True); b.add_argument("--record", required=True)
    b.add_argument("--out", required=True); b.add_argument("--reference", required=True)
    c = sp.add_parser("check"); c.add_argument("verdict"); c.add_argument("--packet", required=True)
    c.add_argument("--reference")
    a = ap.parse_args()
    if a.cmd == "build":
        return build(a)
    e, n = check(a.verdict, a.packet, a.reference)
    print("PASS" if not e else "FAIL\n  " + "\n  ".join(e))
    for x in n:
        if "GARBLED" in x or "PAGE:" in x: print("  WARN " + x)
    if n: print(f"  ({sum('quote found' in x for x in n)} quotes found in the book)")
    sys.exit(1 if e else 0)


if __name__ == "__main__":
    main()
