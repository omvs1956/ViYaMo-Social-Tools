# Review verify brief v2 — stage 3 adjudication, run by the verifier thread

Issued by the coordinator, 2026-09-22, under review method v1.4; supersedes brief v1 (viyamo-record/design/). Authority: Yash
approved the method and its code; no human reviews anything before go-live — the coordinator decides, with
references (Yash, 2026-09-22).

## What the verifier does
For each class, one packet per unit at `Devs/_review/c<N>/verify/<unit>.json`. One FRESH sub-agent per packet,
up to 6 launched together in one message. The thread orchestrates; it judges nothing itself.
Each item is one of three tasks:
- `key`  — decide the stored key: KEEP, CORRECT or HOLD, with a reference.
- `stem` — decide whether the question text itself is defective on the page: STEM_OK or STEM_DEFECT.
- `both` — the stem first, then the key.
Supersedes brief v1 (2026-09-22, never run): v2 adds `both`, the new_key shapes, PDF-page wording, the
quote search across the whole book, and reading pages by text layer (agents may not be able to see images).
The packet deliberately carries NO earlier verdicts. Never look for them: never open `Devs/_review/c*/readA/`,
`readB/`, or `viyamo-record/review/`.

## Steps
1. Calibration: the FIRST packet of the first class ALONE (one agent); stamp, check, STOP, report its usage;
   continue when the coordinator re-states the estimate.
2. Per agent: give ONLY the Agent instructions below, verbatim; its packet path; its verdict path
   `Devs/_review/c<N>/verify/verdicts/<unit>.json`; and one access line (how to reach the files: device_bash via
   ToolSearch and the $HOME/mnt/ spelling of the paths). Nothing about content, nothing about how to write the file.
3. When it returns: `python3 viyamo-tools/src/review_merge.py stamp <verdict> --actor verifier-science
   --agent verifier-science/c<N>/<unit> --usage <agent's reported total tokens>`.
4. `python3 viyamo-tools/src/review_adjudicate.py check <verdict> --packet <packet> --reference Devs/_reference`
   FAIL (including a quote the book does not print) → re-run with a NEW agent; two FAILs → stop that packet and
   report. WARN (a quote found on another page than cited, or a cited page whose text layer code cannot read) is
   not a FAIL: list it in your delivery.
   NO FALLBACK (ruled 2026-09-22): an agent that cannot reach the files cannot read the LBA or the textbooks,
   so the packet alone cannot be adjudicated. If an agent cannot reach device_bash: STOP and report.
5. Deliver per class: one ledger entry (kind delivery, ref "review verify c<N>"): packets, checks, re-runs, WARNs,
   usage. Then the next class. Order: Class 6, 7, 8, 9.

---
## Agent instructions (pass verbatim, with the packet path, the verdict path and the access line)
You are the verifier for a Karnataka State Board science question bank (English medium). Your packet names the
class LBA (the question source, `lba`) and the class textbooks (`textbooks`); every path in the packet is
relative to the Devs folder. Each item is a question with its stored key; `lba_pages` gives the PDF page of the
question and of its printed key. Read LBA pages with `pdftotext -layout -f P -l P <pdf> -`.
Read TEXTBOOK pages from the prepared page texts, not from the PDF: `<textbook folder>/text/<textbook file name
without .pdf>/pNNNN.txt` (NNNN = the PDF page, 4 digits). They hold the text layer with shifted glyphs decoded,
or OCR where the page has no text layer (amended 2026-09-22: many textbook pages are images). Quote from these
files: the checker matches your quote against exactly them. Do not run your own OCR. To SEE a page or a
figure (amended 2026-09-22 — the earlier wording made it impossible): render it INTO the Devs folder, at
`Devs/_scratch/verifier-science/<unit>/` (`pdftoppm -r 100 -f P -l P -png <pdf> <that folder>/pP`), copy it into your
own workspace with device_stage_files, and open the staged copy with your file reader. A file under $HOME cannot be
staged and cannot be seen. Only if that fails, say so and HOLD a question that depends on the figure.

Each item has a `task`:

`key` — decide whether the stored key is right for the question, as the class textbook teaches it:
- `KEEP`    — the key is right. Give a `reference`.
- `CORRECT` — the key is wrong. Give `new_key`, `new_option_id` for a question with options, and a `reference`.
- `HOLD`    — no reference decides it, the question itself is defective, or it depends on a figure you cannot
              see. Give `reason`.

`stem` — decide whether the stored question text is itself defective, against its LBA page (the field is
`outcome`; `stem_outcome` is only for task `both`):
- `STEM_OK`     — it matches the page and is complete and sensible
- `STEM_DEFECT` — garbled, merged with another item, missing words, or not the printed question
Give `reason` either way, naming the page you read.

`both` — first the stem (`stem_outcome` STEM_OK | STEM_DEFECT, with `stem_reason`), then the key as for `key`
(`outcome` …). A STEM_DEFECT always has outcome `HOLD`.

A `reference` is EITHER {"kind":"textbook","file":"<the textbook's file name exactly>","pdf_page":<the PDF page
number — the page index in the file, NOT the number printed on the page>,"quote":"<a sentence copied EXACTLY
from that page, at least 20 characters>"} OR, for a calculation, {"kind":"computation","working":"<the full
working, step by step, with units>"}. A program checks every quote against the textbook's text: a quote the book
does not print fails. Never CORRECT without a reference; if you cannot find one, HOLD.
The quote must itself STATE the fact that decides the key (amended 2026-09-22 after calibration): a sentence
that only mentions the topic is not a reference. If no sentence in the textbook states it, use a computation
(for a calculation) or HOLD.

`new_key` in the shape the question needs: an option question → the option's text, plus `new_option_id` (one of
its option ids); match → pairs as "1-b; 2-a; 3-d"; numeric → value and unit ("54 km/h"); anything else → the
answer as short as the question needs.

Open only your packet, the LBA and the textbooks named in it. Write the verdict file DIRECTLY to its path.
Create no other file except page renders under Devs/_scratch/verifier-science/<unit>/ (nothing in /tmp, nothing under $HOME that you need to look at), and never run a file you
did not write in this task. Judge at the class level. Do not invent facts or quotes.

Write ONLY this JSON to the verdict path, every item exactly once, in packet order, then reply
"done <unit> <number of items>":
{"unit":"<unit>","items":[
 {"id":"…","outcome":"KEEP|CORRECT|HOLD|STEM_OK|STEM_DEFECT","reason":"…","stem_outcome":"…","stem_reason":"…",
  "new_key":"…","new_option_id":"…","reference":{…}}
]}
(Give only the fields your item's task and outcome need.)
