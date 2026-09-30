# Port mapping — 1.5 / 1.6 → 1.7 — v1

**Why this exists.** An earlier draft of `port_to_1_7_spec_v1` said *"No flag re-classification"*. That
was wrong and would have produced 1.7 files carrying 1.5 semantics; the spec now points here instead. Contract 1.7 splits and sharpens several
things that 1.5 and 1.6 recorded under one name, so a faithful port **must** reclassify — but only
along the enumerated, mechanical mappings below, and **never by a thread's judgement.**

Anything not listed here is untouched. A case a thread believes belongs on this list but isn't
goes to the defect register and the unit ships unchanged.

---

## 0. First, a defect in 1.7 itself

1.6 defined two things in nearly the same words, and 1.7 inherited the ambiguity verbatim:

- *inserted key* — "a printed, numbered key that answers no printed question"
- *orphan key* — "a key with no printed question at all"

Both describe a key with no question. **The distinction is not usable as written.** Resolved here
and carried into the schema:

> **INSERTED** — the key is **numbered and sits inside the answer side's own sequence**, so the
> numbering after it runs ahead of the questions. It is a cause of displacement.
>
> **ORPHAN** — the key is **outside the sequence**: unnumbered, in a trailing block, or numbered
> beyond the last question. It displaces nothing.

The test is mechanical: *does the key's presence shift the number of every key after it?* Yes →
inserted. No → orphan.

## 1. Orphan keys may split

Every `extraction.orphan_keys` entry in a 1.5 or 1.6 file is re-tested against §0.

**Correction, 2026-09-21.** This section first said `sci-9-05` key 11 moves from `orphan_keys` to
`inserted_keys`. Both halves were wrong, checked against the file and the page:

- **It is not in `orphan_keys`.** `sci-9-05` carries no `orphan_keys` field; the key is recorded only
  in Class 9's report v2 and verification v4. There is nothing to reclassify.
- **It is an orphan, not inserted.** The page (pdf 78) prints `10. A. Mitochondria`, `11. Cell`,
  `12. Robert Hooke`, and key 12 still answers question 12. The key shifts nothing, so the §0 test
  says ORPHAN — Class 9's original word was right.

The port records it once, as an enumerated addition (§6d).

Across Classes 6–9 exactly one `orphan_keys` entry exists (checked 2026-09-21): `sci-7-07` key 13,
noted as "belongs by text to printed question 12". It is re-tested against §0 at Class 7's port and
the verdict reported. Class 8's thirteen units carry `orphan_keys: []`.

Every other `orphan_keys` entry across all classes is re-tested and the result reported, including
entries that stay orphans.

