#!/usr/bin/env python3
"""pending.py — what is waiting on a defect category, per class, from the LIVE record.

The register (viyamo-record/defects/) is the live record of where a question's defect sits.
A unit file is immutable once tagged, so its pending_category says where the question stood
at EXTRACTION and never changes. Counting from unit files alone would never go down after a
triage. So:

    open instances   = rows in defects/instances/class-N.csv with no `resolved` date
    cross-check      = unit files, to find questions flagged in a file but never registered

Alerts:
    unclassified open >= 20 in any ONE class   ALERT — triage the same day (Yash, 2026-09-21)
    any other category open >= 10 in total    note — the promotion threshold may be met

Usage:
    python3 pending.py --register <viyamo-record>/defects [--units DIR ...]
Exit 0 = no alert · 1 = an alert or an integrity error · 2 = the register could not be read.
Standard library only.
"""
import argparse, csv, glob, json, os, re, sys
from collections import Counter, defaultdict

UNCLASSIFIED_ALERT_PER_CLASS = 20
CATEGORY_NOTE = 10
COLUMNS = ["filed", "category", "question_id", "location", "description", "nearest",
           "filed_by", "route", "moved_to", "resolved", "resolved_by"]
ROUTES = {"", "moved", "founded", "closed", "resolved"}
QID = re.compile(r"^[a-z]{2,4}-(\d{1,2}|puc-[12])-\d{2}-[sx]\d+-q\d{3}[a-z]?$")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--register", required=True, help="viyamo-record/defects directory")
    ap.add_argument("--units", nargs="*", default=[], help="unit files or directories (recursive)")
    a = ap.parse_args()

    cats = {os.path.basename(p)[:-3] for p in glob.glob(os.path.join(a.register, "*.md"))} - {"README"}
    files = sorted(glob.glob(os.path.join(a.register, "instances", "class-*.csv")))
    if not cats or not files:
        print(f"register unreadable or empty at {a.register}: {len(cats)} categories, "
              f"{len(files)} instance files — a zero here would mean nothing")
        sys.exit(2)

    errors, rows_by_q = [], defaultdict(list)
    open_ = defaultdict(Counter)           # class -> category -> open count
    for f in files:
        cls = re.search(r"class-([\w-]+)\.csv$", f).group(1)
        with open(f, encoding="utf-8", newline="") as fh:
            rd = csv.DictReader(fh)
            if rd.fieldnames != COLUMNS:
                errors.append(f"{os.path.basename(f)}: header {rd.fieldnames} != {COLUMNS}")
                continue
            for n, r in enumerate(rd, start=2):
                where = f"{os.path.basename(f)}:{n}"
                if r["category"] not in cats:
                    errors.append(f"{where}: category {r['category']!r} has no file in the register")
                if r["question_id"] and not QID.match(r["question_id"]):
                    errors.append(f"{where}: question_id {r['question_id']!r} is not a valid id")
                if not r["question_id"] and not r["location"]:
                    errors.append(f"{where}: neither question_id nor location — the instance points at nothing")
                if r["route"] not in ROUTES:
                    errors.append(f"{where}: route {r['route']!r} not in {sorted(ROUTES - {''})}")
                if bool(r["route"]) != bool(r["resolved"]):
                    errors.append(f"{where}: route and resolved must be set together")
                if r["route"] == "moved" and r["moved_to"] not in cats:
                    errors.append(f"{where}: moved to {r['moved_to']!r}, which has no file in the register")
                if r["category"] == "unclassified":
                    near = re.match(r"\s*category:([a-z0-9-]+)", r["nearest"] or "")
                    if not r["nearest"].strip():
                        errors.append(f"{where}: unclassified instance with no `nearest`")
                    elif (r["nearest"].strip().startswith("category:") and not near) or (near and near.group(1) not in cats):
                        errors.append(f"{where}: nearest {r['nearest']!r} names no category in the register")
                if r["question_id"]:
                    rows_by_q[r["question_id"]].append(r)
                if not r["resolved"]:
                    open_[cls][r["category"]] += 1

    # cross-check unit files: a question flagged in a file must be in the register
    unregistered, units_read = [], 0
    for arg in a.units:
        paths = sorted(glob.glob(os.path.join(arg, "**", "*_questions_*.json"), recursive=True)) \
            if os.path.isdir(arg) else [arg]
        for p in paths:
            try:
                u = json.load(open(p, encoding="utf-8"))
            except Exception as e:  # noqa
                errors.append(f"unreadable unit {p}: {e}"); continue
            units_read += 1
            for q in u.get("questions", []):
                c = q.get("pending_category")
                if c and not any(r["category"] == c for r in rows_by_q.get(q.get("id"), [])):
                    unregistered.append(f"{q.get('id')} ({c})")
                for fl in q.get("source_flags") or []:
                    m = re.match(r"\s*nearest:\s*category:([a-z0-9-]+)\s+—", str(fl.get("suggested") or ""))
                    if m and m.group(1) not in cats:
                        errors.append(f"{q.get('id')}: nearest names category {m.group(1)!r}, not in the register")

    total = sum(sum(c.values()) for c in open_.values())
    print(f"register: {len(cats)} categories, {len(files)} class files · open instances {total}"
          + (f" · units cross-checked {units_read}" if a.units else " · no units cross-checked"))
    alert = False
    for cls in sorted(open_, key=lambda x: (len(x), x)):
        u_ = open_[cls].get("unclassified", 0)
        flag = "  ALERT: triage today" if u_ >= UNCLASSIFIED_ALERT_PER_CLASS else ""
        alert |= bool(flag)
        detail = ", ".join(f"{k}:{v}" for k, v in sorted(open_[cls].items()) if k != "unclassified")
        print(f"  class {cls:6s} unclassified {u_:3d}{flag}   {detail}")
    tot = Counter()
    for c in open_.values():
        tot.update(c)
    for k, v in sorted(tot.items()):
        if k != "unclassified" and v >= CATEGORY_NOTE:
            print(f"  note: {k} has {v} open — the promotion threshold may be met")
    for x in unregistered:
        print(f"  UNREGISTERED: {x} carries pending_category in its file but has no register row")
    for e in errors:
        print(f"  ERROR: {e}")
    sys.exit(1 if (alert or errors or unregistered) else 0)


if __name__ == "__main__":
    main()
