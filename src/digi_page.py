#!/usr/bin/env python3
"""digi_page.py — page tools for the maths digitization (design: viyamo-record/design/maths_digitization_v2…).

    render   --pdf P --page N --out DIR                 page PNG at 200 dpi → DIR/pNNNN.png (DIR must be under Devs so it
                                                         can be staged and seen)
    figures  --pdf P --page N                           the page's image objects with their boxes (PDF points, top-origin)
    crop     --pdf P --page N --bbox x0,y0,x1,y1 --id ID --figdir DIR --source S [--method pdf_image|drawn]
                                                         cuts DIR/ID.png at 300 dpi and prints its manifest entry (JSON)
    compile  --page-tex F --figdir DIR --out DIR2        compiles one page with viyamo-maths.sty (xelatex) and writes
                                                         DIR2/compiled_pNNNN.png and DIR2/side_pNNNN.png (original | compiled)
                                                         needs --pdf and --page too, for the original side
Sources: cropped-lba | cropped-textbook | generated | modified. Standard library + poppler + pdfplumber + Pillow + xelatex.
"""
import argparse, hashlib, json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
STY = os.path.join(os.path.dirname(HERE), "latex", "viyamo-maths.sty")
SOURCES = {"cropped-lba", "cropped-textbook", "generated", "modified"}


def render(pdf, page, out, dpi=200, name=None):
    os.makedirs(out, exist_ok=True)
    base = os.path.join(out, name or f"p{page:04d}")
    subprocess.run(["pdftoppm", "-r", str(dpi), "-f", str(page), "-l", str(page), "-png", "-singlefile", pdf, base], check=True)
    return base + ".png"


def figures(pdf, page):
    import pdfplumber
    with pdfplumber.open(pdf) as d:
        p = d.pages[page - 1]
        out = [{"k": i + 1, "bbox": [round(im["x0"], 1), round(im["top"], 1), round(im["x1"], 1), round(im["bottom"], 1)],
                "px": [im.get("srcsize", [None, None])[0], im.get("srcsize", [None, None])[1]]}
               for i, im in enumerate(sorted(p.images, key=lambda im: (round(im["top"]), im["x0"])))]
        # vector drawings (the textbooks draw their figures as strokes, not images): strokes merged into boxes
        # when they touch or lie within 6 pt; table rules and underlines (boxes under 12 pt in both directions,
        # or thinner than 3 pt) are dropped. These are CANDIDATES: the converter checks each against the render.
        boxes = [[o["x0"], o["top"], o["x1"], o["bottom"]] for o in p.curves + p.lines + p.rects
                 if o["top"] > 30 and o["bottom"] < p.height - 30]
        merged = True
        while merged:
            merged = False
            for i in range(len(boxes)):
                for j in range(i + 1, len(boxes)):
                    a, b = boxes[i], boxes[j]
                    if a[0] - 6 <= b[2] and b[0] - 6 <= a[2] and a[1] - 6 <= b[3] and b[1] - 6 <= a[3]:
                        boxes[i] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
                        del boxes[j]; merged = True; break
                if merged: break
        drawn = [[round(v, 1) for v in b] for b in sorted(boxes, key=lambda b: (b[1], b[0]))
                 if (b[2] - b[0] >= 12 or b[3] - b[1] >= 12) and min(b[2] - b[0], b[3] - b[1]) >= 3]
        return {"page": page, "page_size": [round(p.width, 1), round(p.height, 1)], "images": out,
                "vector_strokes": len(p.curves) + len(p.lines), "drawn_candidates": drawn}


def crop(pdf, page, bbox, fid, figdir, source, method):
    from PIL import Image
    if source not in SOURCES:
        sys.exit(f"source must be one of {sorted(SOURCES)}")
    x0, y0, x1, y1 = bbox
    tmp = tempfile.mkdtemp(dir=os.path.expanduser("~"))
    full = render(pdf, page, tmp, dpi=300, name="full")
    im = Image.open(full)
    k = 300 / 72
    box = (max(0, int(x0 * k) - 4), max(0, int(y0 * k) - 4), min(im.width, int(x1 * k) + 4), min(im.height, int(y1 * k) + 4))
    os.makedirs(figdir, exist_ok=True)
    path = os.path.join(figdir, f"{fid}.png")
    if os.path.exists(path):
        sys.exit(f"{path} exists — figures are never overwritten; choose a new id")
    im.crop(box).save(path)
    shutil.rmtree(tmp)
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    return {"id": fid, "file": os.path.basename(path), "pdf_page": page, "bbox": [x0, y0, x1, y1],
            "source": source, "bbox_method": method, "sha256": h}


