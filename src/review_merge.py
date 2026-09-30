#!/usr/bin/env python3
"""review_merge.py — check one verdict file, or merge a class's reads (review method v1.3, stages 1–2).

    stamp <verdict.json> --actor <thread> --agent <label> [--usage N]   (the thread, after the agent)
    check <verdict.json> --packet <packet.json>
        Every packet item exactly once, verdicts from the fixed set, a reason unless CORRECT, a suggested
        key for WRONG, stem_defect boolean, no extra ids. Exit 0 PASS, 1 FAIL. Threads run it (brief §3).

    seal-a --class N --review <Devs>/_review --sealed <dir> [--read B]
        Coordinator, after read A and BEFORE read B: copies every read-A verdict into <sealed>/c<N>/readA/
        and replaces the Devs copy with a stub {"sealed": sha256}. Read-B agents can then see no read-A
        verdict. merge reads a stub's sealed copy and verifies the hash. (2026-09-22: Classes 6-8 ran
        without this; see the coordinator ledger.)

    merge --class N --review <Devs>/_review --sealed <dir> --record <viyamo-record> [--out <file>]
        Unseals the plants and, per unit and read, scores them:
          RECALL     a plant is caught when its verdict is WRONG, INCOMPLETE or UNSURE. A missed plant is
                     listed for the coordinator (a plant can be accidentally right) and, unless waived in
                     <record>/review/class-N/waivers.json, marks that read of that unit RE-RUN.
          PRECISION  share of real keys marked WRONG; above 10% the read is listed for inspection.
        Then routes every question of the class (plants removed; a planted question's real key has the
        other read only — `single_read`):
          hold_no_key  no stored key (held until authoring)
          stage4       open register instance, a stem_defect from either read, or listed CONTAMINATED by
                       the 2026-09-21 full read → cleaned mechanically or HOLD
          kept         every real read CORRECT and not listed WRONG/UNSURE by the full read
          incomplete   every real read CORRECT or INCOMPLETE, at least one INCOMPLETE, not listed
          stage3       anything else → the verifier (adjudication with a reference)
        Writes the merge (default <record>/review/class-N/merge.json) and prints a summary.
Standard library only.
"""
import argparse, csv, glob, hashlib, json, os, re, sys
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from review_common import VERDICTS

CAUGHT = {"WRONG", "INCOMPLETE", "UNSURE"}
PRECISION_LIMIT = 0.10
FULL_READ = "reports/coordinator/full_read_2026-09-21.md"


def load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def resolve(vf, sealed_dir=None):
    """A verdict, following a seal-a stub to its sealed copy (hash verified)."""
    v = load(vf)
    if set(v) == {"sealed", "path"}:
        if not sealed_dir:
            raise SystemExit(f"{vf} is sealed; pass --sealed")
        sp = os.path.join(sealed_dir, v["path"])
        body = open(sp, "rb").read()
        if hashlib.sha256(body).hexdigest() != v["sealed"]:
            raise SystemExit(f"{sp}: hash does not match the stub in {vf}")
        return json.loads(body)
    return v


def check(vf, pf, sealed_dir=None):
    errs = []
    try:
        v, pk = resolve(vf, sealed_dir), load(pf)
    except Exception as e:  # noqa
        return [f"unreadable: {e}"]
    want = [it["id"] for it in pk["items"]]
    if v.get("unit") != pk["unit"]:
        errs.append(f"unit {v.get('unit')!r} != packet {pk['unit']!r}")
    if v.get("read") != pk["read"]:
        errs.append(f"read {v.get('read')!r} != packet {pk['read']!r}")
    items = v.get("items")
    if not isinstance(items, list):
        return errs + ["items missing"]
    got = [it.get("id") for it in items]
    dup = [i for i, n in Counter(got).items() if n > 1]
    miss, extra = sorted(set(want) - set(got)), sorted(set(got) - set(want))
    if dup: errs.append(f"duplicated ids: {dup[:5]}")
    if miss: errs.append(f"{len(miss)} packet items without a verdict: {miss[:5]}")
    if extra: errs.append(f"ids not in the packet: {extra[:5]}")
    for it in items:
        i, vd = it.get("id"), it.get("verdict")
        if vd not in VERDICTS: errs.append(f"{i}: verdict {vd!r}")
        if vd != "CORRECT" and not str(it.get("reason") or "").strip(): errs.append(f"{i}: no reason")
        if vd == "WRONG" and not str(it.get("suggested") or "").strip(): errs.append(f"{i}: WRONG without suggested")
        if not isinstance(it.get("stem_defect", False), bool): errs.append(f"{i}: stem_defect not boolean")
    for k in ("actor", "agent"):
        if not v.get(k): errs.append(f"{k} missing (the thread adds it)")
    return errs


