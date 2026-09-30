# Port to contract 1.7 — spec v1

**What this is.** A mechanical, additive conversion of every existing unit file from contract 1.5
(Classes 6–9) or 1.6 (Class 10) to **1.7**, so that one contract, one procedure and one
verification rule govern everything. It is not a re-extraction: no page is re-read for content and
no key is re-decided. Flags change only along the enumerated mappings in
`port_mapping_1_5_to_1_7_v1` — never by a thread's judgement.

**Why now.** 1.7 currently governs no unit in existence. While that is true, every ruling has to
be qualified by which class is on which contract, and a check can be performed under a rule that
postdates the tag — which has already happened once, to `c6-sci-batch-04`. Porting removes the
condition rather than documenting around it.

**Standing constraint.** Pushed tags are never rewritten. A port produces a NEW version of each
unit file and a NEW tag. Every prior version stays reachable at its own tag, which is where the
pre-port hash lives — so no field is needed to carry it.

---

## 1. The invariant

For every question id, these are **byte-identical** to the tagged pre-port file:

    text · text_as_printed · options · answer · answer_as_printed · marks · marks_source
    difficulty · difficulty_source · difficulty_as_printed · objective · learning_outcomes
    source_flags · source_corrections · solution_steps · assets[].ref · id

The id set is identical in count and membership. **A port that changes any of the above is a
defect, not an improvement.** If a thread notices something it believes is wrong, it files an
instance in the defect register and leaves the value alone.

**One set of intended exceptions, and only this one:** the enumerated reclassifications in
`port_mapping_1_5_to_1_7_v1`, each a mechanical test with a stated condition. Hashes were a second
exception until they were checked; they are not (§4). Anything else that moves is a defect.

## 2. What is added

| field | value |
|---|---|
| `contract_version` | `"1.7"` |
| `schema_file` | `question_schema_v7_file layer with locators stimuli rubric and provenance.json` |
| `procedure_file` | `extraction_procedure_v2_how to read a source and how it is verified.md` |
| `amendments_applied` | `[]` — the 1.7 log is empty |
| `stimuli` | `[]` — verified: 0 of 49 units, 3,164 questions, detector validated on synthetic positives |
| `pending_summary` | `{}` — computed; no categories are resolved yet |
| `locators` (per question) | §3 |
| `answer_provenance` (per question) | `{by:"printed", actor:"<thread>", at:"<build ISO>", basis:"key printed in the source"}` — **only where an answer exists**, by the gate's test: `answer.value` not blank, or `option_id` not null, or `parts` / `pairs` / `sequence` / `option_ids` / `criteria` non-empty. Omitted on an empty answer. Where the stored value is the placeholder `[diagram answer — see page image]`, `basis` is **"key printed in the source as a drawing; the stored value is a placeholder, not printed text"** (ruled 2026-09-21: `by` stays `printed` because the drawing is printed; the basis must not claim the text was) |
| `assets[].pdf_page` | the page the object was taken from — the NN in the asset's name, `pNN-iK.png` (an embedded image) or `pNN-rK.png` (a region render) |
| `count_gate.duplicated_numbers` | `[]` where the source prints none |

Not added: `answer_evidence` (Mode A has none), `pending_category` (no question is waiting on a
category yet), `stimulus_id`, `retired_reason`.

## 3. The locator pass

This is the only part that needs the sources again.

Per question, a locator with `role: "question"`:

    source_ref     the QUESTION's own source_ref, verbatim — it begins with the original filename
                   (ruled 2026-09-21 at the joint review of Classes 6-8; all four ports did this)
    pdf_page       the page the stem's printed number appears on
    printed_page   pdf_page minus the unit's own printed_page_offset — EXCEPT Class 8, whose offset
                   is stored with the opposite sign: printed_page = pdf_page − 11 (mapping §6g)
    y              top of the question block, PDF points
    derived_from   "text_layer"  — verified across all five Science LBAs: 1,426–1,924 chars/page,
                   no `(cid:` tokens, PUA negligible (12 chars in class 6, 1 in class 10).
                   CAVEAT: silent glyph-dropping leaves no marker and this test cannot rule it
                   out; comparable density across all five argues against it.

