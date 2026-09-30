#!/usr/bin/env python3
"""filecheck.py — structural gate for question-bank unit files.

Implements the VALIDATED checklist of contract 1.5 (question_schema_v5, log v1–v6),
contract 1.6 (question_schema_v6, log v4) and contract 1.7 (question_schema_v7, file layer).
Every rule is keyed to the contract the unit DECLARES: a 1.5 or 1.6 file is checked, and
sampled, exactly as gate 2.8 checked it. Standard library only.

Usage:
    python3 filecheck.py <unit.json> [--images DIR] [--json OUT] [--quiet]

Exit code 0 = PASS, 1 = FAIL, 2 = could not read the file.
Every finding names the question id and, where a fix is prescribed by the
contract, the exact vocabulary to use. This script checks STRUCTURE only;
the content sample against the printed page remains the coordinator's.
"""
import argparse, hashlib, json, os, re, sys, unicodedata
from collections import Counter

GATE_VERSION = "2.18"
# contract_version -> (log in force, contract filename stem)
CONTRACTS = {"1.5": ("v6", "question_schema_v5"), "1.6": ("v4", "question_schema_v6"),
             "1.7": ("v1", "question_schema_v7"), "1.8": ("v1", "question_schema_v7")}
# 1.8 = 1.7 + the maths addendum (LaTeX editions). Same schema file; addendum_file and procedure v3 required.
C17 = ("1.7", "1.8")
DEFAULT_CONTRACT = "1.5"
TYPES_15 = {"mcq", "mcq_multi", "true_false", "vsa", "sa", "la", "numeric", "ordering", "fill", "match"}
TYPES_16 = TYPES_15 | {"yes_no"}
TYPES_17 = TYPES_16 | {"composition"}
TYPES = {"mcq", "mcq_multi", "true_false", "vsa", "sa", "la", "numeric", "ordering", "fill", "match"}
STATES = {"EXTRACTED", "VALIDATED", "FIGURED", "REVIEW-READY", "STOPPED"}
DIFF = {"easy", "average", "difficult"}
MARKS_SOURCE = {"section_header", "unit_table", "blueprint_table", "same_form_elsewhere", "section_table", "unassigned", "subpart_sum"}
ROLES = {"figure", "answer_diagram", "page", "table", "map_outline"}
QUALITY = {"ok", "low"}
SOURCES = {"lba", "board_qb", "mqp", "board_paper", "textbook", "generated", "template"}
SOURCES_17 = {"lba", "board_qb", "mqp", "board_paper", "textbook", "teacher", "ai", "template"}
# a question whose source is one of these MUST carry a printed locator (1.7)
PRINTED_SOURCES = {"lba", "board_qb", "mqp", "board_paper", "textbook"}
LOC_ROLES = {"question", "answer", "textbook", "stimulus"}
LOC_DERIVED = {"text_layer", "ocr", "render_measured", "manual", "latex_edition"}
STIM_KINDS = {"passage", "poem", "table", "figure", "case", "source_extract", "map"}
PROV_BY = {"printed", "textbook_excerpt", "ai", "teacher", "reviewer"}
EVID_KINDS = {"textbook_excerpt", "lba_working", "stimulus_span"}
EVID_CONF = {"verbatim", "partial", "paraphrase_candidate"}
KINDS_FOR_TYPE = {
    "mcq": {"option"}, "true_false": {"option"}, "mcq_multi": {"multi_option"},
    "numeric": {"numeric", "text"}, "ordering": {"ordering", "text"}, "match": {"match", "text"},
    "vsa": {"text", "numeric"}, "sa": {"text", "numeric"}, "la": {"text", "numeric"}, "fill": {"text"},
}
VOCAB = [  # issue prefixes (text before an em dash) — contract 1.5 + logs v1–v6
    "key belongs to another paper version", "answer truncated in source", "shifted numbering",
    "sub-part labels shifted", "key text paraphrases option", "key text not among options",
    "key text does not address question", "no difficulty tag", "no answer printed", "no LO mapped",
    "marks ambiguous in source", "source notation inconsistent", "extraction damage",
    "inline answer pairing ambiguous", "duplicate of", "key text matches several options after normalisation",
    "printed result contradicts working", "match key not in pair form", "displacement boundary", "match key internally inconsistent", "keys contradict each other", "duplicate question number",
]
REVIEW_BLOCKING = {"key text not among options", "key text does not address question",
                   "printed result contradicts working", "shifted numbering", "no answer printed",
                   "key text matches several options after normalisation"}
# 1.7 additions (question_schema_v7 defect_flag_vocabulary). Contract-keyed: a 1.5 or 1.6
# file using them still FAILS, because its contract never defined them.
VOCAB_17_NEW = ["answer is a diagram", "duplicate stem", "key text differs from option by a printed typo",
                "unclassified"]
# 1.8 additions (contract_1_8_maths_addendum §4 and §6.0): one entry per \vyunclear in the question span or in
# the key, and the report-level slip note when a key's working carries a slip but its final line is consistent.
# Gate 2.17 (2026-09-26): absent from 2.16, which therefore FAILed any faithful 1.8 unit carrying a \vyunclear
# (c8-ext ch6 q023). Contract-keyed like the 1.7 list.
VOCAB_18_NEW = ["edition marks unclear", "edition marks unclear in key", "key working carries a slip"]
REVIEW_BLOCKING_17 = REVIEW_BLOCKING | {"displacement boundary", "duplicate stem"}
FLATTENED_NOTATION = re.compile(r"(?<![\w.])(cm3|m3|kg/m3|m/s2|ms-2|ms-1|H2O|CO2|O2|N2|H2|NH4\+|CaCO3|NaCl2|10-\d{1,2}|10\+\d{1,2}|\d0o ?C)(?![\w])")
# The 10-n / 10+n alternatives are a SCIENCE heuristic for a flattened power of ten ("10-3 m"). In maths the
# same characters are ordinary arithmetic ("a+(10-1)d"), so for any subject but sci they are not applied
# (gate 2.14, 2026-09-22; Class 10 maths pilot). Maths notation damage is judged by glyph measurement (§7).
FLATTENED_NOTATION_NONSCI = re.compile(r"(?<![\w.])(cm3|m3|kg/m3|m/s2|ms-2|ms-1|H2O|CO2|O2|N2|H2|NH4\+|CaCO3|NaCl2|\d0o ?C)(?![\w])")
TAG_RESIDUE = re.compile(r"\(\s*(easy|average|difficult)\b[^)]{0,3}\)?", re.I)
TABLE_RUN = re.compile(r"\S {4,}\S")
ID_RE    = re.compile(r"^[a-z]{2,4}-(\d{1,2}|puc-[12])-\d{2}-[sx]\d+-q\d{3}$")
# 2.12 (Yash, 2026-09-21): a yes_no answer may be the full sentence built at authoring ("No, plants …")
KINDS_17 = dict(KINDS_FOR_TYPE, yes_no={"option", "text"}, composition={"text", "rubric"})
# 1.6+ admits a letter suffix for a DUPLICATED printed number (1.6-a12): -q015, -q015b
ID_RE_16 = re.compile(r"^[a-z]{2,4}-(\d{1,2}|puc-[12])-\d{2}-[sx]\d+-q\d{3}[a-z]?$")


