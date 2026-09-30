EXTRACTION PROCEDURE v3 · READING A LaTeX EDITION · v1.3 · 2026-09-27
(v1.3: count gate — unkeyed reconciliation for an answer side that omits a duplicated question; gate 2.18)
(v1.2, from Test B: keys are copied lines; MCQ letter-vs-text; UTF-8; a mechanical text check against the
 edition in the self-check; item numbers without punctuation)
(v1.1: item-number sequence rule, second_method made independent, spacing/center stripping, judge note)
Companion to contract 1.8 (maths addendum). Replaces procedure v2's READING rules for LaTeX sources only; v2's
VERIFICATION rules (count gate, key pairing, sequence test, displacement, flags) apply unchanged.

1. INPUTS — what the extractor reads, and nothing else
   1.1 The edition: worktree <DEV>/wt-viyamo-staging-class-N-maths/class-N/maths/digitized/<book_id>/
       pages/pNNNN.tex + pNNNN.json, contents.json, manifest.json, at the tag named in the prompt. The .tex is
       the text of record; the .json gives pdf_page, printed_page, unclear count and the figure list (id, file,
       bbox, sha256).
   1.2 The figures: <DEV>/_figures/class-N/maths/<book_id>/pNNNN-fK.png, matched to the .json entries by sha256.
   1.3 The page IMAGE (render of the PDF page) is opened ONLY to resolve a \vyunclear{…} or a \vycont join that
       the .tex leaves ambiguous, and the reply line says so. The PDF is never read for content: if the edition
       is wrong, the unit is wrong the same way and the edition gets a correction — extraction does not fix books.
   1.4 The chapter map: contents.json entries "<n>. <title> — questions" / "— answers" give each chapter's
       first question page and first answers page; the chapter runs to the next entry's page − 1. The LO master
       table (LBA front) is read once for the LO texts; the chapter's own LO table gives the question mapping.

2. UNIT = ONE CHAPTER, ONE AGENT
   2.1 Machine name math-N-CC_questions_v1_<slug>.json (CC = chapter, two digits, LBA numbering; the LBA and
       the textbook agree on chapter numbers for Class 8 — for Classes 9/10 the prompt gives the mapping).
   2.2 One fresh agent per chapter, given: the chapter's page span (questions + answers + LO table), the
       edition paths, this procedure, contract 1.7 + 1.8, and the output path. Agents never share files.
   2.3 Order of work inside the agent: LO table → sections and questions → figures → keys → pairing → gate →
       file → self-check → reply line.

3. READING THE QUESTION PAGES
   3.1 Sections: a Roman-numbered instruction line ("I. Four alternatives are given…", "II. One mark
       questions") opens a section; s<N> is its order on the question side. Marks from the header (1.8 §5).
   3.2 Items: an item starts at a printed number ("12." or "12)") at the start of a line or \item and runs to
       the next item, the next section header, or \vypage. A candidate number is an item ONLY if it is the
       previous item's number + 1 (or a duplicate/gap the agent then flags per 1.7); a line that merely begins
       with a number ("25. Find" inside a stem that wrapped) is stem text. \setcounter{enumi}{k} on key pages
       sets the next number to k+1. Everything in the span is the question: stem,
       options, sub-parts (a), (b) …, a table, [[aK]] placeholders for figures. The difficulty/objective tag at
       the end of the stem ("\hfill \textbf{(EASY)}") is REMOVED from text and recorded per 1.8 §5.
   3.3 Options: "A) 10 \qquad B) 100 …" → options [{id:"a",text:"10"}, …]; letters lowercased in id, text kept.
       Options that are pictures (\vyfiginline in the option) → text "[[aK]]" with the asset.
   3.4 \vypage lines, running heads, the chapter banner and \vycont markers are structure, not content: \vycont
       joins the item across the page break (the item's text continues on the next page's .tex until the next
       item number); the locator points at the page where the item STARTS.
   3.5 LaTeX is copied VERBATIM inside the span (1.8 §1.1), with only these transformations: \vy* macros
       consumed; the tag removed; leading item number removed; \hfill, \quad, \qquad, \begin{center}/
       \end{center} and trailing \\ stripped (spacing is not content; the option separators become single
       spaces); \vyunclear{x} → x + flag. Never re-typeset, never "clean up" notation, never convert \frac
       to a/b, never drop a tabular.
   3.6 A question whose span holds ONLY a figure and a number (e.g. "13. [[a1]]") is a question; its text is the
       placeholder and the report-level note "question is a figure only — <id>".
   3.7 Match-the-following: the two columns become options {left:[…], right:[…]} in printed order; the key's
       pairs become answer.match.

4. READING THE KEY PAGES
   4.1 The answers section for the chapter starts at the contents entry "— answers". Keys are numbered
       (enumerate items with \setcounter, or printed numbers); the section labels on the key side are read for
       the sequence test but never trusted over the numbers (v2 rule).
   4.2 Each key's LaTeX is copied verbatim, line by line: working lines → solution_steps, the final printed line
       → answer.value (1.8 §6.0). Nothing is composed, corrected or completed; a slip is kept and flagged. For an
       MCQ the key TEXT decides the option (1.8 §6.1, v2 §3 pass 1) with a mandatory source_corrections record
       when it differs from the printed letter.
   4.3 Pairing by printed number within the chapter; the v2 sequence test decides orphan vs inserted; a
       displacement band gets the v2 treatment (empty answer + "shifted numbering — see key N").
   4.4 A key that is a figure (\vyfig in the key item) → asset role answer_diagram + text answer per 1.8 §3.

5. FIGURES
   5.1 For every [[aK]] created, copy the crop from _figures to images/<chapter_id>/<figure_id>.png; verify the
       copied file's sha256 equals the page json's; record the asset (1.8 §3). No re-cropping, no re-saving.
   5.2 A \vyfig that sits BETWEEN items (a shared figure for several questions) is a Stimulus of kind figure,
       with its asset, and each question that refers to it ("in the given figure") gets stimulus_id. Whether a
       figure is shared is decided by position (before the first item that refers to it) and wording; when in
       doubt attach it to the first following question and note it.

6. LO MAPPING
   The chapter table's "Question Numbers" cells are lists of integers (with stray trailing commas and ranges
   like "17 to 21" — expand ranges). Map every question number; a number listed nowhere → "no LO mapped";
   listed twice → both. The LO text is the row text as printed (text_as_printed). Cross-check: the union of
   all rows should equal 1…N with N the chapter's highest question number; report the difference as a
   report-level note "LO table covers <k> of <N> questions".