def full_read_lists(record, cls):
    """{'WRONG': set(ids), 'UNSURE': set, 'CONTAMINATED': set} for one class, from the 2026-09-21 report."""
    text = open(os.path.join(record, FULL_READ), encoding="utf-8").read()
    out = defaultdict(set)
    sec = None
    for block in re.split(r"\n(?=[A-Z][A-Z ]+[ (])", text):
        head = block.split("\n", 1)[0]
        m = re.match(r"(WRONG|UNSURE|CONTAMINATED)\b", head)
        if not m:
            continue
        sec = m[1]
        # a class's list runs from "- C<N>:" to the next "- C" line
        for part in re.split(r"\n- (?=C\d:)", "\n" + block):
            mc = re.match(r"C(\d):(.*)", part.strip(), re.S)
            if not mc or int(mc[1]) != cls:
                continue
            body = re.sub(r"\([^)]*\)", " ", mc[2])  # "(q051's answer run in)" names another item; not listed
            last = None
            for tok in re.finditer(r"(\d{2})-(s\d+|x\d+)-q(\d{3}[a-z]?)|(?<![\w-])q(\d{3}[a-z]?)", body):
                if tok[1]:
                    last = (tok[1], tok[2])
                    out[sec].add(f"sci-{cls}-{tok[1]}-{tok[2]}-q{tok[3]}")
                elif last:
                    out[sec].add(f"sci-{cls}-{last[0]}-{last[1]}-q{tok[4]}")
    return out