**A question printed without a number** (recorded in `extraction.unnumbered_questions`, e.g. `sci-6-06-s9-q062`,
`sci-7-07-s1-q000`): `pdf_page` is the page where its stem begins and `y` is the yMin of the stem's
**first printed word** (ruled 2026-09-21). The report names each such question.

And `role: "answer"` on the same shape, **only where a key is actually printed and paired**. A
displaced, absent or unmapped key gets no answer locator. Placement (ruled 2026-09-21): at the key's printed
number; a drawn key printed above or beside its number is still located at the number; a key printed
inline with no number (e.g. an "Answer:" line under a practice question) — FUTURE extractions locate it
at the first word of that line; the 1.7 ports left these 12 (sci-7-05-x1) without one, itemised. A
printed key that pairs with no option (`key text not among options`) gets no answer locator until review
pairs it. The — record where something is printed,
never where it ought to be.

`block` is optional and is **omitted** in this port.

**Derivation, not invention.** The locator comes from re-running the same scan that found the
question at extraction. Where a question cannot be located, it is listed in the port report with
the reason and its locator omitted. An absent locator is an honest result; a wrong one is worse
than none.

## 4. Hashes — verified: NONE change

An earlier draft of this spec said some hashes would change, named `sci-6-11`, and required threads
to itemise old → new. **That was wrong, and it was wrong because a filename was read as data.**
`sci-6-11_questions_v1_phase 2 extraction with unicode numerals…` describes what was in the
*source*; the extraction resolved them and nothing survived into the file.

Checked 2026-09-21 across **all 49 units of Classes 6–9 — 3,164 questions, 83,212 strings, every
field, not only `text`**:

    detector control   ١٢٣ arabic-indic -> 3 hits · १२३ devanagari -> 3 · ೧೨೩ kannada -> 3 · 123 ascii -> 0
    result             ZERO non-ASCII category-Nd characters anywhere

1.7's digit folding therefore changes **no hash in any existing unit**.

**This makes the invariant absolute.** Every `content_hash` is byte-identical before and after;
there is no exception to itemise and no list to keep. A hash that moves during the port is a
defect, full stop — which is a simpler and stronger guarantee than the one this spec first carried.

It also removes the last tension with D18, which declined a port on rehash grounds. There is no
rehash.

## 5. What the port also closes

**Class 9's two grandfathered pilots.** `sci-9-01` and `sci-9-09` have FAILED the gate since the
day it existed. Measured under gate 2.9 on a scratch port (2026-09-21), what remains is:

| field | sci-9-01 | sci-9-09 | backfilled from |
|---|---|---|---|
| `extraction.notation_summary` | missing | missing | the counts in `method_notes` |
| `extraction.excluded_objects` | missing | missing | the counts in `method_notes` (`[]` is valid) |
| `count_gate.second_method` | missing | present | the second count `method_notes` records |
| `count_gate.quota_table` | missing | missing | **the source page** — see below |

`amendments_applied` numbering, which an earlier version of this section listed, is not a
backfill: every ported unit gets `[]` under §2, so it resolves itself.

`quota_table` is the exception to "from `method_notes`": whether the chapter prints a quota table,
and whether it agrees, is a fact about the source. It is determined exactly as the other ten Class
9 units determined theirs. If the pilots' notes already record it, use that and cite it; if not,
read the page. Any other value-producing step here is a finding, not a backfill.

**Where the values come from** (ruled 2026-09-21, Class 9 t2 Q3 — the pilots' `method_notes` hold
only glyph-restoration lines, so "from `method_notes`" above cannot be met). In this order, each value
recorded with its source and the command that produced it:

1. **the unit's own fields** — `notation_summary.render_tokens` and `latex_tokens` counted from
   the questions' `notation_source`; `damage_flags` = the number of `extraction damage` flags;
2. **a fresh mechanical measurement of the source** — `excluded_objects` from `pdfimages -list`
   over the unit's `pdf_pages`: every image object (not smask) that no asset references, as
   `{page, w, h, reason, appears_to_be}`, `appears_to_be` from looking at the render; `[]` if none.
   A missing `second_method` from an independent count of the answer side's printed key numbers;
3. **thread 1's verification v4** — as a cross-check only; any disagreement is reported, not resolved.

