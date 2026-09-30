# Extraction procedure — v2

**Layer: PROCEDURE.** How to read a source, and how what comes out of it is verified. Companion
to `question_schema_v7` (the FILE layer) and `runtime_schema_v1` (the RUNTIME layer).

Supersedes procedure v1 (staged, never in force) and the `rules` block of `question_schema_v6`,
except the clauses that moved to the file layer (id, content_hash, count_gate, unit_states,
left_unset_at_extraction). **v2 adds section 14 (verification), retires the crop pipeline and the
clean-counter regime, and states the hard-link rule.**

This is where per-source irregularity lives. **Facts about one book belong in that class's
addendum, not here.** A rule reaches this document only when it holds across sources — and reaches
the *schema* only when it changes a stored field, what the generator emits, or what a teacher
sees. That test is why these three documents are separate: forty-plus amendment entries were
written in three days and almost all of them were procedure, written into the schema.

---

## 1. Correction

A correction is applied **only** where the printed material contradicts itself and the resolution
is fixed by the document's own content or by arithmetic. Anything needing subject knowledge —
including spelling — is flagged, never corrected. Every correction keeps the printed original and
a basis in `source_corrections[]`.

No manual edits to generated outputs. Where a generator's result looks wrong on subject grounds,
the remedy is a flag.

## 2. Section, where the question side omits it

Take it from the answer side only if it agrees with ONE independent signal, in order: (a) the
quota table's per-section counts, where parseable and consistent; (b) the key-form transition on
the answer side; (c) monotonic numbering with the answer side's own marks labels. Record
`section_source: 'answer_side'`, the `section_signal`, and the counts compared. No signal agrees →
the chapter is STOPPED, section structure unresolvable.

Answer-side headings are never used for marks or type.

**Match a section heading with or without trailing punctuation.** A heading printed as bare `III`
is still a heading; requiring `III.` or `III)` silently understated the section count in four
chapters of one source and, because the section index feeds the `-sN-` id segment, blocked a
chapter outright.

## 3. Key-to-option matching

**Options exist only where the question is an MCQ** (or `mcq_multi`, or a `match` list). In a short,
long or HOT answer, lettered lines — "A. Centriole  B. Mitochondria", "A. Convert 54 km/hr… B. Change
6 m/s… C. A driver…" — are a list of labels or the question's own sub-parts, and they stay in `text`.
Letter markers are read as options only after the section's type is known. (Class 9: four long
answers stored parts or label lists as options — sci-9-05 q039, q040, q041, sci-9-07 q037.)

Two passes over the normalised strings. **Pass 1**: exactly one option matches → apply as a
`source_correction` (basis 'pass 1'); several → flag with `suggested`. **Pass 2**, only if pass 1
yields zero: strip ALL whitespace; exactly one match → apply (basis 'pass 2'); zero or several →
flag with `suggested`. Never the closest option.

## 4. The answer side

1. Pairing is by the answer section's own printed number, never by position. Never shift-align.
2. A question whose key is displaced carries an EMPTY answer and `shifted numbering — see key N`,
   pointer in `suggested`.
3. **The offset loop (Yash, 2026-09-21).** The thread IDENTIFIES the offset — every displaced question
   flagged, the pointer rule stated — and COMMUNICATES it (report + ledger). The coordinator VERIFIES
   **every pair in the run, by content, not a sample** (`verified_sample` = every question in
   `questions`), and COMMUNICATES the verdict back in the thread's ledger, naming each pair. Only then is
   the run accepted. Sampled entries written before this rule (4 of 11, 2 of 4, 2 of 6, 4 of 9, 0 of 16)
   were re-verified in full on 2026-09-21 — one sampled entry had hidden an error (sci-6-12 Q69/Q70).
   A run verified end to end by the coordinator goes in `extraction.verified_shifts` and may be
   resolved by the reviewer in one action. **The thread never writes `verified_shifts`** — that
   field records the coordinator's verification, not the thread's. A key attached by resolving a
   shift is stored in the shape extraction requires for that key, exactly as if it had been
   paired at extraction: a printed table as one step per printed row (§7), a drawing as
   `answer is a diagram — no key text` (item 7), notation lost from the text layer flagged as
   extraction damage. (Class 9 freeze note 7c, 2026-09-21.)
4. The BOUNDARY of a band takes `displacement boundary — see key N`, may keep the by-number key,
   and is a content judgement for the reviewer.
