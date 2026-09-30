#!/usr/bin/env python3
"""digi_check.py — completeness/integrity checks for a digitized maths book (maths digitization v2.2).

Each converted page has two files in <book>/pages/: pNNNN.tex (the page) and pNNNN.json (its page entry + its figures):
  {"pdf_page":N,"printed_page":"…","status":"converted|whole-page-crop|skipped-kannada","unclear":K,"converted_by":"…",
   "figures":[{"id":"pNNNN-fK","file":"pNNNN-fK.png","pdf_page":N,"bbox":[…],"source":"cropped-lba|cropped-textbook|generated|modified",
               "bbox_method":"pdf_image|drawn","derived_from":"…"(generated/modified only),"sha256":"…","made_by":"…"}]}
One file per page, so agents converting pages in parallel never write the same file. manifest.json is ASSEMBLED from them.

    check    --book DIR --figdir DIR --pages 20-25,160-172 [--compile --pdf P]
    assemble --book DIR --book-id ID --pdf P             writes book.tex (pages in order) and manifest.json
    compile-book --book DIR --figdir DIR                  compiles book.tex (in a scratch copy under $HOME) and reports pages
Exit 1 on any FAIL. Unclear counts are reported, not failed.
"""
import argparse, hashlib, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = {"cropped-lba", "cropped-textbook", "generated", "modified"}
STATUS = {"converted", "whole-page-crop", "skipped-kannada", "skipped-nonsyllabus"}
FIG = re.compile(r"\\vyfig(?:inline)?(?:\[[^\]]*\])?\{([^}]+)\}")
UNC = re.compile(r"\\vyunclear\{")


def span(s):
    out = []
    for part in s.split(","):
        a, _, b = part.partition("-")
        out += list(range(int(a), int(b or a) + 1))
    return out


def load(book, n):
    j = os.path.join(book, "pages", f"p{n:04d}.json")
    t = os.path.join(book, "pages", f"p{n:04d}.tex")
    return (json.load(open(j, encoding="utf-8")) if os.path.exists(j) else None,
            open(t, encoding="utf-8").read() if os.path.exists(t) else None)


def check(a):
    fails, warns, unclear, figs = [], [], {}, 0
    ids_seen = {}
    for n in span(a.pages):
        meta, tex = load(a.book, n)
        tag = f"p{n:04d}"
        if meta is None:
            fails.append(f"{tag}: no page json"); continue
        if meta.get("pdf_page") != n: fails.append(f"{tag}: json pdf_page {meta.get('pdf_page')}")
        st = meta.get("status")
        if st not in STATUS: fails.append(f"{tag}: status {st!r}")
        if not meta.get("converted_by"): fails.append(f"{tag}: converted_by missing")
        if st.startswith("skipped-"):
            if tex is not None: fails.append(f"{tag}: {st} page has a .tex")
            continue
        if tex is None:
            fails.append(f"{tag}: no .tex"); continue
        if "\\documentclass" in tex or "\\begin{document}" in tex: fails.append(f"{tag}: .tex must be a page body, not a document")
        if "\\vypage{" not in tex: warns.append(f"{tag}: no \\vypage")
        k = len(UNC.findall(tex)); unclear[tag] = k
        if meta.get("unclear") != k: fails.append(f"{tag}: json unclear {meta.get('unclear')} vs .tex {k}")
        used = FIG.findall(tex)
        declared = {f.get("id"): f for f in meta.get("figures", [])}
        for u in used:
            if u not in declared: fails.append(f"{tag}: \\vyfig{{{u}}} not in its json")
        for fid, f in declared.items():
            figs += 1
            if fid in ids_seen: fails.append(f"{tag}: figure id {fid} also on {ids_seen[fid]}")
            ids_seen[fid] = tag
            if fid not in used: fails.append(f"{tag}: figure {fid} declared, not placed")
            if f.get("source") not in SOURCES: fails.append(f"{tag}: {fid} source {f.get('source')!r}")
            if f.get("source") in ("generated", "modified") and not f.get("derived_from"): fails.append(f"{tag}: {fid} needs derived_from")
            if f.get("bbox_method") not in ("pdf_image", "drawn"): fails.append(f"{tag}: {fid} bbox_method")
            if not f.get("made_by"): fails.append(f"{tag}: {fid} made_by missing")
            p = os.path.join(a.figdir, f.get("file", ""))
            if not os.path.isfile(p): fails.append(f"{tag}: {fid} file missing ({f.get('file')})")
            elif hashlib.sha256(open(p, "rb").read()).hexdigest() != f.get("sha256"): fails.append(f"{tag}: {fid} sha256 mismatch")
        if a.compile:
            r = subprocess.run([sys.executable, os.path.join(HERE, "digi_page.py"), "compile", "--pdf", a.pdf, "--page", str(n),
                                "--page-tex", os.path.join(a.book, "pages", f"{tag}.tex"), "--figdir", a.figdir,
                                "--out", os.path.join(os.path.expanduser("~"), "digi_check_out")], capture_output=True, text=True)
            if r.returncode: fails.append(f"{tag}: compile: {r.stdout.strip()[:200]}")
    pages = span(a.pages)
    print(f"pages {len(pages)} · figures {figs} · unclear {sum(unclear.values())} "
          f"({', '.join(f'{k}:{v}' for k, v in unclear.items() if v) or 'none'})")
    for w in warns: print("WARN", w)
    for f in fails: print("FAIL", f)
    print("RESULT", "FAIL" if fails else "PASS")
    return 1 if fails else 0