def normalise(t: str, cv: str = "1.5") -> str:
    """content_hash normalisation: NFC, lowercase, drop category-P except a . or ,
    standing between two digits (1.5-a5), collapse whitespace.
    Contract 1.6 (1.6-a11) additionally folds Unicode decimal digits to ASCII."""
    t = unicodedata.normalize("NFC", t).lower()
    if cv in ("1.6", "1.7", "1.8"):
        t = "".join(str(unicodedata.decimal(c)) if unicodedata.category(c) == "Nd" else c for c in t)
    out = []
    n = len(t)
    for i, c in enumerate(t):
        if unicodedata.category(c).startswith("P"):
            if c in ".," and 0 < i < n - 1 and t[i - 1].isdigit() and t[i + 1].isdigit():
                out.append(c)
        else:
            out.append(c)
    return re.sub(r"\s+", " ", "".join(out)).strip()


def png_dims(path):
    """Width and height from a PNG IHDR. Standard library only; None if not a PNG."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(24)
        if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
            return None
        return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")
    except Exception:
        return None


def check_locators(rep, owner, locs):
    """Validate every locator entry. Presence rules are the caller's."""
    for l in locs:
        if not isinstance(l, dict):
            rep.F(owner, "locator entry is not an object"); continue
        ed = l.get("derived_from") == "latex_edition"
        need = ("role", "source_ref", "pdf_page", "derived_from") + (("edition_page_file", "block") if ed else ("y",))
        miss = [k for k in need if k not in l]
        if miss:
            rep.F(owner, f"locator missing {', '.join(miss)}")
        if ed:
            if "y" in l:
                rep.F(owner, "locator from a LaTeX edition must not carry y (the edition has no coordinates; 1.8 §2)")
            if not re.fullmatch(r"p\d{4}\.tex", str(l.get("edition_page_file", ""))):
                rep.F(owner, f"locator.edition_page_file {l.get('edition_page_file')!r} must be pNNNN.tex")
            if isinstance(l.get("block"), bool) or not isinstance(l.get("block"), int) or l.get("block", 0) < 1:
                rep.F(owner, "locator.block must be a positive integer (item ordinal in the page .tex)")
        if "role" in l and l["role"] not in LOC_ROLES:
            rep.F(owner, f"locator.role {l['role']!r} not in {'|'.join(sorted(LOC_ROLES))}")
        if "derived_from" in l and l["derived_from"] not in LOC_DERIVED:
            rep.F(owner, f"locator.derived_from {l['derived_from']!r} not in {'|'.join(sorted(LOC_DERIVED))}")
        pg = l.get("pdf_page")
        if "pdf_page" in l and (isinstance(pg, bool) or not isinstance(pg, int) or pg < 1):
            rep.F(owner, f"locator.pdf_page {pg!r} must be a positive integer")
        yy = l.get("y")
        if "y" in l and (isinstance(yy, bool) or not isinstance(yy, (int, float)) or yy < 0):
            rep.F(owner, f"locator.y {yy!r} must be a non-negative number (PDF points)")


MATH_SEG = re.compile(r"(\\\[.*?\\\]|\\\(.*?\\\)|\\begin\{(align\*?|equation\*?)\}.*?\\end\{\2\}|\$[^$]*\$)", re.S)
PLACEHOLDER = re.compile(r"\[\[(a\d+)\]\]")


def normalise18(t: str, assets=None) -> str:
    """content_hash normalisation for contract 1.8 (LaTeX editions), addendum §7:
    a. [[aK]] -> [[<12 hex of asset aK sha256>]]; b. NFC; c. split math/text segments;
    d. text: unwrap textbf/textit/emph, blank -> _, drop list scaffolding, tabular cells in row order,
       lowercase, digits folded, category-P removed except . , between digits and the _ token, whitespace collapsed;
    e. math: all whitespace removed, \\left/\\right removed, dfrac/tfrac -> frac, single-char ^{x}/_{x} -> ^x/_x;
    f. segments joined by one space."""
    shas = {a.get("id"): str(a.get("sha256", ""))[:12] for a in (assets or []) if isinstance(a, dict)}
    t = PLACEHOLDER.sub(lambda m: "[[" + shas.get(m.group(1), "missing") + "]]", t)
    t = unicodedata.normalize("NFC", t)
    out = []
    pos = 0
    def text_norm(x: str) -> str:
        x = re.sub(r"\\(textbf|textit|emph|text)\{([^{}]*)\}", r"\2", x)
        x = re.sub(r"\\underline\{\\hspace\{[^}]*\}\}", " _ ", x)
        x = re.sub(r"\\(begin|end)\{(enumerate|itemize|tabular|center)\}(\{[^}]*\})?", " ", x)
        x = re.sub(r"\\(item|hline|hfill|quad|qquad)\b", " ", x)
        x = x.replace("\\\\", " ").replace("&", " ").lower()
        x = "".join(str(unicodedata.decimal(c)) if unicodedata.category(c) == "Nd" else c for c in x)
        keep = []
        n = len(x)
        for i, c in enumerate(x):
            if unicodedata.category(c).startswith("P"):
                if c == "_" or (c in ".," and 0 < i < n - 1 and x[i - 1].isdigit() and x[i + 1].isdigit()):
                    keep.append(c)
            else:
                keep.append(c)
        return re.sub(r"\s+", " ", "".join(keep)).strip()
    def math_norm(x: str) -> str:
        x = re.sub(r"\s+", "", x)
        x = x.replace("\\left", "").replace("\\right", "").replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
        x = re.sub(r"([\^_])\{(\w)\}", r"\1\2", x)
        return x
    for m in MATH_SEG.finditer(t):
        seg = text_norm(t[pos:m.start()])
        if seg: out.append(seg)
        out.append(math_norm(m.group(0)))
        pos = m.end()
    seg = text_norm(t[pos:])
    if seg: out.append(seg)
    return " ".join(out).strip()


def chash(t: str, cv: str = "1.5", assets=None) -> str:
    if cv == "1.8":
        return hashlib.sha256(normalise18(t, assets).encode("utf-8")).hexdigest()
    return hashlib.sha256(normalise(t, cv).encode("utf-8")).hexdigest()


MOJIBAKE = re.compile(r"â\u0082¹|â€|Ã[\x80-\xbf]|Â[\xa0-\xbf]|\ufffd")
FORBIDDEN_TEX = re.compile(r"\\(vy[a-z]+|documentclass|begin\{document\}|begin\{center\}|hfill|quad|qquad|setcounter|textcolor|newpage|marginpar)\b")


