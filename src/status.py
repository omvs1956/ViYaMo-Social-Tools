#!/usr/bin/env python3
"""status.py — generate viyamo-record/STATUS.md. Nothing in STATUS.md is hand-written.

Every number is computed from a source of truth:
  · contracts, gate    — the viyamo-tools clone (contracts/, src/filecheck.py, HEAD)
  · tags, units        — the viyamo-staging clone (git tags; unit files read at each class's latest tag)
  · verification       — ledger entries of kind `verification` naming the tag with CHECKED
  · register           — defects/instances/class-N.csv (open = no `resolved` date)
  · threads            — status/tasks.csv      (written by record.py task)
  · blocked lists      — status/blocked.csv    (written by record.py blocked)
  · ledgers            — ledgers/_index.md     (written by record.py index)
The "as of" time is the newest ledger entry, not the clock, so a rerun on an unchanged record
gives an identical file, and --check can tell a stale STATUS.md from a current one.

Usage:
    python3 status.py --record <viyamo-record> --tools <viyamo-tools> --staging <viyamo-staging>
    python3 status.py ... --check      exit 1 if STATUS.md is not what this would write

WORKFLOW RULE (Yash, 2026-09-21; procedure §13): any change to the workflow updates status.py
and record.py IN THE SAME CHANGE, or the change is incomplete.

Standard library only.
"""
import argparse, csv, glob, json, os, re, subprocess, sys
from collections import Counter, defaultdict

TAG_RE = re.compile(r"^c(\d+)-(\w+)-batch-(\d+)$")
# entries before 2026-09-21 afternoon carry a date only; both forms are entries
HEAD_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}[+-]\d{2}:\d{2})?) · ([^·]+?) · ([^·]+?) · (.*)$")
UNCLASSIFIED_ALERT = 20
SUBJ = {"sci": "Science", "math": "Mathematics"}


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True).stdout


def git_bytes(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True).stdout


def ledgers(record):
    out = []
    for p in sorted(glob.glob(os.path.join(record, "ledgers", "ledger_*.md"))):
        text = open(p, encoding="utf-8").read()
        blocks = re.split(r"(?m)^(?=## \d{4}-)", text)
        for b in blocks:
            m = HEAD_RE.match(b.split("\n", 1)[0])
            if m:
                out.append(dict(file=os.path.basename(p), ts=m[1], actor=m[2].strip(), kind=m[3].strip(),
                                ref=m[4].strip(), body=b))
    return out


def csv_rows(path, cols):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8", newline="") as fh:
        rd = csv.DictReader(fh)
        if rd.fieldnames != cols:
            sys.exit(f"{path}: header {rd.fieldnames} != {cols}")
        return list(rd)


def tags(staging):
    by = defaultdict(list)
    for t in git(staging, "tag", "-l").split():
        m = TAG_RE.match(t)
        if m:
            by[(int(m[1]), m[2])].append((int(m[3]), t))
    return {k: sorted(v) for k, v in by.items()}


def units_at(staging, tag, cls):
    files = [f for f in git(staging, "ls-tree", "-r", "--name-only", tag).split("\n")
             if "_questions_" in f and f.endswith(".json")]
    n, q, cv = 0, 0, Counter()
    for f in files:
        try:
            j = json.loads(git_bytes(staging, "show", f"{tag}:{f}"))
        except Exception:  # noqa
            continue
        n += 1
        q += len(j.get("questions") or [])
        cv[str(j.get("contract_version"))] += 1
    return n, q, cv