def assemble(a):
    pdir = os.path.join(a.book, "pages")
    nums = sorted(int(f[1:5]) for f in os.listdir(pdir) if re.fullmatch(r"p\d{4}\.json", f))
    pages, figures, body = [], [], []
    for n in nums:
        meta, tex = load(a.book, n)
        figures += meta.pop("figures", [])
        pages.append(meta)
        if tex is not None:
            body.append(f"\\label{{vypg:{n:04d}}}%\n\\input{{pages/p{n:04d}}}\n\\clearpage")
    m = re.search(r"(class-\d+)/maths/digitized/", os.path.abspath(a.book).replace(os.sep, "/"))
    if not m:
        sys.exit("assemble: the book folder must be <worktree>/class-N/maths/digitized/<book id>")
    cls = m[1]
    man = {"book": a.book_id, "source_pdf": os.path.basename(a.pdf),
           "source_sha256": hashlib.sha256(open(a.pdf, "rb").read()).hexdigest(),
           "figure_dir": f"_figures/{cls}/maths/{a.book_id}/", "pages": pages, "figures": figures}
    json.dump(man, open(os.path.join(a.book, "manifest.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    # contents.json (optional, in the book folder): {"title": "...", "entries": [{"title": "...", "pdf_page": N}, ...]}
    # Its entries are printed as a contents page pointing at THIS edition's page numbers (\pageref), not the book's.
    cpath = os.path.join(a.book, "contents.json")
    contents = ""
    if os.path.exists(cpath):
        c = json.load(open(cpath, encoding="utf-8"))
        rows = "\n".join(
            "%s & \\pageref{vypg:%04d} \\\\" % (e["title"].replace("&", "\\&"), e["pdf_page"])
            for e in c.get("entries", []) if e["pdf_page"] in nums)
        contents = ("\\thispagestyle{empty}\n\\begin{center}{\\Large %s}\\par\\vspace{8mm}\n"
                    "{\\large\\bfseries Contents}\\par\\vspace{4mm}\n"
                    "\\begin{tabular}{@{}p{0.72\\linewidth}r@{}}\n%s\n\\end{tabular}\\end{center}\n\\clearpage\n"
                    % (c.get("title", a.book_id).replace("&", "\\&"), rows))
    tex = ("% book.tex — generated by digi_check.py assemble; do not edit by hand\n"
           "\\documentclass[11pt]{article}\n\\usepackage{viyamo-maths}\n"
           "% set \\vyfigdir to the book's _figures folder (absolute, trailing slash) when compiling\n"
           "\\begin{document}\n" + contents + "\n".join(body) + "\n\\end{document}\n")
    open(os.path.join(a.book, "book.tex"), "w", encoding="utf-8").write(tex)
    print(f"assembled {len(pages)} pages, {len(figures)} figures")
    return 0


def compile_book(a):
    import shutil, tempfile
    work = tempfile.mkdtemp(dir=os.path.expanduser("~"))
    shutil.copytree(os.path.join(a.book, "pages"), os.path.join(work, "pages"))
    shutil.copy(os.path.join(a.book, "book.tex"), work)
    shutil.copy(os.path.join(os.path.dirname(HERE), "latex", "viyamo-maths.sty"), work)
    fd = os.path.abspath(a.figdir).rstrip("/") + "/"
    for _ in range(2):        # twice: the contents page's \pageref needs the first pass's labels
        r = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", "-jobname=book",
                            "\\def\\vyfigdir{" + fd + "}\\input{book.tex}"], cwd=work, capture_output=True, text=True, timeout=170)
        if r.returncode: break
    ok = r.returncode == 0
    msg = [l for l in open(os.path.join(work, "book.log"), encoding="utf-8", errors="replace") if l.startswith(("!", "Output written"))]
    shutil.rmtree(work)
    print("".join(msg).strip() or r.stdout[-300:]); print("RESULT", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    c = sp.add_parser("check"); c.add_argument("--book", required=True); c.add_argument("--figdir", required=True)
    c.add_argument("--pages", required=True); c.add_argument("--compile", action="store_true"); c.add_argument("--pdf")
    s = sp.add_parser("assemble"); s.add_argument("--book", required=True); s.add_argument("--book-id", required=True); s.add_argument("--pdf", required=True)
    b = sp.add_parser("compile-book"); b.add_argument("--book", required=True); b.add_argument("--figdir", required=True)
    a = ap.parse_args()
    if a.cmd == "compile-book": sys.exit(compile_book(a))
    if a.cmd == "check" and a.compile and not a.pdf: sys.exit("--compile needs --pdf")
    sys.exit(check(a) if a.cmd == "check" else assemble(a))


if __name__ == "__main__":
    main()