def check_latex18(rep, qid, q, text, opts, a):
    """Contract 1.8 §1.1 / §9: every text-bearing field is a LaTeX body fragment inside the allowed subset."""
    fields = [("text", text)]
    if isinstance(opts, list):
        fields += [(f"option {o.get('id')}", str(o.get("text", ""))) for o in opts if isinstance(o, dict)]
    elif isinstance(opts, dict):
        fields += [("option left", " ".join(map(str, opts.get("left", [])))), ("option right", " ".join(map(str, opts.get("right", []))))]
    if isinstance(a, dict):
        if isinstance(a.get("value"), str):
            fields.append(("answer", a["value"]))
        for p in a.get("parts") or []:
            if isinstance(p, dict) and isinstance(p.get("value"), str):
                fields.append((f"answer part {p.get('id')}", p["value"]))
    fields += [(f"solution_step {i+1}", str(x)) for i, x in enumerate(q.get("solution_steps") or [])]
    has_tab = False
    for name, val in fields:
        if len(re.findall(r"(?<!\\)\$", val)) % 2:
            rep.F(qid, f"{name}: unbalanced $ (1.8 §1.1)")
        depth = 0
        for ch in re.sub(r"\\[{}]", "", val):
            if ch == "{": depth += 1
            elif ch == "}": depth -= 1
            if depth < 0: break
        if depth != 0:
            rep.F(qid, f"{name}: unbalanced braces (1.8 §1.1)")
        m = FORBIDDEN_TEX.search(val)
        if m:
            rep.F(qid, f"{name}: \\{m.group(1)} is outside the allowed LaTeX subset (1.8 §1.1)")
        if "\\begin{tabular}" in val:
            has_tab = True
    if has_tab and q.get("has_table") is not True:
        rep.F(qid, "a tabular is present but has_table is not true (1.8 §1.1)")
    if q.get("has_table") is True and not has_tab:
        rep.F(qid, "has_table is true but no tabular is present")
    used = set(PLACEHOLDER.findall(" ".join(v for _, v in fields)))
    declared = {str(x.get("id")) for x in (q.get("assets") or []) if isinstance(x, dict)}
    for k in sorted(used - declared):
        rep.F(qid, f"placeholder [[{k}]] has no asset (1.8 §3)")
    for k in sorted(declared - used):
        rep.F(qid, f"asset {k} is declared but no [[{k}]] placeholder places it (1.8 §3)")
    for name, val in fields:
        if MOJIBAKE.search(val):
            rep.F(qid, f"{name}: mojibake {MOJIBAKE.search(val).group(0)!r} — the edition's UTF-8 was read or written as Latin-1 (1.8 §1.1; Test B Opus ch1 ₹)")
    tag = re.search(r"\((EASY|AVERAGE|DIFFICULT|[KUAS]P?-\s*(Easy|Average|Difficult))\)", text)
    if tag:
        rep.F(qid, f"printed tag {tag.group(0)!r} left in text (1.8 §5: removed and recorded as difficulty_as_printed)")


class Report:
    def __init__(self):
        self.fail, self.warn, self.info = [], [], []

    def F(self, qid, msg): self.fail.append((qid, msg))
    def W(self, qid, msg): self.warn.append((qid, msg))
    def I(self, qid, msg): self.info.append((qid, msg))


def issue_prefix(issue: str) -> str:
    if issue.startswith("duplicate of"):
        return "duplicate of"
    return issue.split(" — ")[0].strip()


