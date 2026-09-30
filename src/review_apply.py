#!/usr/bin/env python3
"""review_apply.py — stage 4 of review method v1.4: the REVIEW STATE of a class bank (runtime schema, ReviewState).

    apply --class N --record <viyamo-record> --review <Devs>/_review [--out <file>] [--hold <file>]
    check --class N --record <viyamo-record> --review <Devs>/_review

`check` reconciles the written state against its inputs and exits 1 on any mismatch: every question of the merge has
exactly one state; every verifier verdict maps to the outcome its rule gives; every corrected state carries a
reference and an answer; every route maps only to the outcomes it may. Run it after every apply.

Reads <record>/review/class-N/merge.json (stages 1-2: the reads and the routes) and <Devs>/_review/cN/verify/verdicts/
(stage 3: the verifier's adjudication) and writes ONE ReviewState per question of the class to
<record>/review/class-N/review_state.json. Unit files are never touched (runtime_schema QueryRules.never_overwrite):
the importer and the generator read this file beside the tagged bank.

Outcome rules (review method v1.4, coordinator 2026-09-23):
  route kept          -> kept        state machine_verified   decided_by the two reads (or the one real read)
  route incomplete    -> incomplete  state machine_verified   key stays, marked for the authoring pass
  route hold_no_key   -> held        no stored key
  route stage3        -> the verifier's verdict:
        KEEP -> kept (machine_verified, decided_by the verifier agent, reference kept when given)
        CORRECT -> corrected (machine_verified, reference REQUIRED, `correction` carries the new key)
        HOLD -> held; STEM_DEFECT (stem or both task) -> held; STEM_OK on a stem-only task -> kept when both reads
        called the key CORRECT, else held; no verdict on file -> held ("no verdict")
  route stage4        -> the verifier's verdict when it took the item as a stem/both packet (same rules as stage3;
                         a stem-only STEM_OK leaves the key to the reads), else held (nobody adjudicated it)
Extra holds come from --hold <file> (default <record>/review/holds.json when present): JSON list of {"id":…,"reason":…}
(coordinator cleanups, e.g. an option swallowed into another at extraction). Standard library only.
"""
import argparse, datetime, glob, json, os, sys
from collections import Counter


def load_verdicts(review, cls):
    out = {}
    for f in sorted(glob.glob(os.path.join(review, f"c{cls}", "verify", "verdicts", "*.json"))):
        v = json.load(open(f, encoding="utf-8"))
        agent = f"verifier-science/c{cls}/{v.get('unit')}"
        for it in v.get("items", []):
            out[it["id"]] = (it, agent)
    packets = {}
    for f in sorted(glob.glob(os.path.join(review, f"c{cls}", "verify", "*.json"))):
        p = json.load(open(f, encoding="utf-8"))
        for it in p.get("items", []):
            packets[it["id"]] = it
    return out, packets


def reads_of(q):
    return [r for r in (q.get("A"), q.get("B")) if r]


def state_for(q, verdicts, packets, now, extra):
    qid = q["id"]
    base = {"question_id": qid, "unit": q.get("unit"), "at": now, "route": q["route"]}
    if qid in extra:
        return dict(base, outcome="held", decided_by="coordinator", reason=extra[qid])
    rt = q["route"]
    reads = reads_of(q)
    who = "reads A+B" if len(reads) == 2 else "read A" if q.get("A") else "read B"
    if rt == "kept":
        return dict(base, outcome="kept", state="machine_verified", decided_by=who)
    if rt == "incomplete":
        return dict(base, outcome="incomplete", state="machine_verified", decided_by=who,
                    reason="; ".join(r.get("reason") or "" for r in reads if r.get("verdict") == "INCOMPLETE")[:300])
    if rt == "hold_no_key":
        return dict(base, outcome="held", decided_by="merge", reason="no stored key")
    if rt == "stage4" and qid not in verdicts:
        causes = []
        if any(r.get("stem_defect") for r in reads): causes.append("stem defect (a read)")
        if q.get("register"): causes.append("register: " + ", ".join(q["register"]))
        if "CONTAMINATED" in q.get("full_read", []): causes.append("contaminated (full read)")
        vs = "/".join(r.get("verdict") or "-" for r in reads)
        return dict(base, outcome="held", decided_by="merge", reason=f"stage 4: {'; '.join(causes)}; reads {vs}")
    # stage 3 (key packets) and the stage-4 items the verifier took as stem/both packets
    if qid not in verdicts:
        return dict(base, outcome="held", decided_by="coordinator", reason="stage 3: no verdict on file")
    it, agent = verdicts[qid]
    task = packets.get(qid, {}).get("task")
    o, so = it.get("outcome"), it.get("stem_outcome")
    ref = it.get("reference")
    if task == "both" and so == "STEM_DEFECT" or task == "stem" and o == "STEM_DEFECT":
        return dict(base, outcome="held", decided_by=agent, reason="stem defect: " + (it.get("stem_reason") or it.get("reason") or "")[:300])
    if task == "stem":  # STEM_OK: the key was never doubted by the verifier; the reads decide it
        if reads and all(r.get("verdict") == "CORRECT" for r in reads):
            return dict(base, outcome="kept", state="machine_verified", decided_by=f"{who}; stem {agent}")
        return dict(base, outcome="held", decided_by=agent, reason="stem ok; key not accepted by the reads")
    if o == "KEEP":
        return dict(base, outcome="kept", state="machine_verified", decided_by=agent, reference=ref)
    if o == "CORRECT":
        if not ref:
            return dict(base, outcome="held", decided_by="coordinator", reason="CORRECT without a reference")
        return dict(base, outcome="corrected", state="machine_verified", decided_by=agent, reference=ref,
                    correction={"answer": it.get("new_key"), "option_id": it.get("new_option_id")},
                    reason=(it.get("reason") or "")[:300], checked_by="coordinator 2026-09-23")
    return dict(base, outcome="held", decided_by=agent, reason=(it.get("reason") or "")[:300])


