#!/usr/bin/env python3
"""textbook_text.py — one clean text file per textbook page, for the verifier and its checker.

    python3 textbook_text.py --pdf <book.pdf> --out <dir> [--from P --to Q]

Writes <out>/p0001.txt … one per PDF page, and <out>/index.json (per page: method, words). Per page:
  1. the text layer (pdftotext); tokens stored glyph-shifted (+29 code points, KTBS) are decoded, and text
     stored as private-use codes U+F0xx (the Class 9 Science textbooks: symbol-encoded fonts, printable ASCII
     ch stored as U+F000 + (0x120 - ord(ch)); U+F020 and U+F08B are spaces) is decoded the same way
  2. if that leaves under 60 words, the page is rendered at 300 dpi and OCR'd (tesseract, eng)
Idempotent: a page already written is skipped, so the job can run in pieces. Every agent quotes from these
files, and review_adjudicate.py checks against the same files, so a quote is matched against exactly what
the agent read. Standard library + poppler + tesseract.
"""
import argparse, json, os, re, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from review_adjudicate import is_garbled, decode_token

MIN_WORDS = 60


def pages(pdf):
    r = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    return int(re.search(r"^Pages:\s+(\d+)", r, re.M)[1])


def decode_pua(t):
    """U+F0xx symbol-font text -> ASCII (Class 9 Science textbooks). Codes outside the printable range become spaces."""
    out = []
    for ch in t:
        o = ord(ch)
        if 0xF000 <= o <= 0xF0FF:
            a = 0x120 - (o & 0xFF)
            out.append(chr(a) if 0x21 <= a <= 0x7E else " ")
        else:
            out.append(ch)
    return "".join(out)


def layer(pdf, p):
    t = subprocess.run(["pdftotext", "-layout", "-f", str(p), "-l", str(p), pdf, "-"], capture_output=True, text=True).stdout
    t = decode_pua(t)
    lines = []
    for line in t.split("\n"):
        toks = re.split(r"( +)", line)
        lines.append("".join(decode_token(x) if (x.strip() and is_garbled(x)) else x for x in toks))
    return "\n".join(lines)


def ocr(pdf, p, work):
    base = os.path.join(work, f"r{p}")
    subprocess.run(["pdftoppm", "-r", "300", "-gray", "-f", str(p), "-l", str(p), "-png", "-singlefile", pdf, base], check=True)
    t = subprocess.run(["tesseract", base + ".png", "-", "-l", "eng", "--psm", "3"], capture_output=True, text=True).stdout
    os.remove(base + ".png")
    return t


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdf", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--from", dest="a", type=int, default=1); ap.add_argument("--to", dest="b", type=int)
    ap.add_argument("--work", default=os.path.expanduser("~/tt_work"))
    ap.add_argument("--redo", action="store_true", help="rebuild pages that already exist (after a decoder change)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True); os.makedirs(a.work, exist_ok=True)
    ip = os.path.join(a.out, "index.json")
    idx = json.load(open(ip)) if os.path.exists(ip) else {"pdf": os.path.basename(a.pdf), "pages": {}}
    n = pages(a.pdf)
    for p in range(a.a, min(a.b or n, n) + 1):
        f = os.path.join(a.out, f"p{p:04d}.txt")
        if os.path.exists(f) and str(p) in idx["pages"] and not a.redo:
            continue
        t, m = layer(a.pdf, p), "text_layer"
        if len(t.split()) < MIN_WORDS:
            o = ocr(a.pdf, p, a.work)
            if len(o.split()) > len(t.split()):
                t, m = o, "ocr_tesseract_300dpi"
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(t)
        idx["pages"][str(p)] = {"method": m, "words": len(t.split())}
        with open(ip, "w", encoding="utf-8") as fh:
            json.dump(idx, fh, indent=1)
    done = len(idx["pages"])
    print(f"{os.path.basename(a.pdf)}: {done}/{n} pages · ocr {sum(v['method'].startswith('ocr') for v in idx['pages'].values())}")


if __name__ == "__main__":
    main()
