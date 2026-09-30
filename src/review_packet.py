#!/usr/bin/env python3
"""review_packet.py — build the read-A and read-B packets for one class, with sealed plants.

Review method v1.3, stages 0 and 1 (viyamo-record/design/review_method_v1_DRAFT_science_classes_6-9.md).

For every unit at the class's checked tag it writes
    <out>/c<N>/readA/<unit>.json   and   <out>/c<N>/readB/<unit>.json
Each packet holds every ANSWERED question of the unit: stem, options, stored key, marks, and a note
when the question has a figure the reader cannot see. Questions with no stored key are not read
(they are HOLD until authoring) and are listed in the sealed file.

PLANTS. In each read, ~5% of a unit's answered questions (at least 1) carry a realistic wrong key in
place of the stored one. The two reads' plant sets are DISJOINT, so every question's real key is read
at least once; a question planted in one read has its real key read by the other read only
(`single_read` in the merge). Kinds:
    option (mcq, true_false)  another option of the same question
    match                     the right-hand sides of two pairs swapped
    numeric                   one part ×10 (unit slip) or +1 in the last digit (arithmetic slip)
    text ≤ 60 chars           the key of another question of the same type in the unit
    text > 60 chars           one word swapped for its opposite (increases↔decreases, attract↔repel,
                              solid↔liquid …) so the answer states something FALSE (v2, 2026-09-22).
                              v1 replaced a sentence with another answer's sentence; a true, on-topic
                              sentence is not a wrong key, so v1 recall on long text was unreliable.
The plant map goes to <sealed>/plants_c<N>.json — NOT under <out>; the threads never see it. Its
sha256 is printed so the ledger can commit to it before any read starts.

Usage:
    python3 review_packet.py --staging <viyamo-staging> --class 6 --seed 20260922 \
        --out <Devs>/_review --sealed <coordinator-only dir>
Standard library only. Same (tag, seed) → byte-identical packets.
"""
import argparse, hashlib, json, os, random, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from review_common import TAGS, units_at, unit_name, options_of, has_key, render_key, match_sides

RATE = 0.05
SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")
PLANT_VERSION = 2
OPPOSITES = [("increases", "decreases"), ("increase", "decrease"), ("increased", "decreased"),
             ("more", "less"), ("higher", "lower"), ("high", "low"), ("larger", "smaller"), ("large", "small"),
             ("attract", "repel"), ("attracts", "repels"), ("attraction", "repulsion"),
             ("solid", "liquid"), ("acid", "base"), ("acidic", "basic"), ("acids", "bases"),
             ("positive", "negative"), ("hot", "cold"), ("heat", "cool"), ("absorbs", "releases"),
             ("absorb", "release"), ("conductor", "insulator"), ("conductors", "insulators"),
             ("physical", "chemical"), ("renewable", "non-renewable"), ("living", "non-living"),
             ("north", "south"), ("east", "west"), ("inhale", "exhale"), ("oxygen", "carbon dioxide"),
             ("expands", "contracts"), ("expand", "contract"), ("always", "never"), ("can", "cannot"),
             ("faster", "slower"), ("before", "after"), ("maximum", "minimum"), ("male", "female"),
             ("upward", "downward"), ("inside", "outside"), ("gain", "lose"), ("gains", "loses")]
_OPP = {}
for _a, _b in OPPOSITES:
    _OPP[_a] = _b; _OPP[_b] = _a
_OPP_RE = re.compile(r"\b(" + "|".join(sorted(map(re.escape, _OPP), key=len, reverse=True)) + r")\b", re.I)


def swap_case(src, dst):
    return dst.upper() if src.isupper() else (dst[0].upper() + dst[1:] if src[0].isupper() else dst)


def item(q, key_text):
    it = {"id": q["id"], "type": q["type"], "stem": q.get("text") or ""}
    if q.get("marks") is not None:
        it["marks"] = q["marks"]
    if options_of(q):
        it["options"] = [{"id": o.get("id"), "text": o.get("text", "")} for o in options_of(q)]
    left, right = match_sides(q)
    if left or right:
        it["match"] = {"left": left, "right": right}
    if q.get("assets") or q.get("stimulus_ref") or q.get("stimulus"):
        it["note"] = "this question has a figure, table or passage you cannot see — judge on the text; UNSURE if the key depends on it"
    it["key"] = key_text
    return it