**`sci-7-07` key 13 — coordinator's re-test, 2026-09-21, on the page (pdf 58 questions, pdf 112 keys).**
Section I prints an unnumbered question and then 1–12; the key side prints 1–13, then 14 onward. Key 1
answers the unnumbered question (the unit's `-q000`), and key *n*+1 answers printed question *n* for
n = 1…12, so key 13 answers printed question 12 — already recorded by `sci-7-07-s1-q012`'s
`shifted numbering — see key 13`. Removing key 13 renumbers no later key (key 14 answers question 14).
**Verdict under the §0 test: ORPHAN — it stays in `orphan_keys`, unchanged.** Recorded limitation of §0:
the test was written for a key with no question; here the key has one, and the entry duplicates what the
band's flags already say. Normalising that is a review action, not a port step.

## 2. Diagram answers move off `no answer printed`

1.5 had no entry for a key that is a drawing, so threads borrowed `no answer printed`. 1.7 adds
`answer is a diagram — no key text`.

| class | questions | note |
|---|---|---|
| 6 | `sci-6-01-s8-q083`, `sci-6-01-s9-q089`, `sci-6-12-s7-q073` | `answer_diagram` asset attached; the asset is that question's own printed key (added 2026-09-21) |
| 6 — **excluded** | `sci-6-12-s6-q066`, `sci-6-12-s6-q067` | they carry `answer_diagram` assets (p92-i0, p93-i0), but those drawings are printed keys 66 and 67, which by content answer **Q69** (Big and Little Dipper, Pole star) and **Q70** (Orion) inside chapter 12's Q60–Q70 band; q066's and q067's own answers are keys 69 and 70 (text). The assets are misattached, so the test's premise fails. **Stay as they are**; in the register |
| 7 | none | |
| 8 | none | **Corrected 2026-09-21.** This row first named `sci-8-07` keys 38, 41 and `sci-8-13` keys 65, 73. Those four questions carry **no** `no answer printed` flag — they store `[diagram answer — see page image]` with an asset — so there is nothing to move. `sci-8-04-s2-q038` and `sci-8-11-s5-q081` carry the flag and a reason naming a drawing, but **no drawing is printed** for either ("printed key 38 carries Q37's answer"; "no key for the drawing exists"). The vocabulary defines the new entry as *"the key is a drawing, not missing"*; theirs is missing. **Stay `no answer printed`** |
| 9 | `sci-9-05` q029 · `sci-9-06` q032, q034 | `answer_diagram` asset attached, and it is the question's own printed key (the reason also names the diagram). Counted 2026-09-21 from the files: **three**, not the "five" this table first said |

**These are not defects and never were.** They are faithful extractions that an inaccurate flag made
look like gaps. Roughly eleven questions stop reading as missing answers.

Test (tightened 2026-09-21, checked against the vocabulary's definition *"the key is a drawing, not
missing"*): the flag is `no answer printed` **and** the unit records an `answer_diagram` asset for that
question **that is the question's own printed key**. A reason that names a drawing, with no drawing
printed, is a missing key and stays. The questions above are enumerated: a port moves exactly those and
reports any other it believes qualifies, without moving it. The earlier wording ("or the flag's reason
names a drawing") would have moved two missing keys in Class 8 and two misattached ones in Class 6.

## 3. Duplicate stems with conflicting keys

1.5's `duplicate of <id>` could say the stems matched but not that the keys differed — *"which is
the whole problem"*, as Class 9 put it. 1.7 adds `duplicate stem — keys differ`.

**Enumerated, not tested.** Exactly these, and no others:

| class | questions |
|---|---|
| 8 | `sci-8-12` q019 / q022 |
| 9 | `sci-9-06` q020 / q025 |

**Why there is no mechanical test.** This section first said: *both carry `duplicate of` and their
stored answers differ.* Run against all 49 units on 2026-09-21, that test reclassified **16
questions, of which 4 are real.** The other 12 are not conflicts:

- **stored letters vs resolved content** — `sci-7-03` q003/q024, q006/q030 and `sci-7-08`
  q001/q022, q009/q031 store an option letter on one side and text on the other, or different
  letters that resolve to the same option text. The keys agree.
- **one side empty** — `sci-6-10` q033/q050. An empty key conflicts with nothing.
- **same stem, different option sets** — `sci-7-05` q003/q018 and `sci-7-11` q019/q021. The
  stems match, the options do not, so different keys are expected.
- **same content, different form** — `sci-7-02` q079/q111: a list and a table.

Telling these apart needs reading, so it is not a port step. A thread that believes another pair
conflicts files it in the defect register and leaves the flag as it is.

**The flag names its partner.** The port writes `duplicate stem — keys differ — <partner id>`,
keeping the pointer `duplicate of <id>` carried. Ratified 2026-09-21 (schema v7 rev 3); the gate
fails the flag if the id is missing or does not share the question's content_hash.

## 4. Yes/No questions

1.5 has no `yes_no` type, so a printed Yes/No question was recorded as `vsa`. 1.7 adds it.

**Count unknown.** No class has reported one, which means either none exist or nobody was looking —
and the 1.5 contract gave no reason to look. Each thread reports the count found, **including
zero**, so silence and absence stop being indistinguishable.

Test: the printed question admits only Yes or No and the printed key is one of them. A question
merely *answerable* by yes or no is not one.

**The port COUNTS; it never retypes** (ruled 2026-09-21, Class 9 t2 Q1). Retyping moves `type` and
`answer`, both frozen by the invariant, so it is a review action, not a port step. The port report
lists each match by id, and each borderline case (key "No, …" plus an explanation) separately.
Class 9: exact sci-9-08-s2-q037, sci-9-08-s2-q041, sci-9-09-s2-q017; borderline sci-9-08-s2-q038,
sci-9-04-s2-q024.

Classes 6–8, counted by the coordinator 2026-09-21 from the files (answers opening with Yes/No) and the
text layer (headings "Yes (or) No" — one in the three books, Class 6 chapter 7 section V):
- Class 6: exact `sci-6-07-s5-q034` … `q039` (six; heading "V. Write Yes (or) No", keys Yes/NO);
  borderline `sci-6-09-s5-q046`, `sci-6-10-s3-q024`.
- Class 7: exact none; borderline `sci-7-04-s8-q073`, `sci-7-05-s7-q079`, `sci-7-06-s8-q090`,
  `sci-7-11-s6-q050`, `sci-7-11-s6-q051`, `sci-7-11-s7-q052`. (`sci-7-01-s6-q035` and
  `sci-7-02-s2-q043` keys begin "No conclusion…", "No colour…" — not Yes/No answers.)
- Class 8: exact none; borderline `sci-8-03-s3-q061` (key "No need to…"), `sci-8-04-s4-q080`,
  `sci-8-05-s3-q061`, `sci-8-07-s3-q032`, `sci-8-08-s3-q059`, `sci-8-08-s4-q067`, `sci-8-08-s4-q076`,
  `sci-8-08-s5-q079`, `sci-8-10-s4-q060`, `sci-8-11-s2-q034`, `sci-8-11-s4-q070`.

## 5. `quota_table` gains two values

1.5 allowed `consistent | inconsistent | unparsed`. 1.7 adds `absent` and `difficulty_only`.

- a table exists but could not be read → stays `unparsed`
- the source prints **no** per-chapter table → **`absent`**
- the table has a difficulty axis and no per-section row → **`difficulty_only`**

Class 10 reported being forced to assert `inconsistent` and `consistent` where neither was true.

**Classes 6 and 7 — `unparsed` → `absent`, all 24 units** (coordinator, 2026-09-21, text layer read
page by page). Neither LBA prints a per-chapter table. Class 6 prints one document-level blueprint
(pdf 7: weightage to objectives, question types, difficulty, content, in percent and marks); Class 7
prints one document-level blueprint (pdf 16–17: the same, plus chapter-wise marks). Neither has a
chapter's per-section counts, which is what `quota_table` describes. Class 8's values: §6f.

## 6. Fills, not reclassifications — safe and mechanical

| field | 1.5 state | 1.7 |
|---|---|---|
| `marks_source` | absent | **stays absent** unless the unit ITSELF already records where its marks came from (ruled 2026-09-21, Class 9 t2 Q2: filling it is a claim about the source, and the invariant freezes the field). Report the count left absent |
| `count_gate.duplicated_numbers` | not a field | `[]` where the source prints none |
| `count_gate` identity | `audited = highest − gaps` | `+ unnumbered + duplicated` — the **identity** changes, the **value** must not |
| `extraction.notation_summary`, `excluded_objects` | absent on grandfathered units | backfilled from `method_notes` |

If the count-gate value changes under the new identity, that is a **defect, not a port** — stop and
report it.

## 6b. A displaced match key drops its pair-form flag — ratified 2026-09-21

1.6-a2: a match question whose key is displaced or unprinted carries only its defect flag, not
`match key not in pair form` as well. 1.7 carries the rule. Two 1.5 units carry both flags and
fail the 1.7 gate: `sci-6-03-s3-q035`, `sci-6-12-s3-q031` (the id first printed here as `-s2-q031` was a
typo; corrected 2026-09-21 from the file).

Test: type `match`, answer kind `text`, and a `shifted numbering`, `displacement boundary` or
`no answer printed` flag present → remove `match key not in pair form`. Nothing else moves.

## 6c. One coordinator-verified shift added during the port — sci-9-04

One entry, and only this one, is appended to `sci-9-04`'s `extraction.verified_shifts` during the
port, copied **verbatim**:

    {"questions": [55, 65], "pointer_rule": "restart: Q(54+k) <- key k, k = 1..11 — the answer side restarts at 1 after key 54", "verified_by": "coordinator", "at": "2026-09-21T11:17+05:30", "verified_sample": [55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65], "method": "text layer of 9th-Science-EM-LBA-Revised_1787227484.pdf, answer side pdf 100-102; each of the 11 stems compared with its key by content"}

It records the coordinator's own verification, which is what the field is for (procedure §4.3);
the thread copies it and decides nothing. All eleven matched by content: q055 ↔ key 1 (hydrogen
isotopes table) through q065 ↔ key 11 (bromine), across the answer side's "V." heading before key 7.

**Nothing else on q055–q065 moves** — answers stay empty, flags stay as they are. Resolving the
shift is a review action, and the resolved keys then follow procedure §4.3: q055 and q063 are
tables, q062 is a drawing, and q058, q064 and q065 lose fractions from the text layer.

## 6d. One orphan key recorded during the port — sci-9-05

`sci-9-05`'s `extraction.orphan_keys` is created with exactly this entry, copied **verbatim**
(1.6 shape: key_number, text_as_printed, note):

    {"key_number": 11, "text_as_printed": "Cell", "note": "pdf 78: printed between key 10 and key 12; question 11 is never printed; keys either side align with their questions, so the key displaces nothing (sequence test: orphan). Recorded at the port from Class 9 report v2 and verification v4; coordinator-checked on the page 2026-09-21."}

Nothing else in `sci-9-05` moves; `count_gate` is untouched.

## 6e. Four quota_table values corrected during the port — sci-9-05, 06, 08, 11

Contract 1.5 defines `consistent` as: the table's rows sum to its totals AND its per-type counts equal
the sections the page prints. Checked by the coordinator on the source, 2026-09-21, every row and
column of all 24 Class 9 quota tables, and each table's per-type counts against the unit's sections.
Four units say `consistent` and are not:

| unit | table (pdf page) | what the page prints |
|---|---|---|
| `sci-9-05` | both (24) | the tables add up, but promise 9 Very Short Answer questions and the page prints 8 — question 11 is never printed (the §6d orphan key). The second clause fails |
| `sci-9-06` | difficulty (28) | columns sum to 8 / 17 / 10, printed 11 / 15 / 11 — the printed column totals add to 37 against a grand total of 35 |
| `sci-9-08` | difficulty (36) | Very Short Answer row 05 + 08 + 03 = 16, printed 17; the Average column sums to 34, printed 35 |
| `sci-9-11` | objectives (62) | Long Answer (4m) row 03 + 01 = 4, printed 03; the Understanding column sums to 19, printed 18 |

In each of the four, `count_gate.quota_table` becomes **`inconsistent`**. Nothing else moves; the count-gate
reference is the audited count and never depended on these tables. `sci-9-09` was already
`inconsistent` and stays so.

This corrects thread 1's verification v4 §4, which withdrew an earlier "rows disagree" claim for
all chapters — rightly for 7 and 10, wrongly for 6, 8 and 11 — and applied only the first clause to
chapter 5. It matters beyond the label: `consistent` is what licenses the Subject Map to use a table's
Easy / Average / Difficult split, and chapter 6's printed split adds to 37 for 35 questions.

## 6f. Class 8 quota_table — two values corrected, four confirmed

Checked by the coordinator 2026-09-21 against the definition in §6e: every row and every column of both
tables in all thirteen chapters (26 tables, pdf 12, 15, 22, 28, 40, 47, 50, 57, 64, 69, 79, 88, 93), and each
table's per-type counts against the unit's sections.

| unit | stored | verdict | reason |
|---|---|---|---|
| `sci-8-09` | inconsistent | **consistent** | both tables (pdf 64) add up in every row and column; per-type 23/17/10/7/3/2 = the sections |
| `sci-8-13` | inconsistent | **consistent** | both tables (pdf 93) add up; per-type 15/23/15/16/10/5 = the sections |
| `sci-8-04` | inconsistent | inconsistent — **unchanged** | both tables add up and the counts match by position, but the difficulty table labels its last two rows "Long Answer (2m)" and "Long answer (3m)" where the page prints 4-mark and 5-mark sections (the objectives table labels them correctly). Per-type identity fails on the label; the stored value stands. **This is the coordinator's judgement, not a mechanical result:** the definition compares counts with sections and does not say whether a row's printed label is part of its type. Read by position, the table is consistent. Kept `inconsistent` because the port changes a value only where the definition is unambiguous |
| `sci-8-08` | inconsistent | inconsistent | per-type 20/20/18/7/12/9 against sections 20/20/19/18/7/2 |
| `sci-8-10` | inconsistent | inconsistent | per-type 29/15/13/3/2 against sections 29/13/15/3/2 (the 1-mark and 2-mark rows swap) |
| `sci-8-11` | inconsistent | inconsistent | per-type 27/21/15/17/5/14 against sections 27/21/15/17/17/2 |

The seven units stored `consistent` (01, 02, 03, 05, 06, 07, 12) are confirmed.

**Why 09 and 13 were marked inconsistent.** In every Class 8 unit, `inconsistent` coincides with the
table's Easy/Average/Difficult split disagreeing with the per-question difficulty tags (09: table
22/22/18, tags 20/19/23; 13: table 17/41/26, tags 16/43/25), and `consistent` with agreement. That is a
different test from the contract's. It is still a fact worth keeping: for 09 and 13, a Subject Map using
the table's split would disagree with the tags printed on the questions.

## 6g. Class 8 printed_page — the offset's sign

Spec §3 computes `printed_page = pdf_page − printed_page_offset`, which is Class 9's convention (offset
13, printed = pdf − 13). Class 8 stores `extraction.printed_page_offset: -11` in all thirteen units, in the
other convention: its addendum says "LBA printed = PDF − 11", confirmed by the coordinator on the page
2026-09-21 (pdf 20 → 9, pdf 101 → 90, pdf 150 → 139). **For Class 8, `printed_page = pdf_page − 11`.** The
stored offset is **not** changed by the port — it is outside this list; normalising the sign is recorded
here and done at import. Classes 6 and 7 store 0 and print folio = PDF page; no issue. **Class 10** (on hold) stores the field as a
STRING, "PDF page = printed folio + 14" (checked in both pilot units, 2026-09-21) — a third form. Its port must
derive `printed_page` from the page and state its formula, never compute it from the stored field.
(Correction, same day: this note first said Class 10 used the minus convention, reading procedure §12's
"−14 / −16", which are textbook offsets, as Class 10's LBA field.)

**Unflagged drawing keys.** 12 questions store `[diagram answer — see page image]` with an `answer_diagram`
asset and no flag: `sci-6-02-s6-q037`, `q038`, `sci-6-04-s6-q061`, `sci-6-09-s5-q047`, `sci-8-02-s3-q038`,
`q042`, `sci-8-07-s4-q038`, `q041`, `sci-8-08-s3-q049`, `sci-8-11-s3-q049`, `sci-8-13-s4-q065`, `s5-q073`.
1.7's form is an empty answer plus `answer is a diagram — no key text`. Converting them moves `answer`,
which the invariant freezes, so the port does NOT; they are in the register (answer-is-a-diagram) and
converted at review. Until then the bank holds three forms of one fact — flag + empty answer, placeholder
text, and Class 9's two junk values (sci-9-05 q039, q040) — and import must treat all three as "the key
is a drawing".

## 7. What is NOT mapped

`prior_appearances`, `unmapped_key_blocks`, the `-q015b` suffix and `learning_outcomes` rows with an
empty number are 1.6/1.7 constructs that only Class 10 has hit. Classes 6–9 carry none and none are
synthesised.

## 8. What the port report must carry, per class

1. every `orphan_keys` entry, re-tested, with its verdict — including unchanged ones
2. every question moved to `answer is a diagram — no key text`, by id
3. confirmation that only the §3 enumerated questions moved to `duplicate stem — keys differ — <id>`
4a. every `match key not in pair form` dropped under §6b, by id
4b. the §6c and §6d entries, each confirmed byte-identical to this document
4c. the §6e (Class 9) and §6f (Class 8) quota_table values, and §5's `absent` for Classes 6 and 7
4. **the `yes_no` count, including zero**
5. every `quota_table` value changed, with the old value and the reason
6. confirmation that no `count_gate` value moved under the new identity

Everything on this list is a **mechanical test with a stated condition.** A thread that finds itself
deciding has found a case this document does not cover — which is a finding, not a licence.