5. **INSERTED vs ORPHAN — the sequence test.** A key with no printed question is INSERTED
   (`extraction.inserted_keys`) when it is numbered and sits inside the answer side's own
   sequence, so every key after it runs ahead of its question; it is a cause of displacement.
   It is an ORPHAN (`extraction.orphan_keys`) when it sits outside the sequence — unnumbered,
   in a trailing block, or numbered past the last question — and displaces nothing.
   The test is mechanical: *does this key shift the number of every key after it?*
   (1.6 defined both in nearly the same words, which was not usable; this replaces it.)
6. A truncated answer side's unnumbered tail goes verbatim in `extraction.unmapped_key_blocks`.
   Nothing in such a block is ever paired at extraction.
7. A question with no key anywhere: empty answer + `no answer printed`. **A key that is a drawing
   is not a missing key** — `answer is a diagram — no key text`, plus an `answer_diagram` asset.
   Text found beside a drawn key — a stray full stop, the page folio, a callout letter — is residue,
   never the answer: the answer stays empty. (Class 9 sci-9-05 q039/q040 stored "." and "66", the
   folio of pdf 79.)

8. A key whose text addresses a different printed question: `key text does not address question`.
9. **A key count equal to the question count is NOT evidence of alignment.** Keys are read against
   stems at build time and displacement is reported per unit.
10. **Check for duplicated question numbers before mapping any band.** A duplicate is invisible to
    a count check whenever a gap offsets it, and an answer side numbering continuously across one
    runs +1 ahead from that point — which reads exactly like an inserted key.

**Band shapes:** `offset` (with a pointer rule), `rotation`, `transposition`, `reorder`,
`staircase` (repeated offset changes, ONE entry with steps), and a section-wide
`numbering_restart` — which is not a band, and was raised as a gap by a thread forced to express
one restart as eleven individual flags.

**Keys are extracted exactly as printed (Yash, 2026-09-21).** A key printed as a bare "Yes" / "No" (or
"True", a single word, a number) is stored bare. Non-MCQ answers become full sentences ("No, plants do not
…") only when the answers are BUILT at authoring — the "why" part is written then, never at extraction.

## 5. Marks

`marks_source` is one of: `section_header` (the default), `unit_table`, `blueprint_table`,
`same_form_elsewhere` (one counter-example voids it), `section_table`, `subpart_sum`,
`unassigned`. A header printing alternatives, nothing usable, or no figure and no readable type →
marks null, `unassigned`, flag `marks ambiguous in source — <printed>`. Marks are never inferred
from position and stay review-editable.

**Marks the source does not give (Yash, 2026-09-21).** Extraction still records null + `unassigned`;
marks are ASSIGNED later (review / authoring), never at extraction, by this general rule on the expected
answer: one word, one line or one sentence → 1; two to three specific points → 2; four to five points →
3; six or more points → 4. **Refinement from the Karnataka SSLC keys (approved by Yash, 2026-09-21):** count a
FULL point (a definition, law, full-sentence reason, difference pair, equation, formula, event) as 1 and a
PHRASE point (a short item in a list, a calculation step, a diagram label) as ½; the sum is the mark. Fixed
shapes keep the board's value whatever their length: MCQ 1 · map place 1 · diagram drawing 1-3 plus ½ per
label · genetics checkerboard 2 · theorem opening block (figure, given, to prove, construction) 2 · theorem
statement 1 · graph 4 · reported speech 2 · two-output grammar transformation 2 · comprehension
sub-question 2 · essay or letter 5. Five marks only for a multi-part answer, a map, or a 10-point list. The
LBA's printed marks always win. No board evidence exists for maths constructions — they are marked by
review, not by this rule. Evidence and citations: viyamo-record reports/coordinator/marks_research/.

## 6. Difficulty, objective, learning outcomes

Difficulty from the source's per-question tag, normalised. Section-level tag only → inherit with
`difficulty_source: 'section_header'`. No tag → null + `no difficulty tag`; difficulty is authored
at review, and the **count of untagged questions is reported per unit** so the authoring load is
visible before the pass is scheduled — one class carries 166.

**Authoring an untagged difficulty (Yash, 2026-09-21).** The LBA's printed tag always wins. Where the
LBA prints none, extraction stores null (never a code such as -1) + `no difficulty tag`, and the value is
authored later, during the TEXTBOOK pass, because it needs the textbook:
- **difficult** — the answer is derived: not found as such in the textbook's paragraphs (whether or not
  the question is in the exercise section);