ALLOWED = {"kept": {"kept"}, "incomplete": {"incomplete"}, "hold_no_key": {"held"}, "stage3": {"kept", "corrected", "held"},
           "stage4": {"kept", "corrected", "held"}, "extra": {"held"}}


def expected_from_verdict(it, task, reads):
    """The outcome a verifier verdict must have produced (the same rules as state_for, written independently)."""
    o, so = it.get("outcome"), it.get("stem_outcome")
    if (task == "both" and so == "STEM_DEFECT") or (task == "stem" and o == "STEM_DEFECT"):
        return "held"
    if task == "stem":
        return "kept" if reads and all(r.get("verdict") == "CORRECT" for r in reads) else "held"
    return {"KEEP": "kept", "CORRECT": "corrected" if it.get("reference") else "held"}.get(o, "held")


def check(a, m, verdicts, packets, extra):
    op = a.out or os.path.join(a.record, "review", f"class-{a.cls}", "review_state.json")
    s = json.load(open(op, encoding="utf-8"))
    errs = []
    byq = {}
    for x in s["questions"]:
        if x["question_id"] in byq: errs.append(f"duplicate state {x['question_id']}")
        byq[x["question_id"]] = x
    if s.get("tag") != m["tag"]: errs.append(f"tag {s.get('tag')} != merge {m['tag']}")
    for q in m["questions"]:
        x = byq.get(q["id"])
        if not x: errs.append(f"no state for {q['id']}"); continue
        if x["outcome"] not in ALLOWED[q["route"]]: errs.append(f"{q['id']}: route {q['route']} -> {x['outcome']}")
        if q["id"] in extra and x["outcome"] != "held": errs.append(f"{q['id']}: coordinator hold not applied")
    for qid, (it, _) in verdicts.items():
        x = byq.get(qid)
        if not x: errs.append(f"verdict for {qid} but no state"); continue
        if qid in extra: continue
        q = next((q for q in m["questions"] if q["id"] == qid), None)
        exp = expected_from_verdict(it, packets.get(qid, {}).get("task"), reads_of(q) if q else [])
        if x["outcome"] != exp: errs.append(f"{qid}: verdict {it.get('outcome')}/{it.get('stem_outcome')} expects {exp}, state {x['outcome']}")
    for x in s["questions"]:
        if x["outcome"] == "corrected" and not (x.get("reference") and x.get("correction", {}).get("answer")):
            errs.append(f"{x['question_id']}: corrected without reference/answer")
        if x["outcome"] in ("kept", "corrected", "incomplete") and x.get("state") != "machine_verified":
            errs.append(f"{x['question_id']}: tier-A outcome without state")
        if x["outcome"] == "held" and x.get("state"): errs.append(f"{x['question_id']}: held carries a state")
    counts = Counter(x["outcome"] for x in s["questions"])
    if dict(counts) != s.get("counts"): errs.append("counts header disagrees with the states")
    for e in errs[:40]: print("FAIL", e)
    print(f"class {a.cls}: {len(s['questions'])} states, {len(verdicts)} verdicts reconciled, {len(extra)} coordinator holds — "
          f"{'FAIL ' + str(len(errs)) + ' errors' if errs else 'PASS'}")
    return 1 if errs else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    for name in ("apply", "check"):
        a_ = sp.add_parser(name)
        a_.add_argument("--class", dest="cls", type=int, required=True); a_.add_argument("--record", required=True)
        a_.add_argument("--review", required=True); a_.add_argument("--out"); a_.add_argument("--hold")
    a = ap.parse_args()
    m = json.load(open(os.path.join(a.record, "review", f"class-{a.cls}", "merge.json"), encoding="utf-8"))
    verdicts, packets = load_verdicts(a.review, a.cls)
    extra = {}
    hold = a.hold or os.path.join(a.record, "review", "holds.json")
    if os.path.exists(hold):
        for h in json.load(open(hold, encoding="utf-8")):
            if h["id"].startswith(f"sci-{a.cls}-"): extra[h["id"]] = h["reason"]
    if a.cmd == "check":
        sys.exit(check(a, m, verdicts, packets, extra))
    now = datetime.datetime.now().astimezone().isoformat(timespec="minutes")
    states = [state_for(q, verdicts, packets, now, extra) for q in m["questions"]]
    seen = {s["question_id"] for s in states}
    for qid, reason in extra.items():
        if qid not in seen:
            states.append({"question_id": qid, "at": now, "route": "extra", "outcome": "held", "decided_by": "coordinator", "reason": reason})
    counts = Counter(s["outcome"] for s in states)
    out = {"class": a.cls, "tag": m["tag"], "method": "review method v1.4, stage 4", "generated": now,
           "source": {"merge": f"review/class-{a.cls}/merge.json", "verdicts": f"_review/c{a.cls}/verify/verdicts/"},
           "counts": dict(counts), "questions": states}
    op = a.out or os.path.join(a.record, "review", f"class-{a.cls}", "review_state.json")
    json.dump(out, open(op, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    tier_a = counts["kept"] + counts["corrected"] + counts["incomplete"]
    print(f"class {a.cls} @ {m['tag']}: {len(states)} questions · kept {counts['kept']} · corrected {counts['corrected']} · "
          f"incomplete {counts['incomplete']} · held {counts['held']} · on-paper (tier A) {tier_a} → {op}")


if __name__ == "__main__":
    main()