def check_unit(u: dict, path: str, images_dir: str | None, rep: Report):
    # ---- file level -------------------------------------------------------
    cv = str(u.get("contract_version", ""))
    if cv not in CONTRACTS:
        rep.F("file", f"contract_version {cv!r} is not a contract this gate implements ({', '.join(sorted(CONTRACTS))})")
        cv = DEFAULT_CONTRACT
    cf = str(u.get("schema_file", "") if cv in C17 else u.get("contract_file", ""))
    stem_expected = CONTRACTS[cv][1]
    if stem_expected not in cf:
        key = "schema_file" if cv in C17 else "contract_file"
        rep.F("file", f"{key} {cf!r} does not name {stem_expected} (declared contract_version {cv})")
    stem = os.path.basename(path)
    mn = u.get("machine_name", "")
    if not mn or not stem.startswith(mn):
        rep.F("file", f"machine_name {mn!r} does not match filename {stem!r}")
    if not isinstance(u.get("version"), int):
        rep.F("file", "version must be an integer")
    if not u.get("changelog"):
        rep.F("file", "changelog missing")
    st = u.get("unit_state")
    if st not in STATES:
        rep.F("file", f"unit_state {st!r} not in {sorted(STATES)}")
    if u.get("review_ready") != (st == "REVIEW-READY"):
        rep.F("file", "review_ready must equal (unit_state == 'REVIEW-READY'), computed each build")
    am = u.get("amendments_applied", [])
    bad_am = [a for a in am if not str(a).startswith(cv + "-a")]
    if bad_am:
        rep.F("file", f"amendments_applied lists entries outside contract {cv}: {bad_am} (use '{cv}-a<n>')")
    qs = u.get("questions", [])
    if not isinstance(qs, list) or not qs:
        rep.F("file", "questions missing or empty")
        return
    cg = u.get("count_gate", {})
    if cg.get("reference_source") != "audited":
        rep.F("file", "count_gate.reference_source must be 'audited' (amendment 7 of 1.4, contract 1.5)")
    dups = cg.get("duplicated_numbers")
    if cv == "1.6" and dups is not None and not isinstance(dups, list):
        rep.F("file", "count_gate.duplicated_numbers must be a list of the numbers printed more than once (1.6-a12)")
    stim_ids = set()
    if cv in C17:
        if not isinstance(dups, list):
            rep.F("file", "count_gate.duplicated_numbers is required under 1.7 — a list, [] where the source prints none")
        if not (isinstance(u.get("procedure_file"), str) and u["procedure_file"].strip()):
            rep.F("file", "procedure_file missing — the procedure or addendum this unit was built against")
        if cv == "1.8":
            if "contract_1_8" not in str(u.get("addendum_file", "")):
                rep.F("file", "addendum_file must name the contract_1_8 maths addendum (1.8)")
            if "extraction_procedure_v3" not in str(u.get("procedure_file", "")):
                rep.F("file", "procedure_file must name extraction_procedure_v3 (LaTeX editions) under 1.8")
            if u.get("text_format") != "latex":
                rep.F("file", "text_format must be 'latex' under 1.8")
            ed = u.get("edition")
            if not isinstance(ed, dict):
                rep.F("file", "edition block missing (1.8 §1.2)")
            else:
                for k in ("book_id", "tag", "commit", "pages_dir", "figures_dir", "source_pdf", "source_sha256"):
                    if not str(ed.get(k) or "").strip():
                        rep.F("file", f"edition.{k} missing")
                if not re.fullmatch(r"[0-9a-f]{40}", str(ed.get("commit", ""))):
                    rep.F("file", "edition.commit must be the full 40-hex commit of the edition tag")
        stims = u.get("stimuli")
        if not isinstance(stims, list):
            rep.F("file", "stimuli missing — a list, [] where the unit has none")
            stims = []
        for sm_ in stims:
            if not isinstance(sm_, dict):
                rep.F("file", "stimulus entry is not an object"); continue
            sid = sm_.get("id")
            owner = f"stimulus {sid}"
            if not sid or sid in stim_ids:
                rep.F("file", f"stimulus id {sid!r} missing or duplicated")
            stim_ids.add(sid)
            if sm_.get("kind") not in STIM_KINDS:
                rep.F(owner, f"stimulus kind {sm_.get('kind')!r} not in {'|'.join(sorted(STIM_KINDS))}")
            if not str(sm_.get("text") or "").strip() and not sm_.get("assets"):
                rep.F(owner, "stimulus has neither text nor an asset")
            sl = sm_.get("locators")
            if not isinstance(sl, list) or not sl:
                rep.F(owner, "stimulus locators missing — a shared block is printed somewhere")
            else:
                check_locators(rep, owner, sl)
        ps = u.get("pending_summary")
        qs_ = u.get("questions") if isinstance(u.get("questions"), list) else []
        computed = dict(Counter(q.get("pending_category") for q in qs_ if q.get("pending_category")))
        if not isinstance(ps, dict):
            rep.F("file", "pending_summary missing — {} where nothing is pending")
        elif ps != computed:
            rep.F("file", f"pending_summary {ps} does not equal the computed counts {computed}")
        used = {q.get("stimulus_id") for q in qs_}
        for sid in sorted(x for x in stim_ids - used if x):
            rep.F("file", f"stimulus {sid!r} is attached to no question")
    if cg.get("extracted") != len(qs):
        rep.F("file", f"count_gate.extracted {cg.get('extracted')} != questions present {len(qs)}")
    if cg.get("reference") != cg.get("extracted"):
        rep.F("file", f"count_gate.reference {cg.get('reference')} != extracted {cg.get('extracted')}")
    if cg.get("pass") is not True:
        rep.F("file", "count_gate.pass is not true")
    qt_ok = {"consistent", "inconsistent", "unparsed"} | (
        {"absent", "difficulty_only"} if cv in ("1.6", "1.7", "1.8") else set())
    if cg.get("quota_table") not in qt_ok:
        rep.F("file", f"count_gate.quota_table must be one of {sorted(qt_ok)} (got {cg.get('quota_table')!r})")
    sm = cg.get("second_method")
    if not isinstance(sm, dict):
        rep.F("file", "count_gate.second_method missing (every count cross-checked by a second method: {method, extracted, agrees})")
    else:
        ok = sm.get("agrees") if "agrees" in sm else sm.get("agrees_with_reference")
        # 2.18 (v3 §7 v1.3): a 1.8 unit may reconcile an answer side that prints fewer keys than the
        # audited count by naming the unkeyed questions; each must carry 'no answer printed' or 'duplicate of',
        # and a shifted band needs the coordinator's verified_shifts.
        unk = sm.get("unkeyed")
        if unk is not None:
            if cv != "1.8":
                rep.F("file", "count_gate.second_method.unkeyed is a 1.8 field (gate 2.18)")
            elif not isinstance(unk, list) or not unk:
                rep.F("file", "count_gate.second_method.unkeyed must be a non-empty list of question ids")
            else:
                byid = {q.get("id"): q for q in qs if isinstance(q, dict)}
                for uid in unk:
                    q_ = byid.get(uid)
                    if q_ is None:
                        rep.F("file", f"second_method.unkeyed names {uid!r}, not a question in this unit")
                        continue
                    pre_ = [issue_prefix(f.get("issue", "")) for f in (q_.get("source_flags") or [])]
                    if not any(p_ in ("no answer printed", "duplicate of") for p_ in pre_):
                        rep.F(uid, "listed in second_method.unkeyed without a 'no answer printed' or 'duplicate of' flag")
                if isinstance(sm.get("extracted"), int) and sm["extracted"] + len(unk) != cg.get("reference"):
                    rep.F("file", f"second_method.extracted {sm.get('extracted')} + unkeyed {len(unk)} != reference {cg.get('reference')}")
                shifted = [q.get("id") for q in qs if isinstance(q, dict) and any(
                    issue_prefix(f.get("issue", "")) == "shifted numbering" for f in (q.get("source_flags") or []))]
                if shifted and not (u.get("extraction", {}).get("verified_shifts")):
                    rep.F("file", f"shifted numbering on {shifted} but extraction.verified_shifts is absent (coordinator's entry required, v2 §4.3)")
        if unk is None and cv == "1.8" and isinstance(sm.get("extracted"), int) and sm["extracted"] != cg.get("reference"):
            rep.F("file", f"second_method.extracted {sm['extracted']} != reference {cg.get('reference')} and no unkeyed list explains the difference (2.18)")
        if ok is not True:
            rep.F("file", "count_gate.second_method does not agree with the reference")
        if "agrees" not in sm:
            rep.W("file", "count_gate.second_method uses a non-standard key; standard shape is {method, extracted, agrees}")
    ex = u.get("extraction", {})
    for k in ("source_file", "method_notes"):
        if k not in ex:
            rep.W("file", f"extraction.{k} missing")
    if "notation_summary" not in ex:
        rep.F("file", "extraction.notation_summary missing (render/latex token counts, damage flags)")
    if "excluded_objects" not in ex and "notation_excluded" not in ex:
        rep.F("file", "extraction.excluded_objects missing (empty list is fine, presence is required)")

    # ---- per question -----------------------------------------------------
    ids = [q.get("id") for q in qs]
    dup_ids = [i for i, c in Counter(ids).items() if c > 1]
    if dup_ids:
        rep.F("file", f"duplicate ids {dup_ids}")
    hashes = Counter()
    for q in qs:
        qid = q.get("id", "?")
        id_re = ID_RE_16 if cv in ("1.6", "1.7", "1.8") else ID_RE
        if not id_re.match(str(qid)):
            rep.F(qid, "id does not match <subj>-<class>-<ch2>-s|x<n>-q<nnn>")
        if q.get("chapter_id") and not str(qid).startswith(str(q["chapter_id"])):
            rep.F(qid, f"chapter_id {q['chapter_id']!r} disagrees with id prefix")
        for k in ("class", "subject", "language", "chapter_id", "syllabus_map_version", "audience",
                  "type", "text", "answer", "source", "source_ref", "content_hash", "revision",
                  "status", "status_history", "created_by", "created_at"):
            if k not in q:
                rep.F(qid, f"required field {k!r} missing")
        t = q.get("type")
        types_ok = TYPES_17 if cv in C17 else (TYPES_16 if cv == "1.6" else TYPES_15)
        if t not in types_ok:
            rep.F(qid, f"type {t!r} not in enum")
        if q.get("source") not in (SOURCES_17 if cv in C17 else SOURCES):
            rep.F(qid, f"source {q.get('source')!r} not in enum")
        if cv in C17 and q.get("status") == "retired":
            if not q.get("retired_reason"):
                rep.F(qid, "status retired without retired_reason")
        elif q.get("status") != "draft" and q.get("status") not in ("reviewed", "live"):
            rep.F(qid, "status not in draft|reviewed|live")
        if not isinstance(q.get("revision"), int):
            rep.F(qid, "revision must be an integer")
        # marks
        m = q.get("marks")
        if m is None:
            if q.get("marks_source") not in MARKS_SOURCE:
                rep.F(qid, "marks null without a valid marks_source")
        elif not isinstance(m, (int, float)):
            rep.F(qid, "marks must be a number or null")
        if q.get("marks_source") is not None and q.get("marks_source") not in MARKS_SOURCE:
            rep.F(qid, f"marks_source {q.get('marks_source')!r} not in enum")
        # difficulty
        flags = q.get("source_flags") or []
        fl_prefixes = [issue_prefix(f.get("issue", "")) for f in flags]
        d = q.get("difficulty")
        if d is None:
            if "no difficulty tag" not in fl_prefixes:
                rep.F(qid, "difficulty null without flag 'no difficulty tag'")
        elif d not in DIFF:
            rep.F(qid, f"difficulty {d!r} not in enum")
        dap = q.get("difficulty_as_printed")
        if dap and re.search(r"[()]", dap):
            rep.F(qid, f"difficulty_as_printed {dap!r} carries tag punctuation (store the bare word)")
        # locators (1.7): a question from a printed document must say where it is printed
        if cv in C17:
            locs = q.get("locators")
            src = q.get("source")
            if not isinstance(locs, list):
                rep.F(qid, "locators must be a list (it may be empty only where the source is not a printed document)")
            else:
                if src in PRINTED_SOURCES:
                    if not locs:
                        rep.F(qid, f"locators empty but source is {src!r} — a question from a printed "
                                   "document must record where it is printed")
                    elif not any(isinstance(l, dict) and l.get("role") == "question" for l in locs):
                        rep.F(qid, "no locator with role 'question' — the page the stem is printed on is required")
                # template: ruled 2026-09-21 — a question generated from a template is printed nowhere, so its
                # locators are EMPTY like teacher/ai; the template record carries its own source. No warning.
                check_locators(rep, qid, locs)
            # answer provenance and evidence (1.7)
            pv = q.get("answer_provenance")
            ans = q.get("answer") or {}
            answered = bool(str(ans.get("value") or "").strip()) or ans.get("option_id") is not None \
                or bool(ans.get("parts") or ans.get("pairs") or ans.get("sequence") or ans.get("option_ids") or ans.get("criteria"))
            if pv is None:
                # ruled 2026-09-21: under 1.7 every stored answer says who supplied it (printed / teacher / ai /
                # reviewer) — an AI-authored key must never pass as a printed one
                if answered:
                    rep.F(qid, "answer stored without answer_provenance — required under 1.7 (who supplied the answer)")
            elif not isinstance(pv, dict):
                rep.F(qid, "answer_provenance must be an object {by, actor, at, basis}")
            else:
                miss = [k for k in ("by", "actor", "at", "basis") if not pv.get(k)]
                if miss:
                    rep.F(qid, f"answer_provenance missing {', '.join(miss)}")
                if pv.get("by") not in PROV_BY:
                    rep.F(qid, f"answer_provenance.by {pv.get('by')!r} not in {'|'.join(sorted(PROV_BY))}")
                if pv.get("by") == "printed" and src not in PRINTED_SOURCES:
                    rep.F(qid, f"answer_provenance.by is 'printed' but source {src!r} is not a printed document")
                if not answered:
                    rep.F(qid, "answer_provenance present on an empty answer — provenance describes an answer that exists")
            ev = q.get("answer_evidence")
            if ev is not None:
                if not isinstance(ev, list):
                    rep.F(qid, "answer_evidence must be a list")
                else:
                    for e in ev:
                        if not isinstance(e, dict):
                            rep.F(qid, "answer_evidence entry is not an object"); continue
                        if e.get("kind") not in EVID_KINDS:
                            rep.F(qid, f"answer_evidence.kind {e.get('kind')!r} not in {'|'.join(sorted(EVID_KINDS))}")
                        if not str(e.get("text") or "").strip():
                            rep.F(qid, "answer_evidence.text empty — evidence is stored verbatim, not pointed at")
                        if e.get("confidence") not in EVID_CONF:
                            rep.F(qid, f"answer_evidence.confidence {e.get('confidence')!r} not in {'|'.join(sorted(EVID_CONF))}")
                        if not isinstance(e.get("locator"), dict):
                            rep.F(qid, "answer_evidence.locator missing")
                        else:
                            check_locators(rep, qid, [e["locator"]])
            pc = q.get("pending_category")
            if pc is not None and not (isinstance(pc, str) and pc.strip()):
                rep.F(qid, "pending_category must be a non-empty category id when present")
            sid = q.get("stimulus_id")
            if sid is not None and sid not in stim_ids:
                rep.F(qid, f"stimulus_id {sid!r} names no stimulus in this unit")

        # learning outcomes
        lo = q.get("learning_outcomes")
        if not isinstance(lo, list):
            rep.F(qid, "learning_outcomes must be a list (may be empty)")
        elif not lo and "no LO mapped" not in fl_prefixes:
            rep.F(qid, "learning_outcomes empty without flag 'no LO mapped'")
        # text / hash
        text = q.get("text", "")
        if not text.strip():
            rep.F(qid, "text empty")
        elif q.get("content_hash") != chash(text, cv, q.get("assets")):
            rep.F(qid, "content_hash does not recompute under the current normalisation (amendment 5)")
        if re.search(r"\s\d{1,3}\s*$", text) and not text.rstrip().endswith("?") and len(text.split()) > 6 and re.search(r"[a-z)\.]\s+\d{1,3}$", text.rstrip()):
            rep.W(qid, "text ends in a bare number — check for a leaked page folio")
        hashes[q.get("content_hash")] += 1
        # answer
        a = q.get("answer") or {}
        kind = a.get("kind")
        kinds = KINDS_17 if cv in C17 else KINDS_FOR_TYPE
        if t in kinds and kind not in kinds[t]:
            rep.F(qid, f"answer.kind {kind!r} not allowed for type {t!r}")
        opts = q.get("options")
        if t == "mcq":
            if not isinstance(opts, list) or len(opts) < 2:
                rep.F(qid, "mcq without an options list")
            else:
                oid = {o.get("id") for o in opts}
                if len(oid) != len(opts):
                    rep.F(qid, "duplicate option ids")
                unpaired = {"shifted numbering", "no answer printed", "key belongs to another paper version"} & set(fl_prefixes)
                # "key text not among options" WITHOUT "letter kept" means no letter was printed,
                # so there is nothing to pair to and option_id must be null. With "letter kept" a
                # letter WAS printed and must be used.
                for _f in flags:
                    _i = _f.get("issue", "")
                    if _i.startswith("key text not among options") and "letter kept" not in _i:
                        unpaired = unpaired | {"key text not among options"}
                if kind == "option" and a.get("option_id") is None and not unpaired:
                    rep.F(qid, "mcq option_id is null without a shifted/no-answer flag")
                elif kind == "option" and a.get("option_id") is not None and a.get("option_id") not in oid:
                    rep.F(qid, f"answer.option_id {a.get('option_id')!r} does not resolve to an option")
        if t in ("true_false", "yes_no"):
            allowed = ("true", "false") if t == "true_false" else ("yes", "no")
            if kind == "option" and a.get("option_id") not in allowed:
                rep.F(qid, f"{t} option_id must be one of {allowed}")
            if t == "yes_no" and kind == "text":
                v = str(a.get("value") or "").strip()
                if v and not re.match(r"(?i)(yes|no)\b", v):
                    rep.F(qid, "yes_no answer as text must begin with Yes or No")
                pv_ = q.get("answer_provenance") or {}
                if re.sub(r"[\s.!]", "", v).lower() not in ("yes", "no") and pv_.get("by") == "printed":
                    rep.W(qid, "yes_no sentence answer marked answer_provenance.by 'printed' — the book prints a bare "
                               "Yes/No; a sentence is authored (procedure §4)")
            if opts:
                rep.F(qid, f"{t} carries options; they are implicit")
        if t == "match":
            if kind == "match" and "match key not in pair form" in fl_prefixes:
                rep.F(qid, "match answer stored as pairs but still flagged 'match key not in pair form' — drop the flag")
            if kind == "match":
                pairs = a.get("pairs")
                if not isinstance(pairs, list) or not pairs or not all(isinstance(p, dict) and "left" in p and "right" in p for p in pairs):
                    rep.F(qid, "match answer must be pairs: [{left, right}]")
            elif kind == "text":
                unpaired_match = {"shifted numbering", "displacement boundary", "no answer printed"} & set(fl_prefixes)
                has_pairflag = "match key not in pair form" in fl_prefixes
                if cv in ("1.6", "1.7", "1.8") and unpaired_match and has_pairflag:
                    rep.F(qid, "a displaced or unprinted match key carries only its defect flag — drop 'match key not in pair form' (1.6-a2)")
                elif not unpaired_match and not has_pairflag and "match key internally inconsistent" not in fl_prefixes:
                    rep.F(qid, "match stored as text needs 'match key not in pair form' or 'match key internally inconsistent'")
        if kind == "numeric":
            parts = a.get("parts")
            if not isinstance(parts, list) or not parts:
                rep.F(qid, "numeric answer without parts")
            else:
                for p in parts:
                    if cv == "1.8":
                        if not (isinstance(p.get("value"), (int, float)) or (isinstance(p.get("value"), str) and p["value"].strip())):
                            rep.F(qid, f"numeric part {p.get('id')} value must be a number or a non-empty LaTeX string (1.8 §6)")
                        if "value_num" in p and (isinstance(p["value_num"], bool) or not isinstance(p["value_num"], (int, float))):
                            rep.F(qid, f"numeric part {p.get('id')} value_num is not a number")
                    elif not isinstance(p.get("value"), (int, float)):
                        rep.F(qid, f"numeric part {p.get('id')} value is not a number")
                    if p.get("tolerance") is not None and not isinstance(p.get("tolerance"), (int, float)):
                        rep.F(qid, f"numeric part {p.get('id')} tolerance is not a number")
                    if "label" in p and p.get("label_source") not in (None, "question", "answer"):
                        rep.F(qid, f"numeric part {p.get('id')} label_source not in question|answer")
        if kind == "text":
            val = a.get("value") or ""
            if not val.strip() and not flags:
                rep.F(qid, "empty text answer without a source_flags entry")
            if cv != "1.8" and TABLE_RUN.search(val) and not q.get("solution_steps"):
                rep.F(qid, "answer looks like a flattened table (space-padded run) with no solution_steps — one step per printed row, cells joined ' | ' (log v6 §1)")
            if "\n" in val.strip() and not q.get("solution_steps"):
                rep.W(qid, "multi-line answer without solution_steps")
        # flags
        seen = set()
        for f in flags:
            iss = f.get("issue", "")
            pre = issue_prefix(iss)
            allowed = VOCAB + VOCAB_17_NEW + (VOCAB_18_NEW if cv == "1.8" else []) if cv in C17 else VOCAB
            if pre not in allowed:
                rep.F(qid, f"flag issue {iss!r} is not in the defect vocabulary")
            key = (f.get("field"), iss)
            if key in seen:
                rep.F(qid, f"duplicate flag {iss!r}")
            seen.add(key)
            if pre == "unclassified":
                # the LAST resort (schema v7 rev 4): only when no vocabulary entry fits
                desc = iss.split(" — ", 1)[1].strip() if " — " in iss else ""
                if len(desc.split()) < 3:
                    rep.F(qid, "'unclassified' needs a description: 'unclassified — <what is wrong, in a sentence>'")
                if q.get("pending_category") != "unclassified":
                    rep.F(qid, "an 'unclassified' flag must set pending_category 'unclassified'")
                # nearest = a vocabulary entry, or a register category as 'category:<id>'. The gate
                # cannot see the register; pending.py checks that a named category exists.
                m_ = re.match(r"\s*nearest:\s*(.+?)\s+—\s+\S", str(f.get("suggested") or ""))
                near = m_.group(1).strip() if m_ else ""
                is_cat = bool(re.fullmatch(r"category:[a-z0-9]+(?:-[a-z0-9]+)*", near)) and near != "category:unclassified"
                is_voc = issue_prefix(near) in VOCAB + VOCAB_17_NEW + VOCAB_18_NEW and issue_prefix(near) != "unclassified"
                if not (is_cat or is_voc):
                    rep.F(qid, "'unclassified' needs suggested 'nearest: <closest vocabulary entry, or category:<id>> — "
                               "<why it does not fit>' — the catch-all is used only after the existing ones were tried")
            if pre == "displacement boundary" and cv not in ("1.6", "1.7"):
                rep.F(qid, "'displacement boundary' is a 1.6 entry; this file declares " + cv)
            if pre == "shifted numbering":
                if a.get("value") or a.get("option_id") is not None:
                    rep.F(qid, "shifted-numbering question must have an EMPTY answer; pointer goes in suggested")
                if not f.get("suggested"):
                    rep.F(qid, "shifted-numbering flag needs suggested (the pointer)")
            sug = str(f.get("suggested") or "")
            # A key describing ITS OWN number is not a pointer at another key.
            # Class 8 sci-8-11-s4-q078: "key 78" in the suggestion of a
            # "key text does not address question" flag on question 078.
            own = re.search(r"q(\d{3})$", str(qid))
            named = {int(m) for m in re.findall(r"\bkey\s*(\d+)\b", sug, re.I)}
            if own:
                named.discard(int(own.group(1)))
            if pre not in ("shifted numbering", "displacement boundary") and named and (a.get("value") or a.get("option_id") is not None):
                rep.F(qid, f"flag {pre!r} points at another key in suggested but an answer is stored — use 'shifted numbering — see key N' with an EMPTY answer")
            if pre == "no answer printed" and (a.get("value") or a.get("option_id") is not None):
                rep.F(qid, "'no answer printed' but an answer is stored")
            sugg_expected = ["key text matches several options after normalisation", "sub-part labels shifted"]
            if cv in ("1.5", "1.6"):  # 1.7 exempts 'no LO mapped': naming an LO the source does not name is authoring
                sugg_expected.append("no LO mapped")
            if pre in sugg_expected and not f.get("suggested"):
                rep.W(qid, f"flag {pre!r} usually carries suggested")
        for c in q.get("source_corrections") or []:
            if not all(k in c for k in ("field", "printed", "corrected", "basis")):
                rep.F(qid, "source_corrections entry lacks field/printed/corrected/basis")
        # content residue (1.7, WARN) — procedure §3 and §6. Warnings, not failures: a port may not
        # change content, so a ported unit keeps these defects and the register carries them.
        if cv in C17:
            blob_tr = text + " " + " ".join(o.get("text", "") for o in (opts if isinstance(opts, list) else []))
            m_tag = TAG_RESIDUE.search(blob_tr)
            if m_tag:
                rep.W(qid, f"difficulty tag text {m_tag.group(0)!r} left in the question or its options (procedure §6)")
            if opts and t not in ("mcq", "mcq_multi", "match"):
                rep.W(qid, f"type {t!r} carries options — lettered sub-parts or labels belong in text (procedure §3)")
        # notation residue
        blob = " ".join([text] + [o.get("text", "") for o in (opts if isinstance(opts, list) else [])] +
                        [json.dumps(a, ensure_ascii=False)] + list(q.get("solution_steps") or []))
        fn = FLATTENED_NOTATION if str(qid).startswith("sci-") else FLATTENED_NOTATION_NONSCI
        if cv != "1.8" and fn.search(blob) and "extraction damage" not in fl_prefixes and "source notation inconsistent" not in fl_prefixes:
            rep.F(qid, f"flattened notation {fn.search(blob).group(0)!r} in text/options/answer/steps with no 'extraction damage' flag")
        if cv == "1.8":
            check_latex18(rep, qid, q, text, opts, a)
        # assets
        for asset in q.get("assets") or []:
            if asset.get("role") not in ROLES:
                rep.F(qid, f"asset role {asset.get('role')!r} not in enum")
            if asset.get("quality") not in QUALITY:
                rep.F(qid, f"asset quality {asset.get('quality')!r} not in enum")
            ref = asset.get("ref", "")
            # 1.6-a14 / Class 6: an asset must live in ITS OWN chapter's folder. A file
            # referenced by unit A but sitting in unit B's folder passes both an existence
            # check and a naive orphan check, and that is the shape the Class 6 ch1 error
            # would have taken if the folder had been mis-set instead of the page range.
            parts = str(ref).split("/")
            if len(parts) >= 2 and parts[0] == "images" and q.get("chapter_id") and parts[1] != q["chapter_id"]:
                rep.F(qid, f"asset {ref!r} lives in {parts[1]!r} but this question belongs to {q['chapter_id']!r}")
            if images_dir:
                p = os.path.join(images_dir, os.path.basename(ref))
                p2 = os.path.join(os.path.dirname(path), ref)
                if not (os.path.exists(p) or os.path.exists(p2)):
                    rep.F(qid, f"asset file {ref!r} not found")
            if cv == "1.8":
                # 2.16: the editions name re-cut crops pNNNN-fKb, -fKc … (letter) as well as -fKr2 (rN); both are
                # what the page json carries and the figure_id must equal the page json's (Test B, Opus ch4)
                if not re.fullmatch(r"p\d{4}-f\d+[a-z]?(r\d+)?", str(asset.get("figure_id", ""))):
                    rep.F(qid, f"asset {ref!r} figure_id {asset.get('figure_id')!r} must be pNNNN-fK[letter][rN], the edition's own id (1.8 §3)")
                if not str(asset.get("book_id") or "").strip():
                    rep.F(qid, f"asset {ref!r} book_id missing (1.8 §3)")
                sha = str(asset.get("sha256", ""))
                if not re.fullmatch(r"[0-9a-f]{64}", sha):
                    rep.F(qid, f"asset {ref!r} sha256 missing or not 64 hex (1.8 §3)")
                elif images_dir:
                    pth = os.path.join(images_dir, os.path.basename(ref))
                    if not os.path.exists(pth):
                        pth = os.path.join(os.path.dirname(path), ref)
                    if os.path.exists(pth):
                        with open(pth, "rb") as fh_:
                            if hashlib.sha256(fh_.read()).hexdigest() != sha:
                                rep.F(qid, f"asset {ref!r} sha256 does not match the file (the crop was altered or the wrong crop copied)")
                if "inline" in asset and not isinstance(asset["inline"], bool):
                    rep.F(qid, f"asset {ref!r} inline must be true|false")
            if cv in C17:
                ap_ = asset.get("pdf_page")
                if isinstance(ap_, bool) or not isinstance(ap_, int) or ap_ < 1:
                    rep.F(qid, f"asset {ref!r} pdf_page {ap_!r} must be a positive integer (1.7)")
            px = asset.get("source_px") or {}
            if not (isinstance(px.get("w"), int) and isinstance(px.get("h"), int)):
                rep.W(qid, "asset source_px missing w/h")
        # review-blocking
        rb = [p for p in fl_prefixes if p in (REVIEW_BLOCKING_17 if cv in C17 else REVIEW_BLOCKING)]
        if rb:
            rep.I(qid, f"review-blocking: {rb}")
    # every file in this unit's image folder must be referenced by this unit
    if images_dir and os.path.isdir(images_dir):
        referenced = {os.path.basename(a.get("ref", "")) for q in qs for a in (q.get("assets") or [])}
        on_disk = {fn for fn in os.listdir(images_dir) if fn.lower().endswith((".png", ".jpg", ".jpeg"))}
        for fn in sorted(on_disk - referenced):
            rep.F("file", f"orphan image {fn!r} in {os.path.basename(images_dir)}/ is referenced by no question")

    # a stencil mask extracts as one flat colour and compresses to almost nothing.
    # Heuristic, so it WARNS: it names the asset for the coordinator rather than blocking.
    # Threshold 0.02 B/px — the known case was 200 B for 179x190 = 0.0059; real art runs 0.05-3.
    if images_dir and os.path.isdir(images_dir):
        for q in qs:
            for a in (q.get("assets") or []):
                fn = os.path.basename(a.get("ref", ""))
                path = os.path.join(images_dir, fn)
                if not fn.lower().endswith(".png") or not os.path.isfile(path):
                    continue
                dim = png_dims(path)
                if not dim:
                    continue
                w, h = dim
                if w * h == 0:
                    continue
                bpp = os.path.getsize(path) / (w * h)
                if bpp < 0.02:
                    rep.W(q.get("id"), f"asset {fn!r} is {w}x{h} at {bpp:.4f} bytes/pixel — "
                                       "likely a flat stencil mask, not the printed figure; "
                                       "open it before FIGURED")

    # duplicates by hash
    for h, c in hashes.items():
        if c > 1:
            members = [q for q in qs if q.get("content_hash") == h]
            for q in members:
                pres = [issue_prefix(f.get("issue", "")) for f in q.get("source_flags") or []]
                if cv in C17:
                    for f in q.get("source_flags") or []:
                        if issue_prefix(f.get("issue", "")) == "duplicate stem":
                            m_ = re.search(r"([a-z]{2,4}-(?:\d{1,2}|puc-[12])-\d{2}-[sx]\d+-q\d{3}[a-z]?)\s*$", f.get("issue", ""))
                            partners = {x.get("id") for x in members} - {q.get("id")}
                            if not m_ or m_.group(1) not in partners:
                                rep.F(q.get("id"), "'duplicate stem — keys differ' must end with its partner's id, "
                                                   "a question sharing this content_hash")
                ok_flags = {"duplicate of", "duplicate stem"} if cv in C17 else {"duplicate of"}
                if not ok_flags & set(pres):
                    rep.F(q.get("id"), "duplicate content_hash without 'duplicate of <id>' flag"
                          + (" or 'duplicate stem — keys differ'" if cv in C17 else ""))