- **easy** — the answer is a direct copy of a line, sentence or paragraph of the main text, OR the question
  matches a question in the unit's exercise section;
- **average** — the answer is a direct copy from a notes / observation / activity box, or the question does
  not match an exercise question.
Precedence when rules conflict: difficult > easy > average. (Yash's words easy / medium / hard map to the
schema's easy / average / difficult.)

**Tags are printed untidily.** Accept a space inside the brackets (`(Easy )`, `( Easy)`), a closing
bracket that is missing or wrapped to the next line (`…homeostasis.(Difficult`), and any letter case.
**After extraction no tag text may remain** in `text` or in any option: a leftover tag is a defect
whether or not `difficulty` was set. A question whose tag could not be read is NOT `no difficulty tag`
— that flag asserts the book prints none; report it as unread (section 16). (Class 9: eleven questions
kept their tag in the text and were recorded as untagged; two more kept it with difficulty set.)

A tag glued to the stem's last word is separated by **x-coordinate**, never a layout regex. A
chapter may be PARTIALLY tagged: a run that starts and stops is neither tagged nor untagged, and
calling ten right-margin letters noise was a real step-1 error.

**A difficulty tag printed on a section HEADING (coordinator ruling, 2026-09-22; Class 10 ch 2 III, ch 3 II).**
A question's own printed tag always wins. Every question in that section WITHOUT its own tag inherits the
heading's tag with `difficulty_source: 'section_header'` and `difficulty_as_printed` = the heading's tag
text; the section is listed in `section_uniform_difficulty`. The tag text is removed from the heading text
like any other tag. A question with neither its own tag nor a tagged heading is `no difficulty tag`.

Objective normalised to knowledge | understanding | application | skill.

Learning outcomes: per-question LO tables assign every question in a stated range; printed numbers
win over ranges; a question outside every row → `[]` + `no LO mapped`, exempt from the `suggested`
expectation, because naming an LO the source does not name is authoring. An LO row printed
**without a number** takes an empty `number` — the shape did not anticipate it.

## 7. Steps and notation

`solution_steps` split at PRINTED LINE BREAKS: a new text line whose left edge returns to the
block's left margin, or a new table row. An enumerator splits only at the start of a printed line.
A BORDERED table is read with ruled-table extraction — one step per printed row, cells joined
` | `, header row first.

**This rule does something actively wrong to verse.** A poem's line breaks are content; a poem
extract is a `Stimulus`, not `solution_steps`, and is preserved exactly.

Notation: sub/superscripts and units preserved. Text-layer restoration is **per glyph** — a token
is restored only if every small glyph in it was measured; otherwise left as printed and flagged
`extraction damage`. Image-embedded notation may be transcribed from a render with every token
listed under `notation_source.render`; a token the operator hesitates on is flagged, never
guessed. LaTeX residue is transcribed to plain notation.

Multi-line algebra and matrices are **not** covered by the line-break rule. A maths profile is
required before that pilot.

## 8. Figures

An embedded object is NOTATION, never an asset, when: (a) long side under 100 px; (b) inline — its
box substantially overlaps a text-line band and its height is at most 2× that line's; (c) displayed
equation — height at most 2× body line height AND aspect above 3:1.

Everything else is a FIGURE: the asset at native size, per question, `quality: 'low'` below the
floor (long ≥ 600 AND short ≥ 150 px). Objects excluded under (a) or (c) appear on the figure
sheet's thumbnail strip, each labelled with what it appears to be — the label describes, the
coordinator decides rescue. A subject addendum may declare a lower floor with its reason, or
decline to, with its reason.

A whole-page render at 200 dpi (`role: 'page'`, caption "crop pending") only where a figure is
printed as vector or inline scan with no extractable object. **A narrower region render is
permitted** where the region is identifiable, with the role naming what it is and the method
recorded.

A stem referencing a figure the source never printed takes the report note
`figure referenced but not printed — <question id>`.

**Check every asset for flat extraction.** An object whose extracted pixels are a single colour is
a stencil mask whose shape lives in a separate smask; re-render it from the page region. This has
occurred in two independent sources, and *a silent black asset passes every structural check*.

**Figure sheets survive** — one composite per figure-bearing unit, confirmed by the coordinator
before FIGURED. A sheet shows extracted objects, which page rendering does not replace.

## 9. Duplicates

Identical `content_hash` within one source: retain both, flag both `duplicate of <id>`. Where the
stems match but the KEYS DIFFER, the flag is `duplicate stem — keys differ` — the case that
actually needs a reviewer, and which `duplicate of` could not express.

## 10. Sources

Never rename a source file; the filename as downloaded is the provenance key and every
`source_ref` cites it verbatim. Two files are the same document only when their SHA-256 match —
never by size or name. A `_sources_index_v<N>` lists subject, class, year, DIET, printed title,
filename, size, SHA-256, status, and any labelling defect.

Threads may write into the source tree ONLY the sources index and `<class>\split\<subject>\`.

`board_qb` is identified by its own cover, not by a filename. **A board Question Bank may be a
genuinely different document from the LBA for the same chapter** — where both exist and disagree,
that is not a defect to reconcile at extraction; both are recorded and the reviewer rules.

## 11. Cleaning

Strip the watermark, headers, footers and page numbers — a bare number line is a page folio only
where the offset says so; it may be a key. Rejoin line-wrapped words. **Never fix source errors
silently.**

## 12. Page offsets

Derived **per volume and per part**, from that volume's own contents page, confirmed against a
printed folio glyph on at least two pages. **Never carried from another class.** One book's −14 and
another's −16 are each correct for their own volume, and one was copied into the other's task file
and had to be caught by a thread.

Report how many page-numbering systems a volume prints. Several print two; one prints three.

## 13. Staging, identity, and send

**Threads work only in the Devs folder and in git. They never read from or write to Google Drive**
(Yash, 2026-09-21). The rules they follow are in `viyamo-tools/contracts/`, read from the shared
Devs clone; their sources and book notes are in `Devs/_reference/class-N/`; their unit files,
sheets and images are in their own worktree; their ledger, register rows, reports and working
scripts are in `viyamo-record`. **The coordinator alone writes to Drive, and only frozen
material** — a tagged batch that has passed verification, a contract version, a closed report.
Nothing enters `class-N\` on Drive without Yash's send order.

Threads work on their own branch and worktree and commit from there. A batch is one commit and
one tag `c<class>-<subj>-batch-<NN>`. **Pushed tags and branches are never rewritten.**

**Delete permission.** Git removes temporary and lock files on every commit, and `git rm` removes
files; in a connected folder both fail until deletion is allowed. A thread asks for delete
permission on the Devs folder once, before its first git write. Without it a commit can fail
half-way and leave lock files that block every thread sharing the repo.

**The hard-link rule (coordinator).** A file created inside the Google Drive mirror is hard-linked
on creation and the bridge refuses to read it. Material is built outside the mirror and copied in.

**Set git identity per commit:** `git -c user.name=Claude -c user.email=noreply@anthropic.com
commit --author="<actor> <<actor>@viyamo.local>"`. Never `git config`, which in a worktree writes
to the shared clone and lets threads overwrite each other's identity.

**Strip the token from `.git/config` immediately after cloning:**
`git remote set-url origin https://github.com/…`. Two clones have carried write tokens in
plaintext on disk.

**Image identity is by pixel hash, not file hash** — Drive re-encodes PNGs.

**Workflow tooling follows the workflow (Yash, 2026-09-21).** `viyamo-tools/src/status.py` and `record.py`
generate STATUS and the ledger index from the record. Any change to the workflow — a new ledger kind, a
new verdict, a new register column, a new required step — updates these two IN THE SAME CHANGE, or the
change is incomplete.

## 14. Verification

**The structural gate** (`viyamo-tools/src/filecheck.py`) runs on every unit, every build, by the
thread before tagging and independently by the coordinator on fetch. It is free, so it is never
sampled.

**The content sample.** The coordinator **renders source pages on demand** and compares the stored
JSON against what is printed. Threads ship **no crops**. Ids are chosen **after** the pages are
read, which the thread cannot anticipate — a stronger guarantee than the old seeded selection,
where the thread cut the very crops it would be judged on.

At least five questions per unit **new or changed in the tag**: three unflagged spanning distinct
types, one flagged, one figure-bearing (a fourth unflagged where the unit has no figure). **Always add
every question of a risky shape**: sub-parts, a list of labels, a drawn key, a table in the stem or the
key — these are where readers fail silently. The read compares EVERY stored field with the page — text,
options, answer, difficulty — not only where the question is printed.

**A port is content-sampled too.** A port proves nothing changed; it does not prove the extraction was
right. Until a unit has had a content sample, its record says so. (Class 9's first content read, during
its port, found more than a dozen defects in units that had passed every gate since batch-04.)

**Check a claim against its definition.** Before verifying a statement ("the table is consistent",
"the source prints no tag"), read what the term means in the contract, and check THAT — not the numbers
that happen to sit beside it. (2026-09-21: addendum v2 was ratified after its grand totals were
checked; `consistent` also requires every row and column to add up, and four chapters did not.) More
where the unit warrants it. Unflagged questions carry the weight because systematic defects hide
there — a silently dropped option is not flagged.

**The full answer-to-question read — REQUIRED before delivery (Yash, 2026-09-21).** Every structural
check and the content sample can pass while a stored answer answers a different question: they check
where things are printed and that stored words appear on the page, never that the ANSWER fits the
QUESTION. The Classes 6-9 read (reports/coordinator/full_read_2026-09-21.md) found 13 printed keys that
answer another question and 43 page folios inside stored text — all past every earlier check.

1. **Export** every question of the tag with an answer: id, type, full stem, options, stored answer (for an
   mcq the option letter AND its text), flags. **No truncation** — the first read cut long items at 500-600
   characters, and a long answer can hide a merged neighbour.
2. **Plant the control.** Before any reader starts, the thread swaps the answers of at least 2 adjacent
   pairs per ~400 questions in a COPY of the export: at least one short-answer pair and, where the tag has
   them, one mcq pair with similar options (the harder case the first read did not test). Record the plants
   in a file written before reading. Readers are not told.
3. **Read** with independent reader agents, one per ~400 entries, each told to read EVERY entry and report
   OFFSET / WRONG / MISMATCH / CONTAMINATED / UNSURE, never silently passing a doubt.
4. **Score the control.** Every plant must be reported. A missed plant voids that reader's file: re-read
   it with a fresh reader. Report the score.
5. **Check every OFFSET and MISMATCH on the page** at the question's answer locator. Printed that way →
   the book's defect: flag `key text does not address question`, keep the printed key (§4.1: never re-pair
   by content), register row `key-answers-another-question`. Not printed that way → an extraction offset:
   STOP, re-derive the pairing, and the offset loop (§4.3) applies.