def make_plant(q, unit_qs, rng):
    """(planted answer dict, kind) or None when no realistic plant exists for this question."""
    a = json.loads(json.dumps(q.get("answer") or {}))
    k = a.get("kind")
    if k == "option":
        others = [o.get("id") for o in options_of(q) if o.get("id") != a.get("option_id")]
        if not others:
            return None
        a["option_id"] = rng.choice(others)
        return a, "option"
    if k == "match" and len(a.get("pairs") or []) >= 2:
        i, j = rng.sample(range(len(a["pairs"])), 2)
        if a["pairs"][i].get("right") == a["pairs"][j].get("right"):
            return None
        a["pairs"][i]["right"], a["pairs"][j]["right"] = a["pairs"][j]["right"], a["pairs"][i]["right"]
        return a, "match"
    if k == "numeric":
        parts = [p for p in a.get("parts") or [] if isinstance(p, dict) and isinstance(p.get("value"), (int, float))]
        if not parts:
            return None
        p = rng.choice(parts)
        if rng.random() < 0.5:
            p["value"] = p["value"] * 10
            return a, "numeric-unit-slip"
        p["value"] = p["value"] + (1 if isinstance(p["value"], int) else round(10 ** -max(1, len(str(p["value"]).split(".")[-1])), 6))
        return a, "numeric-arith-slip"
    if k == "text":
        v = str(a.get("value") or "")
        if not v:
            return None
        if len(v) <= 60:
            pool = [x for x in unit_qs if x["id"] != q["id"] and x["type"] == q["type"]
                    and (x.get("answer") or {}).get("kind") == "text"
                    and 0 < len(str(x["answer"].get("value") or "")) <= 60
                    and str(x["answer"]["value"]).strip().lower() != v.strip().lower()]
            if not pool:
                return None
            # the nearest question by position: the realistic slip is the neighbour's key
            idx = {x["id"]: n for n, x in enumerate(unit_qs)}
            me = idx[q["id"]]
            pool.sort(key=lambda x: (abs(idx[x["id"]] - me), x["id"]))
            a["value"] = pool[0]["answer"]["value"]
            return a, "text-neighbour-key"
        hits = list(_OPP_RE.finditer(v))
        if not hits:
            return None
        m = rng.choice(hits)
        a["value"] = v[:m.start()] + swap_case(m[1], _OPP[m[1].lower()]) + v[m.end():]
        return a, "text-opposite-word"
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--staging", required=True)
    ap.add_argument("--class", dest="cls", type=int, required=True, choices=sorted(TAGS))
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sealed", required=True)
    ap.add_argument("--tag", help="override the checked tag (tests only)")
    a = ap.parse_args()
    so, oo = os.path.abspath(a.sealed), os.path.abspath(a.out)
    if os.path.commonpath([so, oo]) == oo:
        sys.exit("--sealed must not be inside --out: the threads would see the plants")
    tag = a.tag or TAGS[a.cls]
    sealed = {"class": a.cls, "tag": tag, "seed": a.seed, "rate": RATE, "plant_version": PLANT_VERSION,
              "plants": [], "not_read_no_key": []}
    base = os.path.join(a.out, f"c{a.cls}")
    counts = {"units": 0, "answered": 0, "plants_A": 0, "plants_B": 0}
    for path, unit in units_at(a.staging, tag):
        un = unit_name(unit)
        qs = unit["questions"]
        answered = [q for q in qs if has_key(q.get("answer") or {})]
        sealed["not_read_no_key"] += [q["id"] for q in qs if q not in answered]
        rng = random.Random(f"{a.seed}:{tag}:{un}")
        n = max(1, round(RATE * len(answered)))
        order = answered[:]
        rng.shuffle(order)
        chosen = {"A": [], "B": []}
        for q in order:  # alternate A, B so the sets are disjoint and equal in size
            side = "A" if len(chosen["A"]) <= len(chosen["B"]) else "B"
            if len(chosen[side]) >= n:
                side = "B" if side == "A" else "A"
                if len(chosen[side]) >= n:
                    break
            p = make_plant(q, qs, rng)
            if p:
                chosen[side].append((q, p))
        for side in "AB":
            planted = {q["id"]: (ans, kind) for q, (ans, kind) in chosen[side]}
            items = []
            for q in answered:
                if q["id"] in planted:
                    ans, kind = planted[q["id"]]
                    items.append(item(q, render_key(q, ans)))
                    sealed["plants"].append({"read": side, "unit": un, "id": q["id"], "kind": kind,
                                             "real_key": render_key(q), "planted_key": render_key(q, ans)})
                else:
                    items.append(item(q, render_key(q)))
            pk = {"packet": "review-read", "packet_version": 1, "class": a.cls, "unit": un, "read": side,
                  "tag": tag, "source_file": path, "brief": "review_read_brief_v1", "items": items}
            d = os.path.join(base, f"read{side}")
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, f"{un}.json"), "w", encoding="utf-8", newline="\n") as fh:
                json.dump(pk, fh, ensure_ascii=False, indent=1)
                fh.write("\n")
            counts[f"plants_{side}"] += len(planted)
        counts["units"] += 1
        counts["answered"] += len(answered)
    os.makedirs(a.sealed, exist_ok=True)
    sp = os.path.join(a.sealed, f"plants_c{a.cls}.json")
    body = json.dumps(sealed, ensure_ascii=False, indent=1) + "\n"
    with open(sp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    print(json.dumps(counts), f"no-key {len(sealed['not_read_no_key'])}")
    print(f"sealed {sp} sha256 {hashlib.sha256(body.encode('utf-8')).hexdigest()}")


if __name__ == "__main__":
    main()