**Shape moves, values unchanged** (Q4, Q5): a document-level `quota_table` moves into
`count_gate.quota_table` with its value unchanged and the top-level key removed; `contract_file` is
removed (1.7 names `schema_file` and `procedure_file`); a non-standard `second_method`
(`count`, `agrees_with_reference`) is renamed to `extracted`, `agrees`, other keys kept. Each move is
listed in the changelog; the old shape stays reachable at the previous tag.
**Ten of twelve PASS becomes twelve of twelve.**

## 6. Delivery

One commit and one tag per class, continuing the existing sequence (`c9-sci-batch-05`, not a new
naming scheme). Unit `version` increments; `changelog` says *"port to contract 1.7: locators,
provenance, metadata. No content change."*

The report and the scripts the port ran go to `viyamo-record/reports/class-N/`. **The thread writes nothing to Drive**; the coordinator copies the batch there once it is verified (procedure §13).

## 7. What the thread must prove

The port report carries, per unit:

1. **id set** — count and membership identical to the tagged version
2. **invariant** — every field in §1 byte-identical; the comparison asserted, not asserted-to
3. **hashes** — every one byte-identical. No exceptions exist (§4); any change is a defect
4. **gate** — PASS under `filecheck` at 1.7, 0 fail
5. **locator coverage** — N of N questions carry a question-role locator; every gap itemised with
   its reason
6. **locator spot-check** — for **three questions per unit**, render the page at the recorded
   locator and confirm the question is printed there. The three are the first question, the last,
   and one carrying an asset or a flag; if a unit has neither, the question at position ⌈N/2⌉ in
   file order (ruled 2026-09-21; Class 8's c8-sci-batch-09 picked the next one, accepted) A locator pointing at the wrong page is a
   silent defect of exactly the kind that passes every structural check, which has now happened
   twice with flat-extracted assets

Item 6 is the one that cannot be skipped. The rest are machine checks; this one is the only
evidence that the new field means what it claims.

## 8. Order

1. **Gate learns 1.7** — gate 2.9. Every rule is keyed to the contract the unit declares, so
   1.5 and 1.6 files are checked **and sampled** exactly as gate 2.8 did. For 1.7 it adds:
   the `-q015b` suffix; `difficulty_only`; the three new flag entries and the widened
   review-blocking set; `yes_no` and `composition` answer kinds; digit folding in the hash;
   locators (conditional presence, every entry validated); `stimuli`, `stimulus_id` and orphan
   stimuli; `answer_provenance` and `answer_evidence` shapes; `pending_category` and
   `pending_summary` equal to the computed counts; `procedure_file`;
   `count_gate.duplicated_numbers` required; `assets[].pdf_page`; `retired` with a reason; and a
   flat-asset warning. Nothing can be built until this lands.
   **Proven before landing** by porting all 49 units of Classes 6–9 in a scratch copy: 47 PASS (with the mapping's §6b, now
   ratified); the remaining 2 are `sci-9-01` and `sci-9-09`, failing only on the fields §5
   tabulates. Invariant breaks: 0. Hashes changed: 0.
2. **Class 9 ports first.** Smallest available at 593 questions, and it resolves the
   grandfathering. Its addendum v2 is ratified in the same pass.
3. **Coordinator verifies the invariant** before anyone else starts.
4. **Classes 6, 7 and 8 follow** mechanically.
5. **Class 10 ports when the hold lifts.** Until then it stays at 1.6 and is the one documented
   exception.

## 9. What this does NOT do

No re-extraction. No new questions. No key changes. No figure
re-identification. No answer authoring. No addendum rewrites beyond the reading order.

**Reclassification is NOT forbidden — it is enumerated.** `port_mapping_1_5_to_1_7_v1` lists every
permitted change with its mechanical test: orphan keys re-tested against the sequence test, diagram
answers off `no answer printed`, duplicate stems with differing keys, `yes_no` typing, and two new
`quota_table` values. Nothing outside that list moves. An earlier draft of this spec said "no flag
re-classification", which would have produced 1.7 files carrying 1.5 semantics.

It also does not fix the twelve live documents that still describe retired rules — the extraction
brief, `README_v4`, the consolidation notes, the structure task and the class addenda. Those are
separate and are the coordinator's, not the threads'.

## 10. The risk worth naming

A thread with a unit file open and a pass to run will be tempted to fix something it can see.
**Don't.** The value of this port is that it is provably content-neutral; one improvement smuggled
in costs that property for every unit in the batch. File it in the register and leave it.