6. **Folio scan** — `python3 viyamo-tools/src/folio_scan.py --pdf <LBA> --out <report> --renders <dir> <units>`.
   A 2-3 digit number in stored text equal to the printed page ±1 of the question's locators is looked up on
   the page: printed only in the header/footer band → FOLIO (file it, `folio-in-stored-text`); printed in the
   body beside the same neighbouring word → CONTENT; anything else → UNCLEAR, rendered with every
   occurrence boxed (red = margin, blue = body) for a person to decide. The report and any renders go
   with the delivery. (Yash, 2026-09-21: renders for the doubtful cases.)
7. **WRONG / UNSURE** findings go to the report as a review list, marked unverified. They are opinions
   about science, not defects of the extraction, until review decides.

The coordinator re-checks every step-5 candidate and the control score at verification. A tag without
this read is `PASS (partial)` at best.

**Category questions are not sampled.** A question carrying `pending_category` is handled through
its category (section 15): the coordinator reads enough members to fix the category's shape, rules
once, and the ruling applies in bulk to every question carrying that id. A two-hundred-member
category costs a handful of reads, not two hundred.

**Verdicts.** `CHECKED` — every sampled id read JSON ↔ page, and every figure sheet in the tag
confirmed. `PASS (partial n/m)` — anything less, with the unread ids named; the tag stays in the
queue. `CHECKED (structural, no content sample — fix-only)` — a tag changing no question content,
only flags, metadata or assets; it takes the gate plus a read of the diff, and this is a complete
verdict, not a partial. A verdict covers exactly what its record lists.

