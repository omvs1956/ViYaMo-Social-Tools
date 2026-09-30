CONTRACT 1.8 · MATHS ADDENDUM TO question_schema 1.7 · v1.3a DRAFT · 2026-09-25 · for Yash's critical analysis
(v1.3, from Test B: keys copied never composed; MCQ letter-vs-text rule; UTF-8; numeric only for a bare printed number;
 figure_id forms; contradicts-working flag)
(v1.2: difficulty_as_printed is the bare word, matching the gate; mixed key = working + figure rule)
(v1.1: coordinator's own critical pass — allowed-LaTeX subset, tables, hash fixes, numeric value_num, type precedence,
proof keys, actor carries the model, extraction block for editions, unclear-on-key flag)
Layer: FILE (immutable once tagged). Status: PROPOSED. Companion: extraction_procedure_v3 (LaTeX editions).

0. WHAT THIS IS
   Contract 1.7 stands unchanged. 1.8 = 1.7 + this addendum, for units whose SOURCE is a LaTeX edition produced by
   maths digitization v2.2 (a book folder of pNNNN.tex / pNNNN.json + _figures crops, tagged in viyamo-staging).
   Science units stay on 1.7. A 1.8 unit file carries:
     "contract_version": "1.8"
     "schema_file": "question_schema_v7_… .json"          (unchanged)
     "addendum_file": "<this file>"
     "procedure_file": "extraction_procedure_v3_… .md"
   Every 1.7 rule applies unless a numbered item below replaces it. Six additions, one profile, one flag.

1. UNIT-LEVEL ADDITIONS
   1.1 "text_format": "latex" — REQUIRED. Every Question.text, options[].text, answer.value (text/numeric),
       solution_steps[], Stimulus.text in the unit is a LaTeX BODY FRAGMENT: inline $…$, \[…\], align*,
       \frac, ^{}, _{}, \sqrt, \angle …; no \documentclass, no \begin{document}, and NONE of the edition's
       \vy* macros (\vypage, \vyfig, \vyfiginline, \vyunclear, \vycont) — those are consumed at extraction
       (see 3, 4, 6). Text outside math is plain UTF-8; LaTeX commands are preferred to Unicode symbols
       inside math, exactly as the edition has them.
       ALLOWED CONSTRUCTS (the subset a renderer and the gate are built for; anything else is a gate FAIL):
         math:  $…$  \[…\]  \(…\)  align*  and amsmath/amssymb commands; \text{…} inside math
         text:  \textbf{…} \textit{…} \emph{…} \underline{\hspace{<len>}} (a printed blank)  \\ (line break)
                enumerate / itemize with \item (sub-parts (a), (b), (i), (ii) …)
                tabular (a printed table in the question or key) — kept VERBATIM, and the question gets
                "has_table": true so a renderer that cannot draw tabular can fall back to the page asset.
         nothing else: no \begin{center}, no \hfill, no \quad/\qquad (spacing is not content), no colour, no
         \vy* macro, no \setcounter. The extractor strips spacing commands and center wrappers.
       ENCODING: the edition is UTF-8; every read and write names utf-8 explicitly (open(..., encoding="utf-8");
       json.dump(..., ensure_ascii=False)). A "₹" that arrives as "â\x82¹" is a corrupted question (Test B,
       Opus q56) and the gate fails it (mojibake check, 2.16).
   1.2 "edition": REQUIRED —
       {"book_id": "lba-math-8", "tag": "c8-mathtex-batch-01", "commit": "<40-hex>",
        "pages_dir": "class-8/maths/digitized/lba-math-8/pages", "figures_dir": "_figures/class-8/maths/lba-math-8",
        "source_pdf": "<original filename verbatim>", "source_sha256": "<from the edition's manifest>"}
       The edition, not the PDF, is what the extractor read. A correction commit to the edition after this tag
       does not change the unit; a re-extraction from the corrected edition is a new unit version.

