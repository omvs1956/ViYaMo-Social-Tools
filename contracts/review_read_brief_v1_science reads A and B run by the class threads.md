# Review read brief v1 — Science reads A and B, run by the class threads

Issued by the coordinator, 2026-09-22, under review method v1.3 (viyamo-record/design/). Authority:
Yash approved the method and the code bundle, 2026-09-22. This brief EXTENDS each Class 6–9 thread's
lane to exactly this task, for its own class only. Nothing else is opened by it.

## What you do
For your class, two reads, A then B, of every packet in `Devs/_review/c<N>/readA/` and `.../readB/`.
One FRESH sub-agent per packet (per unit per read). Up to 6 at a time. You orchestrate; you do not judge.

1. Launch agents in batches of up to 6 in ONE message. Give each agent only: the section "Agent
   instructions" below, verbatim; its packet path; its verdict path
   `Devs/_review/c<N>/read<X>/verdicts/<unit>.json`. Do NOT read packets into your own context — that is
   what keeps your cost flat. The agent reads its packet and writes its verdict file.
   ACCESS LINE (ruled 2026-09-22, from Class 6's calibration): you may add ONE line telling the agent how
   to reach the files — e.g. load device_bash via ToolSearch, and the $HOME/mnt/ spelling of its two
   paths. Nothing about content. Report it in your delivery.
   FILE-HYGIENE LINE (ruled 2026-09-22, Class 9 incident: an agent ran another thread's /tmp script): every
   agent from now on also gets the two sentences now in the agent instructions ("Write the verdict file
   DIRECTLY … never run a file you did not write in this task."). All threads' agents share one /tmp on
   Yash's computer.
2. When an agent returns: `python3 viyamo-tools/src/review_merge.py stamp <verdict> --actor <your thread id>
   --agent <thread>/read<X>/<unit> --usage <the agent's reported total tokens, if shown>`.
3. Then `python3 viyamo-tools/src/review_merge.py check <verdict> --packet <packet>`.
   A FAIL is re-run with a fresh agent; never hand-edit a verdict. Two FAILs on the same packet → stop
   that packet and report it. Do not open verdict files yourself beyond running these two commands.
   FALLBACK — only if an agent reports it cannot open its packet: read the packet yourself, pass its JSON
   in the agent's prompt, and write the agent's returned JSON to the verdict path unchanged; record in
   your delivery entry which units used the fallback.
4. Read A is finished for every unit before read B starts. After read A, DELIVER read A and STOP: the
   coordinator seals the read-A verdicts (review_merge.py seal-a — they are replaced on Devs by stubs) and
   then says GO for read B (ruled 2026-09-22). NEVER pass read A's output to a read-B agent.
5. **Calibration stop:** run your FIRST unit of read A ALONE (one agent), then stop and report its `usage` to the
   coordinator (ledger + report). Continue only when the coordinator re-states the estimate.
6. Deliver: one ledger entry per read (kind `delivery`, ref `review read <X> c<N>`), listing units done,
   check results, re-runs and total usage. No commits to viyamo-staging. No tags.

## Why this shape (your four points, answered)
- **Identity.** The reads are YOUR work product: every verdict file carries your actor id plus the agent
  label, and your ledger carries the delivery. Agents write nothing to the record.
- **Lane.** This brief is the coordinator's ruling that opens this one task. c6-sci-batch-07,
  c7-sci-batch-08, c8-sci-batch-09 and c9-sci-batch-05 are all CHECKED.
- **Access.** Agents read one packet and write one verdict file under `Devs/_review/`; nothing else. If your link to the
  computer is down, wait; do not work from memory.
- **Locks.** No git writes at all in this task: verdicts are plain files under `_review/`.
- No Workflow tool: plain sub-agents only.

## If you cannot launch sub-agents
STOP and say so. Do NOT read the units yourself — the two reads would no longer be independent.

---
## Agent instructions (pass verbatim, with the packet path and the verdict path)
You are checking the ANSWER KEYS of a Karnataka State Board science question bank (English medium),
one unit. Each item has a question (`stem`), sometimes `options` or `match` columns, and the stored
`key`. Some keys have been deliberately altered to test you; you are not told which.

For EVERY item, give exactly one verdict:
- `CORRECT`    — the key correctly answers the question as a class textbook would expect
- `WRONG`      — the key is scientifically wrong, answers a different question, or picks the wrong option
- `INCOMPLETE` — right as far as it goes, but short of what the question asks (e.g. asks for two, gives one)
- `UNSURE`     — you cannot decide from the text (ambiguous stem, depends on a figure you cannot see,
                 arguable answer)
Also set `stem_defect: true` when the question text itself is garbled, merged with another item,
or missing words — whatever the key.

Open NO file other than your packet, and write no file other than your verdict path.
Write the verdict file DIRECTLY to its path. Create no other file (no scripts, nothing in /tmp) and never
run a file you did not write in this task.
Rules: judge the science and the fit to the question, not spelling or style. A bare "Yes"/"No" or a
one-word key is fine if it is right. Judge at the class level (a Class 6 answer need not be a
university answer). Do not invent facts about the textbook. Read every item in full.

Read the packet file you are given. Write ONLY this JSON to the verdict path you are given, every item
exactly once, in packet order, then reply "done <unit> <number of items>":
{"unit": "<unit>", "read": "<A|B>", "items": [
  {"id": "<id>", "verdict": "CORRECT|WRONG|INCOMPLETE|UNSURE", "reason": "<one line; required unless CORRECT>",
   "suggested": "<your key; required for WRONG>", "stem_defect": false}
]}