def _sample_v1(qs, seed: str, n: int = 3):
    """Content-sample selection, seeded by the FULL batch commit SHA and recomputable.

    Two UNFLAGGED questions, spanning different types where possible, plus ONE flagged.
    Rationale: per-question verification now happens in the authoring pass, which reads the
    printed page; this sample exists to catch SYSTEMATIC extraction defects, and those hide
    in unflagged questions (an option silently dropped is not flagged). The one flagged pick
    tests the thread's FLAG CLASSIFICATION, which is judgement a gate cannot check and where
    two real misclassifications have been found."""
    import random
    def pre(q): return {issue_prefix(f.get("issue", "")) for f in (q.get("source_flags") or [])}
    def substantive(q):  # a missing difficulty tag is not a defect worth sampling
        return {p for p in pre(q) if p != "no difficulty tag"}
    rng = random.Random(seed)
    unflagged = [q for q in qs if not substantive(q)]
    flagged = [q for q in qs if substantive(q)]
    chosen, seen_types = [], set()
    pool = sorted(unflagged, key=lambda q: q["id"])
    rng.shuffle(pool)
    for q in pool:                      # prefer distinct types
        if q.get("type") not in seen_types:
            chosen.append(q["id"]); seen_types.add(q.get("type"))
        if len(chosen) == max(1, n - 1):
            break
    for q in pool:                      # top up if the unit has few types
        if len(chosen) >= max(1, n - 1):
            break
        if q["id"] not in chosen:
            chosen.append(q["id"])
    fpool = sorted(flagged, key=lambda q: q["id"])
    rng.shuffle(fpool)
    if fpool:
        chosen.append(fpool[0]["id"])
    return sorted(chosen[:n])