2. LOCATORS FROM AN EDITION (replaces 1.7 Locator for these units)
   {"role": "question"|"answer"|"stimulus",
    "source_ref": "<original PDF filename> ch<N> Q<n>"     (1.7 rule, unchanged)
    "pdf_page": <int, = the page json's pdf_page>,
    "printed_page": <int|"none", = the page json's printed_page>,
    "edition_page_file": "pNNNN.tex",
    "block": <int — the item's ordinal among top-level items in that .tex, counting from 1 in file order>,
    "derived_from": "latex_edition"}
   "y" is ABSENT for derived_from latex_edition (the edition has no coordinates). 1.7's requirement that a
   printed-source question carries at least a role:question locator stands; an LBA question carries a
   role:answer locator too, pointing at the answers page.

3. ASSETS FROM AN EDITION (extends 1.7 Asset)
   The edition's crop IS the asset; nothing is re-cropped. Each \vyfig{id} / \vyfiginline[..]{id} inside a
   question's span becomes:
   {"id": "<question-local id, a1, a2…>", "type": "image",
    "ref": "images/<chapter_id>/<figure_id>.png",         (a COPY of the crop, so the unit is self-contained)
    "figure_id": "<exactly the page json's id: pNNNN-fK, pNNNN-fKb/-fKc (a re-cut, letter suffix) or pNNNN-fKrN>",
    "book_id": "<edition.book_id>",
    "sha256": "<the crop's sha256 from the page json — MUST equal the copied file's>",
    "role": "figure"|"answer_diagram"|"table"|"page", "pdf_page": <int>,
    "source_px": {"w","h"} (from the PNG), "quality": "ok",
    "inline": true|false — true when the edition placed it \vyfiginline (a symbol inside a line: the text keeps
    a placeholder [[a1]] at that position, so a renderer can put the image back inline)}
   A \vyfig inside the text span is replaced by the placeholder [[aK]] on its own line. The sha256 of the crop
   takes part in content_hash (7a) so two figure-only questions with different pictures never collide. A crop that is the
   ANSWER (a construction, a drawing) is role answer_diagram and the answer is {kind:"text", value:"[diagram
   answer — see asset aK]"} per 1.7.

4. UNCLEAR MARKS (new defect-flag vocabulary entry)
   "edition marks unclear — <best reading>": the edition wrote \vyunclear{…} inside this question's span. The
   text keeps the best reading WITHOUT the macro; source_flags gets this entry with the reading; NOT review-
   blocking, NOT category-pending — the reviewer resolves it against the page image (edition_page_file +
   pdf_page point at it). One entry per \vyunclear occurrence; an occurrence inside the KEY is the entry
   "edition marks unclear in key — <best reading>" and the answer is still stored (provenance printed).