**Which procedure governs a check.** Verification is performed under the procedure **in force at
check time**, not the one in force when the tag was cut — verification is a property of the checking,
not of the file. The check record names the procedure version used. Without this stated, a tag can be
checked against a rule that postdates it, which is exactly what happened to `c6-sci-batch-04`: tagged
03:54, the sample rule changed 05:09, the record written 05:32 citing the new rule against evidence
cut under the old one.

While files on 1.5 or 1.6 still exist, they are checked under THIS procedure, and the record says so.

**There is no reduced-check regime.** The four-consecutive-clean-units rule in contracts 1.5 and
1.6 is retired. It existed to make checking cheaper when checking was expensive; rendering a page
now takes about a second. It also never once fired, its statistics assumed defects are independent
when they are clustered by source, and its counter reset when a thread disclosed its own defect
after tagging — taxing the single most valuable behaviour these threads have.

What replaces it is measurement, not a gate: the ledger's effectiveness section tracks defect
recurrence per thread per category over time. If coordinator throughput ever binds, sampling rates
are set from that data.

**`viyamo-renders` is retired.** Existing crops stay as historical evidence of checks already
performed. Nothing new is committed to it.

## 15. Defects go to the register, not to an amendment

A defect is filed as an instance against a category in `viyamo-record/defects/`. Filing is cheap,
needs no ruling, and **blocks nothing**: the question is flagged, tagged with `pending_category`,
and extraction continues.