def _sample_v2(qs, seed: str, n: int = 5):
    """Content-sample selection, seeded by the FULL batch commit SHA and recomputable.

    Five per unit (extraction_procedure_v2 s14): THREE unflagged spanning distinct types,
    ONE flagged, ONE figure-bearing (a fourth unflagged where the unit carries no figure).
    This is a recomputable STARTING set: since the coordinator now renders source pages on
    demand, ids may be chosen after the pages are read, which the thread cannot anticipate.
    Rationale: per-question verification now happens in the authoring pass, which reads the
    printed page; this sample exists to catch SYSTEMATIC extraction defects, and those hide
    in unflagged questions (an option silently dropped is not flagged). The one flagged pick
    tests the thread's FLAG CLASSIFICATION, which is judgement a gate cannot check and where
    two real misclassifications have been found."""
    import random
    def pre(q): return {issue_prefix(f.get("issue", "")) for f in (q.get("source_flags") or [])}
    def substantive(q):  # a missing difficulty tag is not a defect worth sampling
        return {p for p in pre(q) if p != "no difficulty tag"}
    def figured(q): return bool(q.get("assets"))
    rng = random.Random(seed)
    unflagged = [q for q in qs if not substantive(q)]
    flagged   = [q for q in qs if substantive(q)]
    chosen, seen_types = [], set()

    # one figure-bearing pick, from anywhere in the unit
    fig = sorted([q for q in qs if figured(q)], key=lambda q: q["id"])
    rng.shuffle(fig)
    if fig:
        chosen.append(fig[0]["id"]); seen_types.add(fig[0].get("type"))

    # one flagged pick — tests the thread's flag CLASSIFICATION
    fpool = sorted(flagged, key=lambda q: q["id"])
    rng.shuffle(fpool)
    for q in fpool:
        if q["id"] not in chosen:
            chosen.append(q["id"]); seen_types.add(q.get("type")); break

    # the rest unflagged, spanning distinct types — systematic defects hide here
    pool = sorted(unflagged, key=lambda q: q["id"])
    rng.shuffle(pool)
    for q in pool:
        if len(chosen) >= n: break
        if q["id"] in chosen: continue
        if q.get("type") not in seen_types:
            chosen.append(q["id"]); seen_types.add(q.get("type"))
    for q in pool:                       # top up where the unit has few types
        if len(chosen) >= n: break
        if q["id"] not in chosen:
            chosen.append(q["id"])
    for q in sorted(qs, key=lambda q: q["id"]):   # tiny units: take what exists
        if len(chosen) >= n: break
        if q["id"] not in chosen:
            chosen.append(q["id"])
    return sorted(chosen[:n])