7. COUNT GATE (v2, restated for editions)
   reference = audited: highest printed item number − gaps + unnumbered + duplicates, per chapter.
   quota_table = the chapter's EASY/AVERAGE/DIFFICULT/TOTAL table → "difficulty_only" (the source's own claim,
   reported, never the reference). second_method = an INDEPENDENT count: the number of keys found on the answer
   side for the chapter, {method:"answer_side_keys", extracted, agrees}; it must agree with audited or the gate
   says so.
   v1.3 (2026-09-27, from Class 9 ch6 — the source prints a question twice and omits its key): when the answer
   side prints FEWER keys than the audited count, second_method may carry unkeyed:[question ids] naming the
   questions the answer side has no key for; agrees = true is accepted only when extracted + len(unkeyed) ==
   reference, every listed question carries `no answer printed` or `duplicate of …`, and any `shifted numbering`
   band in the unit has the coordinator's extraction.verified_shifts (v2 §4.3 — the thread never writes it).
   A 1.8 unit whose second_method.extracted differs from reference without an unkeyed list FAILS the gate
   (filecheck 2.18). The thread still identifies and flags; the coordinator still verifies every displaced pair.
   extracted, paired, flagged as v2. Practice/unnumbered blocks: x-segments as 1.7.

8. SELF-CHECK BEFORE THE REPLY (the agent's second pass)
   a. every item number 1…N present once (or flagged as duplicate/gap);
   b. every [[aK]] has an asset and every asset a placeholder;
   c. every text/option/answer has balanced $ and braces and no \vy macro;
   d. every question has ≥1 locator with edition_page_file; every answered question has answer_provenance;
   e. difficulty tag removed from every text (grep "(EASY)" etc. must find nothing in text);
   f. MECHANICAL TEXT CHECK, every question: for each item, take its span from the .tex, strip the tag, the
      item number, spacing commands and \vy* macros, replace figures by nothing; normalise both the span and
      the unit's text + options with the 1.8 §7 profile (filecheck.normalise18); they must be EQUAL. List every
      unequal question in the reply line with the first differing characters; zero is the expected result
      (Test B: this check would have caught "members"→"students", "findthe"→"find the", and the ₹ mojibake).
      The check compares text + options. A residual difference is REPORTED, never "fixed" by editing the unit
      to match the script: the orchestrator reads it and decides whether it is a real edit (relaunch) or an
      artefact of the check itself (e.g. `\\` inside align*, an option label) — a checker's quirk is not a
      reason to touch a question.
   g. every file read and written with encoding utf-8; grep the unit for "â" and "\ufffd" — must be absent.
   Reply line: "done ch<CC> · questions <n>/<audited> · paired <p> · flags <f> · assets <a> · unclear <u> ·
   gate PASS|FAIL · <notes>".

9. THE THREAD (orchestrator) — same shape as the science threads
   Verify the tag, run the agents (one chapter each, up to the prompt's width), run filecheck (LaTeX profile)
   on every unit, commit units + images to the class branch under class-N/maths/, tag cN-mathq-batch-NN,
   ledger entries per round, §9.5 block to the coordinator. The orchestrator never extracts a chapter itself.

9b. JUDGING NOTE (for Test B and every coordinator check)
   A unit is checked against the EDITION first (unit ↔ .tex), then the edition against the print. An error
   that is already in the .tex is an edition defect (correction commit to the book), not an extraction error,
   and is scored to neither model in Test B.

10. WHAT IS NOT DONE HERE
   Templates (1.7 Template type) — a later authoring pass from reviewed questions. Review/verification — the
   verifier thread, review method v1.4, after all classes. Textbook items — second pass (1.8 §10.2).
