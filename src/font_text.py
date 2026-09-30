#!/usr/bin/env python3
"""font_text.py — a page's font text, as a READING AID for the maths converter (maths digitization v2.2).

    python3 font_text.py --pdf P --page N

Prints the page's text line by line, top to bottom, with glyphs the text layer leaves blank restored from the
EMBEDDED font (its own cmap, else a reverse walk of its GSUB substitutions). Adopted, reviewed, from the Class 10
maths pilot's cidcache.py (viyamo-record reports/class-10-maths/scripts/batch-01/, 2026-09-22).
Marks, by geometry only: a raised run of smaller glyphs as ^{…}, a lowered run as _{…}; math-alphanumeric letters
(𝑥, 𝛼) as plain letters (NFKC); a glyph neither the text layer nor the font can name as ⍰.
It does NOT build fractions, roots or layout: stacked fractions come out as separate lines. The page render
decides every reading; this tool only helps with exact digits and letters. Needs pdfminer.six and fontTools.
"""
import argparse, io, sys, unicodedata
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTChar, LTContainer
from pdfminer.pdftypes import resolve1
from fontTools.ttLib import TTFont


class Agg(PDFPageAggregator):
    def render_char(self, matrix, font, fontsize, scaling, rise, cid, ncs, gs):
        adv = super().render_char(matrix, font, fontsize, scaling, rise, cid, ncs, gs)
        it = self.cur_item._objs[-1]; it.cid = cid; it.fontobj = font
        return adv


_INV = {}


def _inverse(font):
    k = id(font)
    if k in _INV: return _INV[k]
    m = None
    try:
        ff = resolve1((font.descriptor or {}).get("FontFile2"))
        if ff is not None:
            tt = TTFont(io.BytesIO(ff.get_data()))
            go = tt.getGlyphOrder(); cm = tt.getBestCmap() or {}
            g2u = {}
            for u, g in sorted(cm.items()):
                if g not in g2u or g2u[g] == 0x20: g2u[g] = u
            rev = {}
            if "GSUB" in tt:
                for lk in tt["GSUB"].table.LookupList.Lookup:
                    for st in lk.SubTable:
                        t = st.ExtSubTable if lk.LookupType == 7 else st
                        for x, y in getattr(t, "mapping", {}).items():
                            if isinstance(y, list):
                                if len(y) != 1: continue
                                y = y[0]
                            rev.setdefault(y, []).append(x)
                        for x, ys in getattr(t, "alternates", {}).items():
                            for y in ys: rev.setdefault(y, []).append(x)

            def trace(g, d=0):
                if g in g2u: return chr(g2u[g])
                if d > 5: return None
                for x in rev.get(g, []):
                    r = trace(x, d + 1)
                    if r: return r
                return None
            m = (go, trace, {})
    except Exception:
        m = None
    _INV[k] = m
    return m


def glyph(ch):
    t = ch.get_text()
    if t.strip() and not t.startswith("(cid:"):
        return t, False
    f = ch.fontobj
    if f.__class__.__name__ == "PDFCIDFont":          # Identity CIDToGIDMap: gid == cid
        m = _inverse(f)
        if m:
            go, trace, memo = m
            if ch.cid not in memo: memo[ch.cid] = trace(go[ch.cid]) if ch.cid < len(go) else None
            if memo[ch.cid] and memo[ch.cid].strip(): return memo[ch.cid], True
    return (" " if t == " " else "⍰"), False


def page_chars(pdf, n):
    rm = PDFResourceManager(); dev = Agg(rm, laparams=None); it = PDFPageInterpreter(rm, dev)
    out = []
    with open(pdf, "rb") as fh:
        for i, page in enumerate(PDFPage.get_pages(fh), 1):
            if i < n: continue
            it.process_page(page); H = page.mediabox[3]

            def walk(o):
                for x in o:
                    if isinstance(x, LTChar):
                        t, rec = glyph(x)
                        t = unicodedata.normalize("NFKC", t) if t != "⍰" else t
                        out.append(dict(t=t, x0=x.x0, x1=x.x1, top=H - x.y1, bot=H - x.y0, sz=x.size, rec=rec))
                    elif isinstance(x, LTContainer): walk(x)
            walk(dev.get_result())
            break
    return out


def lines(cs):
    cs = [c for c in cs if c["t"] != " "]
    cs.sort(key=lambda c: (c["bot"], c["x0"]))
    rows = []
    for c in cs:
        mid = (c["top"] + c["bot"]) / 2
        for r in rows:
            if r["top"] - 0.45 * r["sz"] <= mid <= r["bot"] + 0.45 * r["sz"]:
                r["cs"].append(c); r["top"] = min(r["top"], c["top"]); r["bot"] = max(r["bot"], c["bot"]); break
        else:
            rows.append(dict(cs=[c], top=c["top"], bot=c["bot"], sz=c["sz"]))
    res = []
    for r in sorted(rows, key=lambda r: r["top"]):
        g = sorted(r["cs"], key=lambda c: c["x0"])
        big = sorted(c["sz"] for c in g)[len(g) // 2]
        base = sorted(c["bot"] for c in g if c["sz"] >= 0.9 * big)[len([c for c in g if c["sz"] >= 0.9 * big]) // 2]
        s, mode, prev = "", "", None
        for c in g:
            k = ""
            if c["sz"] < 0.85 * big:
                if c["bot"] < base - 0.2 * big: k = "^"
                elif c["bot"] > base + 0.1 * big: k = "_"
            if k != mode:
                if mode: s += "}"
                if k: s += k + "{"
                mode = k
            if prev is not None and c["x0"] - prev["x1"] > 0.25 * min(c["sz"], prev["sz"]) and not s.endswith((" ", "{")): s += " "
            s += c["t"]; prev = c
        if mode: s += "}"
        res.append(s)
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdf", required=True); ap.add_argument("--page", type=int, required=True)
    a = ap.parse_args()
    cs = page_chars(a.pdf, a.page)
    for l in lines(cs): print(l)
    print(f"-- glyphs {len(cs)} · restored from font {sum(c['rec'] for c in cs)} · unnamed ⍰ {sum(c['t'] == '⍰' for c in cs)}", file=sys.stderr)


if __name__ == "__main__":
    main()
