# Review verify brief v1 — SUPERSEDED by v2 (2026-09-22, before it ran). Do not use.

Issued by the coordinator, 2026-09-22, under review method v1.4 (viyamo-record/design/). Authority: Yash
approved the method and its code; no human reviews anything before go-live — the coordinator decides, with
references (Yash, 2026-09-22).

## What the verifier does
For each class, one packet per unit at `Devs/_review/c<N>/verify/<unit>.json`. One FRESH sub-agent per packet,
up to 6 launched together in one message. The thread orchestrates; it judges nothing itself.
Each item is one of two tasks:
- `key`  — decide the stored key: KEEP, CORRECT or HOLD, with a reference.
- `stem` — decide whether the question text itself is defective on the page: STEM_OK or STEM_DEFECT.
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
   FAIL (including a quote NOT FOUND on its cited page) → re-run with a NEW agent; two FAILs → stop that packet
   and report. WARN (a quote on a page whose text layer cannot be decoded) is not a FAIL: list it in your delivery.
5. Deliver per class: one ledger entry (kind delivery, ref "review verify c<N>"): packets, checks, re-runs, WARNs,
   usage. Then the next class. Order: Class 6, 7, 8, 9.

---
## Agent instructions (pass verbatim, with the packet path, the verdict path and the access line)
You are the verifier for a Karnataka State Board science question bank (English medium). Your packet names the
class LBA (the question source, `lba`) and the class textbooks (`textbooks`), all PDFs under the Devs folder.
Each item is a question with its stored key; `lba_pages` gives the PDF page of the question and of its printed key.

For each item with task `key`, decide whether the stored key is right for the question, as the class textbook
teaches it:
- `KEEP`    — the key is right. Give a `reference`.
- `CORRECT` — the key is wrong. Give `new_key` (the right key, as short as the question needs), `new_option_id`
              for a question with options, and a `reference`.
- `HOLD`    — no reference decides it, the question itself is defective, or it depends on a figure you cannot
              resolve. Give `reason`.
A reference is EITHER {"kind":"textbook","file":"<textbook file name>","pdf_page":<PDF page number>,
"quote":"<a sentence copied EXACTLY from that page, at least 20 characters>"} OR, for a calculation,
{"kind":"computation","working":"<the full working, step by step>"}. The quote is checked by a program against
the page's text: a quote the page does not print fails. Never CORRECT without a reference; if you cannot find
one, HOLD.

For each item with task `stem`, look at the question on its LBA page (render it: `pdftoppm -r 100 -f P -l P
-png <lba> <out>` into your own folder under $HOME, never /tmp) and decide:
- `STEM_OK`     — the stored question text matches the page and is complete and sensible
- `STEM_DEFECT` — garbled, merged with another item, missing words, or not the printed question
Give `reason` either way, naming the page you read.

Open only your packet, the LBA and the textbooks named in it. Write the verdict file DIRECTLY to its path.
Create no other file except page renders under your own $HOME folder (nothing in /tmp), and never run a file you
did not write in this task. Judge at the class level. Do not invent facts or quotes.

Write ONLY this JSON to the verdict path, every item exactly once, in packet order, then reply
"done <unit> <number of items>":
{"unit":"<unit>","items":[
 {"id":"…","outcome":"KEEP|CORRECT|HOLD|STEM_OK|STEM_DEFECT","reason":"…",
  "new_key":"…","new_option_id":"…","reference":{…}}
]}
