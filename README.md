# viyamo-tools

Shared tooling for the question-bank pipeline (Mohre Public School / ViYaMo). Written by the coordinator; read by every extraction thread. This repo holds code and rules only — never a question bank.

**Threads read this repo from the shared clone `Devs/viyamo-tools/` and never run git in it.** The coordinator pushes here and updates that clone.

## contracts/ — the rules in force (the ONLY authority)
Contract 1.7: `question_schema_v7` (file layer) · `runtime_schema_v1` · `extraction_procedure_v2` · `port_to_1_7_spec_v1` · `port_mapping_1_5_to_1_7_v1`. Every change is a commit here, so a unit's rules are recoverable from the commit in force at its tag. The Drive `contracts\` folder is an archive copy the coordinator refreshes at freeze points; where the two differ, this folder wins. Older contracts (1.4–1.6, the extraction briefs, the amendment logs) are superseded wherever they conflict.

## src/filecheck.py — the structural gate
**Gate 2.10.** Implements contracts **1.5**, **1.6** and **1.7**; every rule — and the content sample — is keyed to the contract the unit declares, so a 1.5 or 1.6 file is checked exactly as gate 2.8 checked it. For 1.7 it checks locators, stimuli, answer provenance and evidence, pending categories against `pending_summary`, `procedure_file`, `duplicated_numbers`, `assets[].pdf_page`, the 1.7 vocabulary including the last-resort `unclassified`, and warns on flat-extracted assets. Standard library only.

    python3 src/filecheck.py <unit.json> [--images DIR] [--json out.json]

The gate prints the contract and log versions it enforces and refuses a unit whose `contract_file` names another contract. `--sample <full 40-character commit SHA>` prints the content-sample ids for a batch (up to 3 review-blocking, up to 2 figure-bearing, filled to 5 by a PRNG seeded with the SHA); the coordinator recomputes them from the tag, so the sample cannot be pre-selected. The coordinator runs the same script with the same exit codes on fetch.

Exit 0 = PASS, 1 = FAIL (every finding names the question and the contract's fix vocabulary), 2 = unreadable file. Structure only — the content sample against the printed page stays with the coordinator.

**Rule:** every thread runs it on every unit and fixes every FAIL before tagging a batch. A tagged unit that fails `filecheck.py` is returned without a manual check. The coordinator runs the same script on fetch.

## src/pending.py — the defect register, counted
    python3 src/pending.py --register <viyamo-record>/defects [--units <unit dirs>]
Counts open register instances per class from `defects/instances/class-N.csv`, alerts at 20 open `unclassified` in one class, and lists any question flagged in a unit but missing from the register. Threads run it before pushing register rows; it must report no ERROR.

## src/folio_scan.py — page numbers stored inside question text (2026-09-21)
    python3 src/folio_scan.py --pdf <LBA.pdf> --out report.md [--renders DIR] <unit files or dirs>
Only numbers INSIDE stored text are examined (every text field: stem, options, answer and its parts, printed
key, solution steps). A 1-3 digit number that equals the folio of a page around the question's locators (the page
before, two after) is looked up on the page and classed FOLIO / CONTENT / UNCLEAR; the folio band is learned
from where each book prints its folios. A unit with no locators is an ERROR (exit 2), never a clean pass.
Test: `tests/folio_plant.py <units> <copy dir> <expected.json>` plants folios of 11 shapes into copies and writes
the expected list before scanning; 34/34 caught on Classes 6-8 (2026-09-21), none outside the plants.
Procedure §14, full read step 6. Not part of the gate: it needs the source PDF.

## src/record.py — the writer for viyamo-record (rewritten 2026-09-21)
    python3 src/record.py --record <viyamo-record> entry --ledger <thread> --actor <actor> --kind <kind> \
        --ref "<ref>" --what "<one line>" --evidence "[derived] …" [--evidence "[stated] …"] \
        --cost "…" --blocks "…" --outcome "…"
    python3 src/record.py --record <viyamo-record> task --thread <t> --task "<task>" --state <STATE> [--reason "…"]
    python3 src/record.py --record <viyamo-record> blocked --on yash|coordinator --item "…" --state open|closed [--note "…"]
    python3 src/record.py --record <viyamo-record> index
Appends ledger entries with the clock's timestamp (Asia/Kolkata) and a validated kind; every evidence
line must start `[derived]` or `[stated]`; arguments go to Python, so backticks and `$` are never
executed (the heredoc hazard). `task` and `blocked` keep `status/tasks.csv` and `status/blocked.csv`;
`index` regenerates `ledgers/_index.md`.

## src/status.py — generates STATUS.md (rewritten 2026-09-21)
    python3 src/status.py --record <viyamo-record> --tools <viyamo-tools> --staging <viyamo-staging> [--check]
Nothing in STATUS.md is typed: contracts and gate from this repo, tags and unit counts from the staging
clone, content-checked tags from coordinator ledger entries naming the tag with CHECKED, the register
from `defects/instances/`, threads and blocked lists from `status/*.csv`. "As of" is the newest ledger
entry, so `--check` exits 1 when STATUS.md is stale or hand-edited.

**Workflow rule (Yash, 2026-09-21; procedure §13):** any workflow change updates `record.py` and
`status.py` in the same change, or the change is incomplete.

The crop-era versions (check records in `_temp/_checks/`, crops read from montages) are retired with
viyamo-renders; they remain in this repo's history.

**Two rules carried over.** A verdict covers only what its record lists. And a displacement band is
verified pair by pair — every question in the run, not a sample (procedure §4.3, 2026-09-21; this
replaces the old first/last/first-aligned sample rule).

## Repos and roles
| repo | holds | threads | coordinator |
|---|---|---|---|
| viyamo-staging | unit JSONs, images/, figure sheets | write (own branch) | read |
| viyamo-record | ledgers, STATUS, defect register, reports and working scripts | write (own ledger, own class CSV, own reports/class-N/) | write |
| viyamo-tools | code and contracts | read, via the shared Devs clone | write |
| viyamo-renders | RETIRED with the crop pipeline | none | none |

## Git rules (all repos)
- One branch per class-subject (`class-7-science` …), created from `main`; never commit to `main` in the bank repos or to another class's branch.
- A batch = one commit + one tag `c<class>-sci-batch-<NN>` on your branch. Tags and pushed branches are **never rewritten** — no force-push, no tag moves; a wrong batch is superseded by the next tag.
- First commit on a branch: `.gitattributes` with `* -text`; `.gitignore` with `_oversize/`, `*.tmp`, `_scratch/`.
- Use a worktree per branch (`git worktree add ..\wt-<repo>-<branch> <branch>`); never `git worktree prune` (repair only); clear only your own lock files.
- Report section 7 notes use a fixed shape: `case (question id) · gap · what was done · suggested rule`.
- (Coordinator) Files created inside the Google Drive for desktop mirror are hard-linked on creation and the Cowork bridge refuses to read them. Build outside the mirror; copy in.
- Image identity is by pixel hash, not file hash (Drive re-encodes PNGs).
- **Threads work only in the Devs folder and git; they never touch Google Drive.** Reports, working scripts, ledgers and register rows live in `viyamo-record`; sources and book notes are copied for threads into `Devs/_reference/class-N/`. The coordinator alone writes to Drive, and only frozen material. Sends are copies of tagged files into the Drive archive on Yash's order.
- **Delete permission first.** Git removes temporary and lock files on every commit; in a connected folder that fails until deletion is allowed, and a failed commit leaves locks that block every thread sharing the repo. Ask for delete permission on the Devs folder before the first git write.