A category becomes an amendment only at **2+ independent sources AND ≥10 linked instances**, or
when it blocks builds in 2+ classes. It escalates regardless of count at 3+ classes, 14 days open,
or >5% of a unit's questions — the last meaning it is structural for that book and the ADDENDUM
must act even though the contract will not.

The threshold governs source-defect-driven amendments. It does not govern deliberate design
changes.

## 16. Reporting

One fenced code block per report, fixed sections: STATUS · 1 DONE · 2 GATES AND UNIT STATES ·
3 DEVIATIONS (including corrections to your own earlier reporting) · 4 FINDINGS · 5 DECISIONS
NEEDED · 6 INFO NEEDED · 7 RISKS / PUSHBACK · 8 PENDING SEND · 9 NEXT · FILES PRODUCED.

**A failed read is not a fact about the book.** When a reader does not find a tag, a heading, a table
or a key, record it as UNREAD and report it — never write "the source prints none" or "not parsed" as
if it were a property of the source. Three Class 9 claims made that way were wrong: "two quota
vocabularies" (it prints five), "chapters 8, 11 and 12 not parsed", and "chapter 5 q031, q039, q040
carry no tag". Absence is a claim like any other and needs the negative-result control (section 17).

**A report is not delivered until it is a file.** Chat is a notification, not a record. One thread
reported six batches in chat, wrote none of them, and its context was later compacted.

Every ledger entry carries `cost` and, when known, `outcome`.

## 17. The second pass

**Every report gets two passes.** Produce it, critically analyse your own output, correct what the
analysis finds, and deliver the corrected version. A first draft is not a deliverable.

The second pass asks, of every load-bearing claim: **did I verify this in this pass, or am I
recalling it?** Anything unverified is either checked before sending or marked unverified in the
report. This is the `[derived]` / `[stated]` distinction the ledgers already require — turned on
the report itself.

**Reporting an absence.** "None found", "no defects", "zero" is reported only with:

- the **universe** — how many candidates were examined
- evidence the **detector works** — a positive case it caught, synthetic if the corpus has none

An unvalidated detector returning zero is not a result: a broken instrument and a true absence look
identical from the output. *"0 of 28 checked, the test flags a known positive"* is a finding.
*"None"* is a silence.

And a verified absence still has several possible causes. **Choosing one is a second inference that
needs its own evidence.** A report that was verified missing was attributed to a dropped relay; the
cause was that it had never been written to disk. The absence was right and the explanation wrong.

## 18. Porting from 1.5 or 1.6

A port is not a re-extraction, but it is not free of reclassification either: 1.7 splits and sharpens
things 1.5 recorded under one name. The permitted changes are enumerated in
`port_mapping_1_5_to_1_7_v1` and nowhere else. A thread that finds itself deciding has found a case
that document does not cover — which is a finding for the register, not a licence to judge.

## 19. What is NOT settled

Stated so nobody builds on it by accident:

- `content_hash` normalisation for **Indic scripts** and for **mathematical notation**
- `solution_steps` for **multi-line algebra and matrices**
- the figure quality floor for **map outlines**
- **two disagreeing sources** for one chapter (LBA vs board Question Bank)
- the **page-render fallback** has never run on a scanned source