def compile_page(tex, figdir, out, pdf, page):
    from PIL import Image
    os.makedirs(out, exist_ok=True)
    work = tempfile.mkdtemp(dir=os.path.expanduser("~"))
    shutil.copy(STY, work)
    fd = os.path.abspath(figdir).rstrip("/") + "/"
    body = open(tex, encoding="utf-8").read()
    doc = ("\\documentclass[11pt]{article}\n\\usepackage{viyamo-maths}\n\\renewcommand{\\vyfigdir}{" + fd + "}\n"
           "\\begin{document}\n" + body + "\n\\end{document}\n")
    open(os.path.join(work, "page.tex"), "w", encoding="utf-8").write(doc)
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", "page.tex"], cwd=work,
                       capture_output=True, text=True, timeout=150)
    if r.returncode:
        log = open(os.path.join(work, "page.log"), encoding="utf-8", errors="replace").read()
        err = [l for l in log.splitlines() if l.startswith("!")][:5]
        print("COMPILE FAILED:", " | ".join(err) or r.stdout[-500:])
        return 1
    log = open(os.path.join(work, "page.log"), encoding="utf-8", errors="replace").read()
    miss = sorted(set(re.findall(r"Missing character: There is no (.) ", log)))
    if miss:
        print("COMPILE FAILED: glyphs missing from the font (they print blank):", " ".join(miss))
        return 1
    subprocess.run(["pdftoppm", "-r", "100", "-png", os.path.join(work, "page.pdf"), os.path.join(work, "c")], check=True)
    parts = sorted(f for f in os.listdir(work) if f.startswith("c") and f.endswith(".png"))
    ims = [Image.open(os.path.join(work, f)) for f in parts]
    w, h = max(i.width for i in ims), sum(i.height for i in ims)
    comp = Image.new("RGB", (w, h), "white")
    y = 0
    for i in ims:
        comp.paste(i, (0, y)); y += i.height
    cp = os.path.join(out, f"compiled_p{page:04d}.png"); comp.save(cp)
    orig = Image.open(render(pdf, page, work, dpi=100, name="orig")).convert("RGB")
    side = Image.new("RGB", (orig.width + comp.width + 20, max(orig.height, comp.height)), "white")
    side.paste(orig, (0, 0)); side.paste(comp, (orig.width + 20, 0))
    sp = os.path.join(out, f"side_p{page:04d}.png"); side.save(sp)
    shutil.rmtree(work)
    print(f"compiled OK · {len(parts)} page(s) · {sp}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    for n in ("render", "figures", "crop", "compile"):
        s = sp.add_parser(n); s.add_argument("--pdf", required=True); s.add_argument("--page", type=int, required=True)
        if n == "render": s.add_argument("--out", required=True)
        if n == "crop":
            s.add_argument("--bbox", required=True); s.add_argument("--id", required=True); s.add_argument("--figdir", required=True)
            s.add_argument("--source", required=True); s.add_argument("--method", default="pdf_image", choices=["pdf_image", "drawn"])
        if n == "compile":
            s.add_argument("--page-tex", required=True); s.add_argument("--figdir", required=True); s.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.cmd == "render": print(render(a.pdf, a.page, a.out))
    elif a.cmd == "figures": print(json.dumps(figures(a.pdf, a.page), indent=1))
    elif a.cmd == "crop": print(json.dumps(crop(a.pdf, a.page, [float(x) for x in a.bbox.split(",")], a.id, a.figdir, a.source, a.method)))
    else: sys.exit(compile_page(a.page_tex, a.figdir, a.out, a.pdf, a.page))


if __name__ == "__main__":
    main()
