#!/usr/bin/env python3
"""record.py — the writer for viyamo-record's structured files.

Nobody hand-edits the record's structured files; they are written through this script,
which enforces the formats and takes every timestamp from the clock, never from memory.

    entry    append one ledger entry (append-only; the file may only grow)
    task     set a row of status/tasks.csv            (the "Threads" table in STATUS.md)
    blocked  set a row of status/blocked.csv          (the "Blocked on …" lists)
    index    regenerate ledgers/_index.md from the ledgers

After any of these, regenerate STATUS.md:  python3 status.py --record <viyamo-record> ...

WORKFLOW RULE (Yash, 2026-09-21; procedure §13): any change to the workflow — a new ledger
kind, a new task state, a new register column, a new required step — updates record.py and
status.py IN THE SAME CHANGE, or the change is incomplete.

Examples (arguments are passed to Python, not through a heredoc, so backticks and $ are safe):
    python3 record.py --record ~/vr entry --ledger coordinator --actor coordinator \
        --kind ruling --ref "joint review" --what "one line" \
        --evidence "[derived] first line" --evidence "[stated] second line" \
        --cost "-" --blocks nothing --outcome "-"
    python3 record.py --record ~/vr task --thread c6-sci-t2 --task "port to 1.7" --state CHECKED \
        --reason "verified by the coordinator"
    python3 record.py --record ~/vr blocked --on yash --item "marks rubric v1" --state open
    python3 record.py --record ~/vr index

Standard library only.
"""
import argparse, csv, datetime, glob, os, re, sys

KINDS = ["work", "finding", "incident", "correction", "pushback", "delivery", "decision",
         "ruling", "verification", "advice", "deviation", "owed"]
STATES = ["NOT STARTED", "ISSUED", "IN PROGRESS", "STOPPED", "DELIVERED", "CHECKED", "COMPLETE",
          "PARTIAL", "SKIPPED", "ON HOLD", "BLOCKED", "CLOSED"]
BLOCK_ON = ["yash", "coordinator"]
BLOCK_STATES = ["open", "closed"]
TASK_COLS = ["thread", "task", "state", "reason", "as_of"]
BLOCK_COLS = ["on", "item", "state", "note", "as_of"]
# entries before 2026-09-21 afternoon carry a date only; both forms are entries
HEAD_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}[+-]\d{2}:\d{2})?) · ([^·]+?) · ([^·]+?) · (.*)$")
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def now():
    t = datetime.datetime.now(IST)
    return t.strftime("%Y-%m-%dT%H:%M") + "+05:30"


def ledger_path(record, name):
    if name.startswith("ledger_") and name.endswith(".md"):
        p = os.path.join(record, "ledgers", name)
    else:
        hits = sorted(glob.glob(os.path.join(record, "ledgers", f"ledger_{name}_v*.md")))
        if len(hits) != 1:
            sys.exit(f"ledger {name!r}: {len(hits)} files match ledgers/ledger_{name}_v*.md — name it exactly")
        p = hits[0]
    if not os.path.exists(p):
        sys.exit(f"no ledger {p} — a ledger is opened by the coordinator, not by an entry")
    return p


def one_line(s, field):
    if "\n" in s:
        sys.exit(f"--{field} must be one line; use repeated --evidence for multi-line evidence")
    return s.strip()