def register_open(record, cls):
    p = os.path.join(record, "defects", "instances", f"class-{cls}.csv")
    if not os.path.exists(p):
        return {}
    out = defaultdict(list)
    with open(p, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if not r.get("resolved"):
                out[r["question_id"]].append(r["category"])
    return out


def merge(a):
    cls = a.cls
    sealed = load(os.path.join(a.sealed, f"plants_c{cls}.json"))
    plants = {(p["read"], p["id"]): p for p in sealed["plants"]}
    base = os.path.join(a.review, f"c{cls}")
    wv = os.path.join(a.record, "review", f"class-{cls}", "waivers.json")
    waivers = set(load(wv)) if os.path.exists(wv) else set()  # list of "A:id", or {"A:id": reason}
    fr = full_read_lists(a.record, cls)
    reg = register_open(a.record, cls)
    verdicts = {"A": {}, "B": {}}
    units = set()
    problems = []
    for side in "AB":
        for pf in sorted(glob.glob(os.path.join(base, f"read{side}", "*.json"))):
            un = os.path.basename(pf)[:-5]
            units.add(un)
            vf = os.path.join(base, f"read{side}", "verdicts", f"{un}.json")
            if not os.path.exists(vf):
                problems.append(f"read {side} {un}: no verdict file")
                continue
            e = check(vf, pf, a.sealed)
            if e:
                problems.append(f"read {side} {un}: check FAIL — {e[0]}")
                continue
            for it in resolve(vf, a.sealed)["items"]:
                verdicts[side][it["id"]] = dict(it, unit=un)
    if problems:
        print("\n".join(problems))
        sys.exit("merge refused: every read of every unit must pass check first")
    # controls
    ctrl = defaultdict(lambda: {"plants": 0, "caught": 0, "missed": [], "real": 0, "real_wrong": 0})
    for side in "AB":
        for i, it in verdicts[side].items():
            c = ctrl[(side, it["unit"])]
            if (side, i) in plants:
                c["plants"] += 1
                if it["verdict"] in CAUGHT:
                    c["caught"] += 1
                else:
                    p = plants[(side, i)]
                    c["missed"].append({"id": i, "kind": p["kind"], "planted_key": p["planted_key"],
                                        "real_key": p["real_key"], "reason": it.get("reason", ""),
                                        "waived": f"{side}:{i}" in waivers})
            else:
                c["real"] += 1
                c["real_wrong"] += it["verdict"] == "WRONG"
    rerun, inspect = [], []
    for (side, un), c in sorted(ctrl.items()):
        c["precision_wrong_share"] = round(c["real_wrong"] / c["real"], 3) if c["real"] else 0
        if any(not m["waived"] for m in c["missed"]):
            rerun.append(f"{side}:{un}")
        if c["precision_wrong_share"] > PRECISION_LIMIT:
            inspect.append(f"{side}:{un}")
    # routing
    rows, route = [], Counter()
    ids = sorted(set(verdicts["A"]) | set(verdicts["B"]))
    for i in ids:
        real = {s: verdicts[s][i] for s in "AB" if i in verdicts[s] and (s, i) not in plants}
        rv = [r["verdict"] for r in real.values()]
        listed = [k for k in ("WRONG", "UNSURE") if i in fr.get(k, set())]
        if reg.get(i) or any(r.get("stem_defect") for r in real.values()) or i in fr.get("CONTAMINATED", set()):
            rt = "stage4"
        elif not rv:
            rt = "stage3"  # cannot happen with disjoint plants; kept as a guard
        elif all(v == "CORRECT" for v in rv) and not listed:
            rt = "kept"
        elif all(v in ("CORRECT", "INCOMPLETE") for v in rv) and "INCOMPLETE" in rv and not listed:
            rt = "incomplete"
        else:
            rt = "stage3"
        route[rt] += 1
        rows.append({"id": i, "unit": (real.get("A") or real.get("B") or {}).get("unit"), "route": rt,
                     "single_read": len(real) == 1,
                     "A": {k: real["A"].get(k) for k in ("verdict", "reason", "suggested", "stem_defect")} if "A" in real else None,
                     "B": {k: real["B"].get(k) for k in ("verdict", "reason", "suggested", "stem_defect")} if "B" in real else None,
                     "full_read": listed + (["CONTAMINATED"] if i in fr.get("CONTAMINATED", set()) else []),
                     "register": reg.get(i, [])})
    for i in sealed["not_read_no_key"]:
        rows.append({"id": i, "route": "hold_no_key", "register": reg.get(i, [])})
        route["hold_no_key"] += 1
    out = {"class": cls, "tag": sealed["tag"], "seed": sealed["seed"], "method": "review method v1.3",
           "routes": dict(route), "rerun": rerun, "inspect_precision": inspect,
           "controls": [dict(read=s, unit=u, **c) for (s, u), c in sorted(ctrl.items())], "questions": rows}
    op = a.out or os.path.join(a.record, "review", f"class-{cls}", "merge.json")
    os.makedirs(os.path.dirname(op), exist_ok=True)
    with open(op, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    tp = sum(c["plants"] for c in ctrl.values()); tc = sum(c["caught"] for c in ctrl.values())
    print(f"class {cls}: routes {dict(route)} · plants caught {tc}/{tp} · re-run {len(rerun)} · inspect {len(inspect)}")
    print(f"wrote {op}")
    return 1 if rerun else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    c = sp.add_parser("check"); c.add_argument("verdict"); c.add_argument("--packet", required=True)
    st = sp.add_parser("stamp", help="the thread records who ran the read and what it cost")
    st.add_argument("verdict"); st.add_argument("--actor", required=True); st.add_argument("--agent", required=True)
    st.add_argument("--usage", type=int, help="the agent's reported total tokens; omit if not shown")
    m = sp.add_parser("merge")
    m.add_argument("--class", dest="cls", type=int, required=True)
    m.add_argument("--review", required=True); m.add_argument("--sealed", required=True)
    m.add_argument("--record", required=True); m.add_argument("--out")
    sa = sp.add_parser("seal-a")
    sa.add_argument("--class", dest="cls", type=int, required=True)
    sa.add_argument("--review", required=True); sa.add_argument("--sealed", required=True)
    sa.add_argument("--read", choices=["A", "B"], default="A", help="B: before a re-read of read A, so it cannot see read B")
    a = ap.parse_args()
    if a.cmd == "seal-a":
        src = os.path.join(a.review, f"c{a.cls}", f"read{a.read}", "verdicts")
        dst = os.path.join(a.sealed, f"c{a.cls}", f"read{a.read}")
        os.makedirs(dst, exist_ok=True)
        n = 0
        for vf in sorted(glob.glob(os.path.join(src, "*.json"))):
            v = load(vf)
            if set(v) == {"sealed", "path"}:
                continue
            body = open(vf, "rb").read()
            rel = os.path.join(f"c{a.cls}", f"read{a.read}", os.path.basename(vf))
            with open(os.path.join(a.sealed, rel), "wb") as fh:
                fh.write(body)
            with open(vf, "w", encoding="utf-8", newline="\n") as fh:
                json.dump({"sealed": hashlib.sha256(body).hexdigest(), "path": rel}, fh); fh.write("\n")
            n += 1
        print(f"sealed {n} read-{a.read} verdicts of class {a.cls} into {dst}"); return
    if a.cmd == "stamp":
        v = load(a.verdict)
        v.update(actor=a.actor, agent=a.agent, usage=a.usage)
        with open(a.verdict, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(v, fh, ensure_ascii=False, indent=1); fh.write("\n")
        print(f"stamped {a.verdict}"); return
    if a.cmd == "check":
        e = check(a.verdict, a.packet)
        print("PASS" if not e else "FAIL\n  " + "\n  ".join(e))
        sys.exit(1 if e else 0)
    sys.exit(merge(a))


if __name__ == "__main__":
    main()
