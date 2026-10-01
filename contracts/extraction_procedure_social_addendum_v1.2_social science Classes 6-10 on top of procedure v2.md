SOCIAL SCIENCE ADDENDUM to extraction_procedure_v2 · v1.2 · 2026-10-01 · IN FORCE (committed on Yash's go, 2026-10-01; supersedes v1.1)
(v1.2, from pilot batch-01 (Class 10 ch4 + ch27, tag c10-soc-batch-01r1): features_source + answer-map transcription
 for category-instruction maps; slug feature ids; text-only key with a printed typo; marks structurally unprinted in
 the Class 10 LBA; difficulty table vs tags; the un-bulleted first answer point; provenance fields set once; chapter
 boundary + TOC drift notes; coordinator checks scoped to the chapter span. No schema or gate change.)
(v1.1: fresh-read critique against 1.7 + v2 — asset role corrected to answer_diagram; quota_table = difficulty_only;
 "exhaustive QB" found to be a 2nd EDITION of the LBA, not a source; MQP unitisation gap raised; Position gains
 geometry kind; parenthetical disambiguation; crop reproducibility; map questions always content-sampled;
 §0 overclaim narrowed.)
Layer: PROCEDURE (subject addendum). Status: IN FORCE — units built from now name this file as procedure_file;
batch-01 units name v1.1 and stand.
Companions: question_schema_v7 (FILE, contract 1.7 — UNCHANGED) · extraction_procedure_v2 (PROCEDURE).

0. WHAT THIS IS
   E1 tested contract 1.7 + gate 2.18 on six real Class 10 questions across five shapes (letter-key MCQ, text-only
   VSA key, bullet-list LA key, sub-headed key, mark-on-map) — two scratch units PASS, fail=0. Those shapes need NO
   schema change and NO new contract version. Classes 6-9 layouts are UNSEEN and are confirmed at each class's
   survey, not assumed from Class 10. A social unit file carries:
     "contract_version": "1.7"  ·  "schema_file": "question_schema_v7_….json"  ·  "procedure_file": "<this addendum>"
   Every rule of extraction_procedure_v2 applies unless a numbered item below refines it. A subject addendum to the
   PROCEDURE, not a new contract (the maths 1.8 addendum changed stored fields; social changes none).
   OPTIONAL additive fields (the map block, item 6): the gate validates REQUIRED fields and IGNORES optional extras
   (verified E1), so a unit carrying them PASSES today — which also means a TYPO in an optional field passes
   silently. Until a gate rule validates the block (CODE, Yash's go), every map question is in the coordinator's
   content sample (item 6.5).

1. SUBJECT, IDS, LANGUAGE
   - subject slug "social"; id segment "soc" (2-4 letters; gate-verified). language "en".
   - id = soc-<class>-<chapter2>-s<section>-q<qqq>. chapter_id = the FULL id prefix "soc-<class>-<chapter2>" (gate:
     qid.startswith(chapter_id)); NOT the bare number. E1 caught this.
   - content_hash: Class 10 English-medium question text is plain English; 1.6/1.7 normalisation applies as is.
     [D4] Each class's survey confirms NO Kannada run inside QUESTION text. If one is found, that class STOPS at
     that chapter until a normalisation profile exists (1.7: content_hash is unspecified for Indic script) —
     escalate to Yash; never improvise a normalisation.

2. CHAPTER NUMBER, PRINTED ORDER, DISCIPLINE, BOUNDARIES  (new — social is multi-discipline)
   - The LBA prints chapters in NON-NUMERIC order across six disciplines (History, Political Science, Sociology,
     Geography, Economics, Business Studies). The chapter NUMBER sets <chapter2>; print order is metadata.
   - A per-class SUBJECT MAP (coordinator artifact) records per chapter: number, discipline, printed title, pdf
     pages of its question block and of its answer block.
   - Chapter boundaries: the next "Chapter N" heading. The row of red asterisks that precedes it is a GRAPHIC and is
     absent from the text layer (pilot: a thread reported "no separator" from the text layer — a failed read, v2 §16);
     never rely on it. A pdf page can hold the END of one chapter and the START of the next (p16/p58 open with
     Chapter 3's tail; p36, p106). extraction.pdf_pages lists EVERY page the chapter touches; a region render (item 6)
     must exclude the neighbouring chapter's text. EVERY parse — the thread's and the coordinator's — is scoped to the
     span from the chapter's heading to the next heading: a by-number check over whole pages pairs the wrong chapter.
   - Page location: by heading + printed folio (v2 §12). The Class 10 LBA's CONTENT page prints question/answer page
     columns that DRIFT from the printed folios (+3/+4 by ch27); the real printed-folio-to-pdf offset is a constant
     +12 for the body. TOC numbers are never used for location.
   - Section id -sN- = printed ORDER of sections on the QUESTION side (v2 §2). The ANSWER side REGROUPS sections
     (ch1: question side I/II/III…, answer side carries IV): pairing is by printed NUMBER only (v2 §4.1), never by
     the answer-side roman; answer-side headings never set marks or type (v2 §2).

3. FUSED SECTION / QUESTION NUMBERS  (refines v2 §2) — BOTH sides
   A roman may print fused with a question number on either side: "IV. 29. Mark the following…" (question side),
   "V. 25" (answer side). Split mechanically: leading roman (dot optional) = section; following integer = question
   number; the roman is NOT part of the stem or key.

4. KEY FORMS AND INLINE MARKERS  (refines v2 §3, §4, §6)
   4.1 MCQ key LETTER+text ("1. b) Constantinople") -> option by the printed letter; text confirms.
   4.2 MCQ key TEXT ONLY, no letter ("1) Basappa Shastri") -> v2 §3 two-pass normalised matching; the derived
       letter is recorded as a source_correction {field:"answer", printed:<key text>, corrected:<option id>,
       basis:"pass 1"|"pass 2"}; zero/several matches -> the 1.7 flag with suggested, never the closest option.
   4.3 VSA/SA key as bare text ("6. Robert Clive") -> answer.text, verbatim (v2 §4).
   4.4 TEXT-ONLY key that matches no option because of a PRINTED TYPO (pilot ch4 q7: key "Krishna Raj Wodeyar IV" vs
       option B "Krishnaraja Wodeyar IV"; pass 1 and pass 2 both fail): option_id null + flag "key text not among
       options" + suggested <letter — printed key vs option>; register key-text-not-among-options. There is no letter
       to keep and extraction never picks the closest option; the intended letter is confirmed at REVIEW. (The 1.7
       "differs by a printed typo" entry presumes a printed letter and does not apply.)
   4.5 MARKS — STRUCTURAL FOR THE CLASS 10 LBA (escalate rule fired at 100% in both pilot units): sections I and II
       print no marks; III and IV print ALTERNATIVES ("2/3 marks", "3/4 Marks"); section V (maps) prints none. Every
       question therefore carries marks null, marks_source "unassigned" and the flag "marks ambiguous in source —
       <printed>" — this is the EXPECTED state, not a defect of the unit (register section-marks-not-printed, one row
       per unit). Marks are assigned at authoring (v2 §5). For v2 §14 sampling in this source, "unflagged" means "no
       flag other than the structural marks flag".
   4.4 TWO parenthetical kinds sit glued to stems, often side by side — "(June-2022) (Easy)", "(SLP 2020, June
       2025)", "(MQP-1. 21-22)": a DIFFICULTY tag (v2 §6: normalised, removed from text) and an EXAM-APPEARANCE
       marker (1.7 prior_appearances: recorded, removed from text so it leaves content_hash). Neither is content.
       A marker printed against a single map feature is a per-feature prior_appearance (item 6) and is likewise
       removed from the feature name and from text.

5. BULLET-LIST AND SUB-HEADED KEYS  (refines v2 §7)
   5.1 A bullet-list key -> solution_steps[], ONE step per printed LINE (v2 §7 line-break rule). The Class 10 LBA
       often prints the FIRST answer point un-bulleted on the key-number line ("21. Unfit for transportation during
       the rainy season." then bullets): that line IS a step, equal to the bullets. Checkers count printed lines,
       never bullet glyphs (the coordinator's own bullet-only counter mis-flagged six correct keys in the pilot).
       answer.value carries the verbatim key (lines joined by newline). solution_steps is REQUIRED for a bullet key (a
       multi-line answer without it only WARNs at the gate, so the rule, not the gate, enforces it).
   5.2 Sub-headed keys ("Causes…"/"Consequences…", ch1 q23): solution_steps hold ONLY the real answer points; a
       heading is NOT a step (v2 §5 counts points for marks). The heading stays in answer.value verbatim.

6. MAP QUESTIONS — FIELD SCHEMA  (new; refines v2 §4.7, §7, §8; declares the v2 §19 map floor)
   Two kinds — do not conflate:
   (A) MARK-ON-MAP: instruction + lettered feature list on the question side, no figure; the ANSWER is a completed
       map (E1: pdf 106). This item. type "sa" (1.7 has no map type; the type is a weak signal — the answer shape
       and the map block carry the meaning). The lettered list stays in text and is NEVER options (v2 §3).
   (B) READ-THE-MAP: the question SHOWS a map and asks about it -> 1.7 Stimulus kind "map" + a normal text answer.

   6.1 INVARIANT for a mark-on-map question: (a) the "map" block; (b) answer {kind:"text", value:"[diagram answer —
       see page image]"}; (c) an Asset with role "answer_diagram" (v2 §4.7 — a drawn key is an answer_diagram; NOT
       "map_outline", which names a BLANK outline map and is reserved for the generator's base map, item 6.4);
       (d) source_flag "answer is a diagram — no key text — <what the map shows>"; (e) answer_provenance by
       "printed"; (f) locators role "question" (stem page) AND role "answer" (map page). features[] is a PARSE of
       the stem; the stem text stays the source of truth and a mismatch is a defect.

   6.2 The "map" block (OPTIONAL additive fields; EXTRACTION unless marked):
     "map": {
       "subject":     string|null   — map theme if the stem states one ("rivers","ports"); null if mixed
       "instruction": string        — printed instruction verbatim
       "region":      string        — base region the source names ("India")
       "features_source": "stem" | "answer_map_render" | "answer_map_text"
                                    — WHERE the features came from: the stem's lettered list; or, for a CATEGORY
                                      INSTRUCTION ("Mark the major Sea ports…") that lists none, the ANSWER MAP's
                                      printed labels — transcribed from the >=200 dpi render when they are raster
                                      (v2 §7 image-embedded transcription, method in extraction.method_notes), or
                                      read from the text layer inside crop_bbox when present. Listing the key's
                                      printed labels is structuring the key, not authoring. features [] is NOT
                                      acceptable for a mark-on-map question.                                [EXTRACTION]
       "features":    [ MapFeature ] — one per feature; from the stem in printed order, or from the answer map in a
                                      deterministic stated order                                             [EXTRACTION]
       "answer_map_asset_id": string — id of the answer_diagram Asset in assets[]
     }
     MapFeature = {
       "id":              string     — the printed letter where the stem prints one ("A","B"…); otherwise a SLUG of
                                      the name: lowercase, runs of non-alphanumerics -> "-", trimmed, unique within
                                      the map (collision -> "-2"). Render-independent, so the later position join
                                      survives a re-render. (Ordinals, used in batch-01, are replaced by slugs in its
                                      next correction tag.)                                                   [EXTRACTION]
       "name":            string     — feature name verbatim (markers removed, 4.4)
       "name_as_printed": string|opt — where the stem abbreviates or differs
       "category":        string|null— mechanical from the name's own type word: mountain_range|hill|peak|plateau|
                                      coast|river|dam|lake|port|city|state|capital|strait|bay|gulf|island|cape|
                                      latitude|longitude|pass|nat_park|railway|other; null where the name states
                                      none — never guessed; finalised at the MAP INDEX pass
       "prior_appearances": [...]|opt— per-FEATURE exam markers (4.4)
       "position":        Position|null — null at extraction (position is printed only as a picture)  [SET LATER]
       "position_source": "authored"|"digitised_from_printed_map"|"unset" — "unset" at extraction     [SET LATER]
     }
     Position = {                                                                                  [SET LATER]
       "kind":   "point" | "line" | "area"   — a port/city/peak/dam is a point; a river/coast/latitude/longitude
                                              is a LINE; a range/plateau/state is an AREA. A single coordinate
                                              cannot mark a river or a range.
       "anchor": {"lat": number, "lon": number}  — REQUIRED for every kind: the label/marker anchor, degrees,
                                              base-map-INDEPENDENT (one value renders on any India outline)
       "path":   [{"lat","lon"}, …]|opt       — the polyline (line) or outline (area)
       "confidence": "exact" | "approx" | opt
     }
     (No pixel scheme: lat/lon is the only coordinate system, so one coordinate table serves any outline.)

   6.3 The answer map asset: a per-QUESTION REGION render of the answer page (p106 holds two maps on one page),
       located by the printed number label beside the map, >= 200 dpi, every label legible, NOT object extraction
       (§D: ~170 fragments on those pages). The asset records the crop so the coordinator can reproduce it (v2 §14
       renders on demand; v2 §8 "method recorded"): optional "crop_bbox": {"pdf_page", "x0","y0","x1","y1"} in
       PDF points from the top-left. v2 §8 flat-asset check applies.
       FLOOR DECLARATION (v2 §8 permits a subject addendum to declare one, with reason): a region render of a whole
       printed map is not an embedded object; its size is the page region. The figure pixel floor (long>=600 &
       short>=150) therefore does not apply to a map answer_diagram; legibility of every printed label, confirmed
       by eye, is the floor.
   6.4 SET LATER (the custom Q&A generator — OUT of extraction scope): every MapFeature.position + position_source,
       and a reusable BLANK outline asset (role "map_outline") with its lat/lon->pixel projection. Whether a novel
       combination is renderable is decided at render time, not stored. The printed answer map stays the faithful
       extracted answer; positions are an added structured layer.
   6.5 VERIFICATION: every mark-on-map question is ALWAYS in the content sample (v2 §14: a drawn key is a listed
       risky shape), and the map block is checked field by field against the page until a gate rule validates it.
       Transcribed features are a CONTROLLED read: the thread transcribes blind; the coordinator makes an independent
       read of the same crops BEFORE seeing the thread's list and compares name for name (pilot: 24/24).
   6.6 MAP INDEX (coordinator, derived, after extraction): features aggregated by category across the source -> the
       pools ("all rivers", "all ports") a variant draws from; categories finalised. Generated by a script (CODE,
       later); lives beside the subject map.
   6.7 marks: the LBA's printed marks win (v2 §5).

7. TEXTBOOK WATERMARK  (refines v2 §11; a precondition for the TEXTBOOK passes, not for extraction)
   The Class 10 English SS textbook carries a diagonal "NOT TO BE REPUBLISHED" watermark whose glyphs land as
   scattered single letters between paragraphs in the text layer (E1: pp15/30/60/90/130). Body prose otherwise
   clean (~250-350 words/page). v2 §11 already requires the watermark stripped; textbook_text.py does NOT yet do
   it. [CODE — Yash's go, SEPARATE] a watermark-filter pass is needed before ANY pass that quotes the textbook:
   the review verifier (v2 §14) AND the difficulty-authoring textbook pass (v2 §6). It does not block LBA extraction.

8. PER-CHAPTER TABLES THE LBA PRINTS  (the count gate's second method)
   Each chapter prints an LO table and a "Distribution of Questions based on difficulty level" table
   (Easy/Average/Difficult/Total). No per-section or per-type quota table is printed.
   - LO table -> learning_outcomes[] per question (v2 §6); a question in no row -> [] + "no LO mapped".
   - count_gate.quota_table = "difficulty_only" (the 1.7 enum value for exactly this table — NOT "consistent").
     Its Total is count_gate.second_method {method:"printed difficulty distribution table", extracted, agrees}.
   - The table can DISAGREE with the chapter's own per-question tags while its total agrees (pilot ch27: table 9/16/5,
     tags 10/15/5, total 30). The per-question printed tag WINS (v2 §6); the table is a source defect: quota_table
     stays "difficulty_only", the second method stays valid when the TOTAL agrees, the mismatch goes in count_gate.note
     and in the register under difficulty-table-vs-tags (distinct from printed-difficulty-not-per-question, which is
     for MISSING tags). If the TOTAL disagrees with the audited count: quota_table "inconsistent", an independent
     count as second method, a FINDING — never a STOP.

9. CLASS 10 SOURCES  (Yash 2026-09-30/10-01; CORRECTED by the fresh read of the files)
   Classes 6-9: LBA + textbook only.
   Class 10 — what the files under _reference/class-10 actually are:
   - LBA (10thSS-EM-LBA-Revised_….pdf, 121 pp): the primary extraction source.
   - "ExhaustiveQuestionBankPDF - 85E -Social.pdf" (117 pp) is NOT a question bank and is OUT OF SCOPE (Yash ruling
     2026-10-01: "only extract LBA and use that as reference, we will not touch EQB"). Facts for the sources index
     (v2 §10, labelling defect): its cover is the LBA's ("LBA, Revised Edition 2026-27", DIET Haveri); PDF created
     Mon 10 Aug 2026 (the LBA: Tue 11 Aug 2026, 121 pp); same chapters in the same order; 94% of text lines
     identical (3,724 of 3,960). It is an OLDER BUILD of the same edition. It is NOT extracted and NOT used as a
     diff or recovery reference. Anything the LBA lacks (a stem keyed on the answer side but not found on the
     question side) is handled as an LBA source fact at the pilot — rendered, read, and recorded UNREAD or as a
     defect per v2 §4.5/§16 — never recovered from the EQB. [D5 RULED]
   - BLUEPRINT (85EK) is NOT a question source — the marks/quota distribution; it feeds count_gate quota and
     marks_source blueprint_table; never extracted as questions.
   - FOUR MQPs (source mqp) ARE question sources; they are organised by PAPER SECTION, not chapter (MQP-1 §I:
     q1 history, q2 history, q3 political science, q4 constitution), and print no chapter labels.
     [D6 RULED 2026-10-01] UNITISATION of a chapterless source. The id grammar needs <chapter2> at extraction and
     assigning a syllabus chapter per question is a judgement (authoring — forbidden at extraction). Therefore:
     - one unit per paper under a RESERVED chapter2 range: MQP-1..4 -> soc-10-91 .. soc-10-94 (chapter_id
       "soc-10-9N", machine_name soc-10-9N_questions); the paper's own printed sections are -sN-; ids record
       WHERE a question is printed and are re-run-stable. source = "mqp".
     - the syllabus chapter is a TAG, not the id: OPTIONAL additive field on the question
         "chapter_tag": {"chapter_id": "soc-10-CC", "source": "lba_hash_match" | "near_match_confirmed" |
                         "reviewer" | "ai_suggested", "confirmed": boolean}
       (gate-safe like the map block). A consumer keys on chapter_tag.chapter_id ?? chapter_id, so MQP questions
       sit beside LBA questions by chapter.
     - HOW IT IS FILLED (an INDEX pass, not extraction): (1) exact content_hash join against the extracted LBA
       units -> chapter inherited deterministically, source lba_hash_match, confirmed true; (2) token-overlap
       near-matches -> candidates only, never auto-applied; (3) the remainder by a person, or a model's suggestion
       labelled ai_suggested until confirmed. NOTE the LBA's own markers "(MQP-1. 21-22)" cite EARLIER years'
       papers, not these 2026-27 MQPs — provenance only, not a link.
     - NON-BLOCKING (Yash): an unfilled or unconfirmed chapter_tag blocks NOTHING — not extraction, not a tag's
       delivery, not import. The machine pass runs whenever LBA units exist and re-runs as the LBA grows; the
       remainder is batched for Yash together with other review items, at a time of his choosing, never as a
       standalone gate.
   - EXTRACTION ORDER (Class 10): LBA -> 4 MQPs. The EQB is never run.
   - PROVENANCE, not priority (priority is a generator/runtime concern, out of scope): every question records
     source (lba|mqp) and prior_appearances. A question printed in both an MQP and the LBA is extracted in EACH
     unit with its own provenance; the cross-source link is made at IMPORT/INDEX by content_hash, not by a flag at
     extraction (v2 §9's "duplicate of" is WITHIN one source). Disagreement between sources is never reconciled at
     extraction (v2 §10, §19): both recorded, the reviewer rules.

10. PROVENANCE FIELDS ARE SET ONCE  (new — from the pilot's r1)
    created_at, status_history[*].at and answer_provenance.at are set at FIRST extraction and carried forward
    byte-identical through every later write of the unit. A correction is a SURGICAL edit of the stored file; a
    rebuild over a delivered unit is permitted only if it preserves those fields byte-identically AND is disclosed in
    the report's §3 DEVIATIONS before the tag. A pre-tag correction's provenance lives in extraction.method_notes (and
    source_corrections where a value changed), never in re-stamped timestamps. Corrections to a tagged delivery are
    new commits + a new tag suffix (…-01r1, r2 …); the coordinator diffs every delivery against the previous tag at
    QUESTION level and FILE level (v2 §14; pilot: a rebuild re-stamped 28 untouched questions and was caught only by
    the question-level diff).

11. WHAT IS NOT CHANGED
    offset/displacement loop (v2 §4.3), marks rule (§5), difficulty-from-textbook authoring (§6), duplicates (§9),
    the full answer-to-question read with planted controls before delivery (§14) — unchanged. The review PLANT
    redesign for social keys is a REVIEW-phase item, ruled then.

12. OPEN DECISIONS / DEFERRED
    D4 (§1)  no-Kannada check per class; STOP + escalate if found. Class 10: none seen in the pilot chapters (ch4,
             ch27); the gate's content_hash recompute and the thread's report keep checking every chapter.
    batch-01 feature ids: ordinals "01".."12" on soc-10-27 q29/q30 -> slugs at that unit's next correction tag (r2),
             before import; nothing joins on them yet.
    D5 (§9)  RULED 2026-10-01: LBA only; EQB untouched (not extracted, not diffed).
    D6 (§9)  RULED 2026-10-01: MQP units soc-10-91..94; chapter via non-blocking chapter_tag (hash-join, then batch).
    deferred: map positions/base outline (§6.4, generator); textbook_text.py watermark filter (§7, CODE);
              (edition DIFF dropped per D5.)
