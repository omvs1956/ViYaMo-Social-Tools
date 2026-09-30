#!/usr/bin/env python3
"""estimate.py — token estimate for the review reads (review method v1.3, stage −1).

Model (every constant is an ASSUMPTION until calibrated; the report says which):
  agent  (one per unit per read; it reads its packet file and writes its verdict file, AGENT_TURNS
         turns): input = T×(BASE+BRIEF) + (T−1)×packet + (T−2)×output ; output = items × OUT_PER_ITEM
  thread (orchestration, per class): agents are launched BATCH at a time in one turn; each batch costs
         TURNS_PER_BATCH turns, each re-reading the thread context CTX (+ GROW per unit done)
  verifier (stage 3): stage3 questions × ADJ_PER_Q
Packet tokens are MEASURED (characters/4 of the packet files). Calibration: after the first unit of a
class, pass --actual <unit>=<tokens> (the agent's reported total); the agent component is scaled by
actual/estimated for that unit and the scale is saved to --calibration.

Usage:
    python3 estimate.py --review <Devs>/_review [--class 6 ...] [--stage3 300]
        [--calibration <record>/review/estimate_calibration.json] [--actual sci-6-01=23000]
Standard library only.
"""
import argparse, glob, json, math, os

D = dict(AGENT_TURNS=3, BASE=15000, OUT_PER_ITEM=120, BATCH=6, TURNS_PER_BATCH=2, CTX=30000, GROW=1500, ADJ_PER_Q=12000)
BRIEF_TOK = 1100


def tok(path):
    return os.path.getsize(path) // 4


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--review", required=True)
    ap.add_argument("--class", dest="classes", type=int, action="append")
    ap.add_argument("--stage3", type=int, default=None, help="expected stage-3 questions (default 8%% of items)")
    ap.add_argument("--calibration")
    ap.add_argument("--actual", action="append", default=[])
    a = ap.parse_args()
    cal = json.load(open(a.calibration)) if a.calibration and os.path.exists(a.calibration) else {}
    scale = cal.get("agent_scale", 1.0)
    classes = a.classes or sorted(int(os.path.basename(d)[1:]) for d in glob.glob(os.path.join(a.review, "c[0-9]*")))
    grand = 0
    for c in classes:
        units = sorted(glob.glob(os.path.join(a.review, f"c{c}", "readA", "*.json")))
        per = {}
        for side in "AB":
            for pf in sorted(glob.glob(os.path.join(a.review, f"c{c}", f"read{side}", "*.json"))):
                n = len(json.load(open(pf, encoding="utf-8"))["items"])
                T, out = D["AGENT_TURNS"], n * D["OUT_PER_ITEM"]
                per[(side, os.path.basename(pf)[:-5])] = (T * (D["BASE"] + BRIEF_TOK) + (T - 1) * tok(pf) + (T - 2) * out, out)
        for s in a.actual:
            un, v = s.split("=")
            if ("A", un) in per:
                est = sum(per[("A", un)])
                scale = int(v) / est
                cal = {"agent_scale": round(scale, 3), "from": f"{un} actual {v} vs estimated {est}"}
                if a.calibration:
                    json.dump(cal, open(a.calibration, "w"), indent=1)
        ag_in = sum(i for i, _ in per.values()) * scale
        ag_out = sum(o for _, o in per.values()) * scale
        nu = len(units)
        turns = 2 * math.ceil(nu / D["BATCH"]) * D["TURNS_PER_BATCH"] + 4
        th = sum(D["CTX"] + D["GROW"] * min(nu * 2, t * D["BATCH"] // D["TURNS_PER_BATCH"]) for t in range(turns))
        items = sum(n for (s, _), (_, o) in per.items() if s == "A" for n in [o // D["OUT_PER_ITEM"]])
        s3 = a.stage3 if a.stage3 is not None else round(0.08 * items)
        ver = s3 * D["ADJ_PER_Q"]
        tot = ag_in + ag_out + th + ver
        grand += tot
        print(f"class {c}: units {nu} · items {items} · agents in {ag_in/1e6:.2f}M out {ag_out/1e6:.2f}M · "
              f"thread {th/1e6:.2f}M ({turns} turns) · verifier {ver/1e6:.2f}M ({s3} q) · total {tot/1e6:.2f}M")
    status = f"calibrated ({cal.get('from')})" if cal else "UNCALIBRATED — constants are assumptions"
    print(f"all: {grand/1e6:.1f}M tokens · {status}")


if __name__ == "__main__":
    main()