5. TAGS PRINTED BY THE LBA (how 1.7 fields are filled; no new fields)
   difficulty: from the printed tag "(EASY)" / "(AVERAGE)" / "(DIFFICULT)" or "(K-Easy)" forms →
               easy|average|difficult; difficulty_as_printed = the BARE word as printed ("EASY", "Easy" — no
               parentheses or dashes; the gate rejects tag punctuation); difficulty_source "printed".
   objective:  from "(K-…)", "(U-…)", "(A-…)", "(S-…)", "(AP-…)" → knowledge|understanding|application|skill
               (AP → application); objective_as_printed = the bare letter(s) as printed; absent → objective null
               (Class 8's LBA prints difficulty only). Not gate-enforced under 2.15: a free string field in 1.7.
   marks:      from the section header ("II. One mark questions", "5 × 1 = 5", "(5x2=10)") → marks_source
               "section_header"; a header without a figure → marks null + "marks ambiguous in source — <header>".
   learning_outcomes: from the CHAPTER's LO table (the "LO No · Learning Outcomes · Question Numbers" table on
               the chapter's first question page): every question number listed under an LO row gets
               {number:"<LO No>", text_as_printed:"<row text>"}; lo_source "chapter_table". A number in no row →
               learning_outcomes [] + "no LO mapped". A number in two rows → both LOs, in row order.
   type:       decided in this precedence — (1) FORM: options A)–D) → mcq; a printed blank in the stem → fill;
               "true/false" header → true_false; two columns to pair → match; (2) KEY: numeric ONLY when the
               key's final printed line is a BARE number or quantity ("36", "168", "21 m", "$\frac{5}{8}$") —
               a sentence that ends in a number ("The perfect square between 30 and 40 is 36", "total number
               of students $= 77$") is NOT bare and stays text; (3) MARKS: 1 → vsa, 2–3 → sa, ≥ 4 → la.
               A "prove/show that" question is la/sa by marks with a text answer (6), never numeric.
               (Test B: the two runs split on exactly this; the bare-line rule is the tie-break.)
   section:    id segment s<N> = the Roman-numbered section's ORDER on the question side (1.7 rule).

6. ANSWERS FROM THE KEY PAGES — every value is a COPY of printed lines, never a composition
   6.0 answer.value, every solution_steps[] line and answer_as_printed are copied from the key's .tex. The
        extractor never writes a sentence of its own into an answer ("9408 is multiplied by 3; √28224 = 168"
        is a composition — Test B, Opus q61), never corrects a printed number, never completes a line. A
        printed slip is kept and FLAGGED: a final line that disagrees with the working above it (or with the
        question) → "printed result contradicts working — <what>", value kept as printed; a slip inside the
        working with a consistent final line → report-level note "key working carries a slip — <id>", nothing
        changed. source_corrections is NOT an extraction tool for keys (only for the MCQ pass-1 letter, 6.1).
   6.1 MCQ: the key prints letter + text ("B) 100"). Procedure v2 §3 applies: normalise the key TEXT and match
        it to the options — pass 1 exactly one option matches → option_id = THAT option, and when it differs
        from the printed letter a source_corrections record is MANDATORY: {field:"answer.option_id",
        printed:"<letter as printed>", corrected:"<matched id>", basis:"pass 1: key text '<text>' is option
        <id>"}; answer_as_printed = the key line verbatim. Zero matches → the printed letter is kept + flag
        "key text not among options — letter kept". Several matches → letter kept + the 1.7 several-options
        flag. (Test B ch4 q9: "(D) Rectangle" with Rectangle = option B → option b + record; not letter D with
        a mislabelled flag, and not option b silently.)
   Numeric / short: ONLY when the key's final printed line is a BARE number or quantity (§5 (2)) → {kind:"numeric",
        parts:[{id:"1", value:"<LaTeX as printed>",
        value_num:<decimal, only when the printed value is a plain integer, decimal or simple fraction — computed
        mechanically, e.g. \frac{5}{8} → 0.625; absent otherwise>, unit?}]}. A marker compares value_num when
        present and falls back to human marking when absent. Otherwise {kind:"text", value:"<LaTeX>"}.
        accepted_alternates left for review.
   Proof / show-that / explain keys: {kind:"text", value:"<the whole key, LaTeX>"}; solution_steps = its lines;
        no "final result" is picked out.
   Worked solutions: every printed line of the key's working, in order, → solution_steps[] (LaTeX lines);
        answer.value = the final printed line, VERBATIM, even when it carries a slip (then 6.0's flag). A key
        that is working only, no stated result → answer.value = the last line + report-level note "key ends
        in working — <id>".
   answer_provenance: {by:"printed", actor:"<thread>/<exact model id of the agent>", at, basis:"key printed in
        the source (LaTeX edition p<N>)"} — REQUIRED with every stored answer (1.7 rule). The model id in actor
        is what lets Test B's three units be told apart and what root-cause needs later.
   Displacement, orphan keys, inserted keys, shifted numbering: 1.7 + procedure v2 §keys apply unchanged; the
        sequence test runs on the key page's item numbers exactly as before.

7. content_hash — MATHS PROFILE (fills 1.7's stated gap; applies when text_format is latex)
   normalise(text):
     a. replace every [[aK]] placeholder by "[[" + the first 12 hex of asset aK's sha256 + "]]" (a figure is
        content; a figure-only question must not hash to the empty string);
     b. NFC (never NFKC);
     c. split into MATH segments ($…$, \[…\], \(…\), align*/equation* bodies) and TEXT segments;
     d. TEXT segments: unwrap \textbf{ } \textit{ } \emph{ } (keep the content); replace every
        \underline{\hspace{…}} by the token "_"; drop \item, \\ and environment begin/end lines of
        enumerate/itemize (the items' text stays, in order); a tabular is kept as its cell texts in row order
        joined by spaces; then lowercase; fold category-Nd digits to ASCII; remove category-P characters EXCEPT
        '.' or ',' between two digits and the "_" token; collapse whitespace to one space; strip;
     e. MATH segments: remove ALL whitespace; remove \left and \right; \dfrac and \tfrac → \frac; a
        single-character superscript or subscript loses its braces (x^{2} → x^2, a_{n} → a_n); nothing else
        is rewritten; keep case (x and X differ);
     f. join segments with a single space; SHA-256 hex.
   Consequence: `2x + 3`, `2x+3`, `x^2` and `x^{2}` agree; `\frac{1}{2}` and `1/2` do NOT (the edition writes
   \frac, so the difference is real). Computed over `text` only, as in 1.7.

7b. THE 1.7 extraction BLOCK, FILLED FOR AN EDITION
   source_file = edition.source_pdf; source_ref_prefix = "<source_pdf> ch<N>"; pdf_pages = the chapter's page
   spans {questions:[a,b], answers:[c,d], lo_table:[p]}; printed_page_offset = "per page (edition)";
   method_notes = ["read from LaTeX edition <book_id>@<tag>", …]; notation_summary = {latex_tokens:<count of
   math segments>, render_tokens:0, damage_flags:[]}; excluded_objects = []; inline_excluded_count = 0;
   the optional key fields (unnumbered_questions, orphan_keys, inserted_keys, verified_shifts) as v2 finds them.

8. WHAT STAYS EXACTLY 1.7
   id and id_regex; count_gate (reference = audited; quota_table = the chapter's EASY/AVERAGE/DIFFICULT table,
   status "difficulty_only"; second_method = the difficulty-table total); unit_states; left_unset_at_extraction;
   Stimulus; Answer kinds; Template; defect_flag_vocabulary (+ the one entry in 4); review_blocking_flags;
   status_history; source enum ('lba' | 'textbook').

9. FILECHECK — LaTeX PROFILE (code; needs Yash's go; the gate FAILS a 1.8 unit until it exists)
   For units declaring 1.8: contract map entry; text_format required = latex; edition block required with a
   40-hex commit; every text/option/answer/solution_steps line: balanced $ and { }, no \vy* macro, no
   \documentclass; each asset: file exists, sha256 equals the page json's AND the file's, figure_id matches
   pNNNN-fK; locators: derived_from latex_edition ⇒ edition_page_file present and y absent; placeholders [[aK]]
   in text ⇔ an asset aK exists; figure_id matches pNNNN-fK[a-z]?(rN)? AND equals a page-json id (2.16); no
   mojibake in any text field (2.16); only the ALLOWED CONSTRUCTS of 1.1 appear (a command outside the subset is a
   FAIL naming it); has_table true ⇔ a tabular is present; numeric.value_num, when present, is a number; the
   science FLATTENED_NOTATION heuristics OFF; a compile test of each text fragment inside a minimal document
   (xelatex, the edition's style) — optional flag, slow.

10. OPEN POINTS (decide before the pilot)
   10.1 Copy the crop into images/<chapter_id>/ (self-contained unit, duplicates ~1–3 MB per chapter) or
        reference the _figures path only (no duplication; unit not self-contained)? Draft says COPY.
   10.2 Textbook "Figure it Out" items (no printed key, no tags): same addendum, source 'textbook', answer empty
        + flag "no answer printed" unless the chapter's answers section (Class 8 tb-p1 has one) supplies it.
        Second pass, after the LBAs — not in Test B.
   10.3 The subject slug: "maths" (proposed; the syllabus map for maths must exist with chapter ids
        math-8-01 … before IMPORT; class9_chapters_v1 has maths for 9; 8 and 10 need theirs). Test B units use
        syllabus_map_version "math-8-2026-draft" and are test artefacts, never imported.
   10.4 Downstream requirement, not a contract item: the app's renderer must accept exactly the ALLOWED
        CONSTRUCTS of 1.1 (KaTeX/MathJax for math; a table renderer or the page asset for tabular). Until it
        does, maths questions display as source.