def register(record):
    cats = {os.path.basename(p)[:-3] for p in glob.glob(os.path.join(record, "defects", "*.md"))} - {"README"}
    open_ = defaultdict(Counter)
    for f in sorted(glob.glob(os.path.join(record, "defects", "instances", "class-*.csv"))):
        cls = re.search(r"class-([\w-]+)\.csv$", f)[1]
        with open(f, encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                if not r.get("resolved"):
                    open_[cls][r["category"]] += 1
    return cats, open_


def gate_version(tools):
    src = open(os.path.join(tools, "src", "filecheck.py"), encoding="utf-8").read()
    m = re.search(r'GATE_VERSION\s*=\s*"([^"]+)"', src)
    return m[1] if m else "?"


def review_section(record):
    """Review stage (method v1.3): one row per class that has a merge in review/class-N/merge.json."""
    rows = []
    for p in sorted(glob.glob(os.path.join(record, "review", "class-*", "merge.json"))):
        m = json.load(open(p, encoding="utf-8"))
        r = m.get("routes", {})
        pl = sum(c["plants"] for c in m.get("controls", [])); cg = sum(c["caught"] for c in m.get("controls", []))
        rows.append(f"| {m['class']} | `{m['tag']}` | {r.get('kept', 0)} | {r.get('incomplete', 0)} | {r.get('stage3', 0)} | "
                    f"{r.get('stage4', 0)} | {r.get('hold_no_key', 0)} | {cg}/{pl} | {len(m.get('rerun', []))} |")
    if not rows:
        return ["## Review (method v1.4)", "", "No class merged yet.", ""]
    out = ["## Review (method v1.4)", "",
           "| class | tag | kept | incomplete | stage 3 | stage 4 | no key | plants caught | re-runs |",
           "|---|---|---|---|---|---|---|---|---|"] + rows + [""]
    srows = []
    for p in sorted(glob.glob(os.path.join(record, "review", "class-*", "review_state.json"))):
        s = json.load(open(p, encoding="utf-8"))
        c = s.get("counts", {})
        srows.append(f"| {s['class']} | `{s['tag']}` | {len(s['questions'])} | {c.get('kept', 0)} | {c.get('corrected', 0)} | "
                     f"{c.get('incomplete', 0)} | {c.get('held', 0)} | {c.get('kept', 0) + c.get('corrected', 0) + c.get('incomplete', 0)} | {s['generated'][:10]} |")
    if srows:
        out += ["Review state (stage 4, `review/class-N/review_state.json` — one ReviewState per question; tier A = kept + corrected + incomplete, all `machine_verified`):", "",
                "| class | tag | questions | kept | corrected | incomplete | held | tier A | generated |",
                "|---|---|---|---|---|---|---|---|---|"] + srows + [""]
    return out


def digitization_section(staging, T):
    """Maths digitization (design maths_digitization_v2): per book, from the manifests at each class's latest mathtex tag."""
    rows = []
    for (cls, subj), ts in sorted(T.items()):
        if subj != "mathtex":
            continue
        latest = ts[-1][1]
        for f in git(staging, "ls-tree", "-r", "--name-only", latest).split("\n"):
            if not re.fullmatch(rf"class-{cls}/maths/digitized/[^/]+/manifest\.json", f):
                continue
            try:
                m = json.loads(git_bytes(staging, "show", f"{latest}:{f}"))
            except Exception:  # noqa
                continue
            pg = m.get("pages", [])
            st = Counter(p.get("status") for p in pg)
            src = Counter(x.get("source") for x in m.get("figures", []))
            rows.append(f"| {cls} | `{m.get('book')}` | `{latest}` | {len(pg)} | "
                        f"{', '.join(f'{k} {v}' for k, v in sorted(st.items()))} | "
                        f"{', '.join(f'{k} {v}' for k, v in sorted(src.items())) or '—'} | "
                        f"{sum(p.get('unclear', 0) for p in pg)} |")
    if not rows:
        return ["## Maths digitization", "", "No digitization tag yet.", ""]
    return ["## Maths digitization", "", "| class | book | latest tag | pages | by status | figures by source | unclear marks |",
            "|---|---|---|---|---|---|---|"] + rows + [""]


def render(a):
    L = ledgers(a.record)
    as_of = max((e["ts"] for e in L), default="—")
    tools_head = git(a.tools, "log", "-1", "--format=%h %s").strip()
    contracts = sorted(os.path.basename(p) for p in glob.glob(os.path.join(a.tools, "contracts", "*"))
                       if not os.path.basename(p).startswith(("_", ".")) and not os.path.basename(p).lower().startswith("readme"))
    T = tags(a.staging)
    checked = {}
    for e in L:
        # a tag counts as content-checked when a coordinator entry's heading names it with CHECKED,
        # or a `verification` entry's text does
        if e["actor"] != "coordinator":
            continue
        text = e["ref"] if e["kind"] != "verification" else e["ref"] + " " + e["body"]
        for t in re.findall(r"c\d+-\w+-batch-\d+", text):
            if re.search(re.escape(t) + r"[^\n]{0,40}CHECKED", text):
                checked.setdefault(t, e["ts"][:10])
    cats, reg = register(a.record)
    tasks = csv_rows(os.path.join(a.record, "status", "tasks.csv"), ["thread", "task", "state", "reason", "as_of"])
    blocked = csv_rows(os.path.join(a.record, "status", "blocked.csv"), ["on", "item", "state", "note", "as_of"])

    o = ["# STATUS — ViYaMo question bank", "",
         "GENERATED by `viyamo-tools/src/status.py` — **do not hand-edit**; a hand edit is overwritten and",
         "`status.py --check` reports it. Change the record through `record.py`, then regenerate.", "",
         f"As of the newest ledger entry: **{as_of}**", "",
         "## Rules and tools", "",
         f"- viyamo-tools HEAD: `{tools_head}` · gate `filecheck` **{gate_version(a.tools)}**",
         "- contracts (the only authority): " + " · ".join(f"`{c}`" for c in contracts),
         "- threads work only in Devs and git; the coordinator alone writes to Drive, only frozen material (Yash)",
         "", "## Content by class", "",
         "| class-subject | tags | latest tag | units | questions | contract at latest | content-checked tags |",
         "|---|---|---|---|---|---|---|"]
    total_q = 0
    for (cls, subj), ts in sorted(T.items()):
        if subj == "mathtex":
            continue            # digitization tags: their own section below
        latest = ts[-1][1]
        n, q, cv = units_at(a.staging, latest, cls)
        total_q += q
        chk = [t for _, t in ts if t in checked]
        o.append(f"| {cls} {SUBJ.get(subj, subj)} | {len(ts)} | `{latest}` | {n} | {q} | "
                 f"{', '.join(f'{k} ×{v}' for k, v in sorted(cv.items()))} | "
                 f"{', '.join(f'`{t}` ({checked[t]})' for t in chk) or 'none'} |")
    o += ["", f"Questions at the latest tags: **{total_q:,}**. Reviewed: **0** — no review record exists yet.", ""]

    o += digitization_section(a.staging, T)
    o += review_section(a.record)
    o += ["## Defect register (open instances)", "",
          "| class | open | unclassified | by category |", "|---|---|---|---|"]
    tot = Counter()
    for cls in sorted(reg, key=lambda x: (len(x), x)):
        c = reg[cls]
        tot.update(c)
        u = c.get("unclassified", 0)
        flag = " **ALERT: triage today**" if u >= UNCLASSIFIED_ALERT else ""
        rest = ", ".join(f"{k} {v}" for k, v in sorted(c.items()) if k != "unclassified")
        o.append(f"| {cls} | {sum(c.values())} | {u}{flag} | {rest} |")
    o += ["", f"Total open: **{sum(tot.values())}** across {len(cats)} categories. "
          "Unclassified is the last-resort bin: 20 open in one class is triaged the same day.", ""]

    o += ["## Threads", "", "| thread | task | state | reason | as of |", "|---|---|---|---|---|"]
    o += [f"| {r['thread']} | {r['task']} | {r['state']} | {r['reason']} | {r['as_of']} |"
          for r in sorted(tasks, key=lambda r: (r["thread"], r["task"]))]
    for who in ("coordinator", "yash"):
        rows = [r for r in blocked if r["on"] == who and r["state"] == "open"]
        o += ["", f"## Blocked on {'Yash' if who == 'yash' else 'the coordinator'}", ""]
        o += [f"{i}. {r['item']}" + (f" — {r['note']}" if r["note"] else "") + f" *(since {r['as_of']})*"
              for i, r in enumerate(rows, 1)] or ["Nothing open."]
    closed = [r for r in blocked if r["state"] == "closed"]
    o += ["", f"Closed items: {len(closed)} (status/blocked.csv).", "",
          "## Ledgers", "", "See `ledgers/_index.md` (generated by `record.py index`)."]
    kinds = Counter(e["kind"] for e in L)
    o += [f"{len(L)} entries in {len({e['file'] for e in L})} ledgers · " +
          " · ".join(f"{k} {v}" for k, v in sorted(kinds.items())), ""]
    return "\n".join(o) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--record", required=True)
    ap.add_argument("--tools", required=True)
    ap.add_argument("--staging", required=True)
    ap.add_argument("--deep", action="store_true", help="(kept for compatibility; unit counts are always read)")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = render(a)
    path = os.path.join(a.record, "STATUS.md")
    if a.check:
        cur = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        if cur != text:
            print("STATUS.md is STALE or hand-edited — regenerate with status.py")
            sys.exit(1)
        print("STATUS.md is current")
        return
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