def sample_ids(qs, seed: str, cv: str = "1.5"):
    """The sampling rule belongs to the contract a unit was TAGGED under, not to the gate
    that happens to run. A 1.5 or 1.6 batch re-checked by this gate draws exactly the ids
    gate 2.8 drew (_sample_v1, verbatim); only a 1.7 unit uses _sample_v2. Without this, a
    re-check performs a rule that postdates the tag — the c6-sci-batch-04 failure."""
    return _sample_v2(qs, seed) if cv in C17 else _sample_v1(qs, seed)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("unit")
    ap.add_argument("--images", default=None, help="images/<chapter_id> directory; default derived from the JSON's location")
    ap.add_argument("--json", default=None, help="write findings as JSON to this path")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--sample", default=None, metavar="COMMIT_SHA", help="print the content-sample ids for this batch commit; seed with the FULL 40-character commit SHA")
    args = ap.parse_args()
    try:
        with open(args.unit, encoding="utf-8") as fh:
            u = json.load(fh)
    except Exception as e:  # noqa
        print(f"ERROR: cannot read {args.unit}: {e}")
        sys.exit(2)
    images = args.images
    if images is None and u.get("questions"):
        ch = u["questions"][0].get("chapter_id", "")
        cand = os.path.join(os.path.dirname(os.path.abspath(args.unit)), "images", ch)
        images = cand if os.path.isdir(cand) else None
    rep = Report()
    check_unit(u, args.unit, images, rep)
    verdict = "PASS" if not rep.fail else "FAIL"
    if args.sample:
        print("SAMPLE", " ".join(sample_ids(u.get("questions", []), args.sample, str(u.get("contract_version", "")))))
    if not args.quiet:
        cvp = str(u.get("contract_version", "?")); lg = CONTRACTS.get(cvp, ("?", "?"))[0]
        print(f"filecheck {GATE_VERSION} — file declares contract {cvp} (log {lg}); gate implements {', '.join(sorted(CONTRACTS))}")
        print(f"{verdict}  {os.path.basename(args.unit)}  questions={len(u.get('questions', []))}  fail={len(rep.fail)} warn={len(rep.warn)} review-blocking={len(rep.info)}")
        for qid, msg in rep.fail:
            print(f"  FAIL  {qid}: {msg}")
        for qid, msg in rep.warn:
            print(f"  WARN  {qid}: {msg}")
        if rep.info and not args.quiet:
            print(f"  INFO  review-blocking questions: {len(rep.info)}")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"verdict": verdict, "unit": os.path.basename(args.unit),
                       "fail": rep.fail, "warn": rep.warn, "review_blocking": rep.info}, fh, ensure_ascii=False, indent=1)
    sys.exit(0 if verdict == "PASS" else 1)


if __name__ == "__main__":
    main()