def cmd_entry(a):
    if a.kind not in KINDS:
        sys.exit(f"kind {a.kind!r} not in {KINDS}")
    p = ledger_path(a.record, a.ledger)
    ev = [one_line(e, "evidence") for e in (a.evidence or [])]
    if not ev:
        sys.exit("--evidence is required: what can be checked ([derived] or [stated])")
    bad = [e for e in ev if not re.match(r"\s*\[(derived|stated)\]", e)]
    if bad and not a.allow_untagged:
        sys.exit("every --evidence line starts with [derived] or [stated]: " + "; ".join(bad[:3]))
    head = f"## {now()} · {one_line(a.actor, 'actor')} · {a.kind} · {one_line(a.ref, 'ref')}"
    body = [head,
            f"what:     {one_line(a.what, 'what')}",
            "evidence: " + ev[0]] + [" " * 10 + e for e in ev[1:]] + [
            f"cost:     {one_line(a.cost, 'cost')}",
            f"blocks:   {one_line(a.blocks, 'blocks')}",
            f"outcome:  {one_line(a.outcome, 'outcome')}"]
    before = os.path.getsize(p)
    with open(p, "rb") as fh:
        fh.seek(max(0, before - 1))
        ends_nl = before == 0 or fh.read(1) == b"\n"
    with open(p, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(("" if ends_nl else "\n") + "\n" + "\n".join(body) + "\n")
    if os.path.getsize(p) <= before:
        sys.exit("append failed: the ledger did not grow")
    print(head)


def upsert(path, cols, key, row):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rows = []
    if os.path.exists(path):
        with open(path, encoding="utf-8", newline="") as fh:
            rd = csv.DictReader(fh)
            if rd.fieldnames != cols:
                sys.exit(f"{path}: header {rd.fieldnames} != {cols}")
            rows = list(rd)
    for r in rows:
        if all(r[k] == row[k] for k in key):
            r.update(row)
            break
    else:
        rows.append(row)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def cmd_task(a):
    if a.state not in STATES:
        sys.exit(f"state {a.state!r} not in {STATES}")
    upsert(os.path.join(a.record, "status", "tasks.csv"), TASK_COLS, ("thread", "task"),
           dict(thread=a.thread, task=a.task, state=a.state, reason=a.reason or "", as_of=now()[:10]))
    print(f"task {a.thread} / {a.task} -> {a.state}")


def cmd_blocked(a):
    if a.on not in BLOCK_ON or a.state not in BLOCK_STATES:
        sys.exit(f"--on in {BLOCK_ON}, --state in {BLOCK_STATES}")
    upsert(os.path.join(a.record, "status", "blocked.csv"), BLOCK_COLS, ("on", "item"),
           dict(on=a.on, item=a.item, state=a.state, note=a.note or "", as_of=now()[:10]))
    print(f"blocked on {a.on}: {a.item} -> {a.state}")


def read_ledger(p):
    heads = []
    with open(p, encoding="utf-8") as fh:
        for line in fh:
            m = HEAD_RE.match(line.rstrip("\n"))
            if m:
                heads.append(dict(ts=m[1], actor=m[2].strip(), kind=m[3].strip(), ref=m[4].strip()))
    return heads


def cmd_index(a):
    rows = []
    for p in sorted(glob.glob(os.path.join(a.record, "ledgers", "ledger_*.md"))):
        name = os.path.basename(p)
        thread = re.match(r"ledger_(.+)_v\d+\.md$", name)[1]
        h = read_ledger(p)
        last = h[-1] if h else None
        rows.append((thread, name, len(h), h[0]["ts"][:10] if h else "—", last["ts"] if last else "—",
                     f'{last["kind"]} · {last["ref"]}' if last else "—"))
    out = ["# Ledger index", "",
           "GENERATED by `viyamo-tools/src/record.py index` — do not hand-edit.", "",
           "| thread | ledger | entries | opened | last entry | last entry is |", "|---|---|---|---|---|---|"]
    out += [f"| {t} | `{n}` | {c} | {o} | {l} | {k} |" for t, n, c, o, l, k in rows]
    out += ["", "Entries are counted by their heading line (`## <timestamp> · <actor> · <kind> · <ref>`)."]
    with open(os.path.join(a.record, "ledgers", "_index.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"index: {len(rows)} ledgers")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--record", required=True, help="path to the viyamo-record clone")
    sp = ap.add_subparsers(dest="cmd", required=True)
    e = sp.add_parser("entry")
    for f in ("ledger", "actor", "kind", "ref", "what", "cost", "blocks", "outcome"):
        e.add_argument("--" + f, required=True)
    e.add_argument("--evidence", action="append")
    e.add_argument("--allow-untagged", action="store_true", help="old-style evidence without [derived]/[stated]")
    t = sp.add_parser("task")
    for f in ("thread", "task", "state"):
        t.add_argument("--" + f, required=True)
    t.add_argument("--reason")
    b = sp.add_parser("blocked")
    for f in ("on", "item", "state"):
        b.add_argument("--" + f, required=True)
    b.add_argument("--note")
    sp.add_parser("index")
    a = ap.parse_args()
    dict(entry=cmd_entry, task=cmd_task, blocked=cmd_blocked, index=cmd_index)[a.cmd](a)


if __name__ == "__main__":
    main()
