#!/usr/bin/env python3
"""plant.py — write planted folios into COPIES of units, and the expected list BEFORE any scan runs."""
import json, glob, os, sys, random, re
src, dst, exp = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(dst, exist_ok=True)
random.seed(21)
plants = []
units = sorted(glob.glob(os.path.join(src, "*.json")))
U = {f: json.load(open(f)) for f in units}
def ans_loc(q): return [l for l in q.get("locators", []) if l["role"] == "answer"]
def q_loc(q): return [l for l in q.get("locators", []) if l["role"] == "question"]
cands = [(f, q) for f, u in U.items() for q in u["questions"] if ans_loc(q) and q.get("answer", {}).get("kind") == "text" and len(str(q["answer"].get("value") or "")) > 40]
mcqs = [(f, q) for f, u in U.items() for q in u["questions"] if q["type"] == "mcq" and q.get("options") and q_loc(q)]
random.shuffle(cands); random.shuffle(mcqs)
def add(f, q, field, n, shape):
    plants.append(dict(unit=os.path.basename(f), id=q["id"], field=field, number=n, shape=shape, expected="FOLIO"))
used = set()
def pick(pool):
    for f, q in pool:
        if q["id"] not in used:
            used.add(q["id"]); return f, q
# 1 end of answer, followed by the next question's opening words (the Class 9 shape)
for _ in range(2):
    f, q = pick(cands); a = ans_loc(q)[0]["printed_page"]
    q["answer"]["value"] = q["answer"]["value"].rstrip() + f" {a} What is the"; add(f, q, "answer", a, "end + next stem")
# 2 start of answer
f, q = pick(cands); a = ans_loc(q)[0]["printed_page"]
q["answer"]["value"] = f"{a} " + q["answer"]["value"]; add(f, q, "answer", a, "start")
# 3 middle of answer, between two sentences
for _ in range(2):
    f, q = pick(cands); a = ans_loc(q)[0]["printed_page"]; v = q["answer"]["value"]
    i = v.find(". ", 15)
    if i < 0: i = len(v) // 2
    q["answer"]["value"] = v[:i + 1] + f" {a} " + v[i + 2:]; add(f, q, "answer", a, "middle")
# 4 inside the stem, the question page's folio (the question side's footer)
f, q = pick(cands); b = q_loc(q)[0]["printed_page"]; t = q["text"]
q["text"] = t.rstrip() + f" {b}"; add(f, q, "text", b, "end of stem (question page)")
# 5 inside an MCQ option
f, q = pick(mcqs); b = q_loc(q)[0]["printed_page"]; o = q["options"][-1]
o["text"] = str(o["text"]).rstrip() + f" {b}"; add(f, q, "option " + str(o["id"]), b, "end of option")
# 6 one page after the answer page (an answer that runs on)
f, q = pick(cands); a = ans_loc(q)[0]["printed_page"] + 1
q["answer"]["value"] = q["answer"]["value"].rstrip() + f" {a} Answer the"; add(f, q, "answer", a, "next page (+1)")
# 7 two pages after the answer page
f, q = pick(cands); a = ans_loc(q)[0]["printed_page"] + 2
q["answer"]["value"] = q["answer"]["value"].rstrip() + f" {a}"; add(f, q, "answer", a, "two pages on (+2)")
# 8 bracketed folio "[N]" as some books print it
f, q = pick(cands); a = ans_loc(q)[0]["printed_page"]
q["answer"]["value"] = q["answer"]["value"].rstrip() + f" [{a}]"; add(f, q, "answer", a, "bracketed [N]")
# 9 single-digit folio, where the class prints pages 1-9 (question page)
small = [(f, q) for f, q in cands if q_loc(q) and q_loc(q)[0]["printed_page"] <= 9]
if small:
    f, q = pick(small); b = q_loc(q)[0]["printed_page"]
    q["text"] = q["text"].rstrip() + f" {b}"; add(f, q, "text", b, "single digit (question page)")
# 10 inside solution_steps or parts, if the class has any
steps = [(f, q) for f, u in U.items() for q in u["questions"] if q.get("solution_steps") and ans_loc(q)]
if steps:
    f, q = pick(steps); a = ans_loc(q)[0]["printed_page"]; st = q["solution_steps"]
    if isinstance(st[0], dict):
        k = next(k for k, v in st[0].items() if isinstance(v, str)); st[0][k] = st[0][k] + f" {a}"
    else:
        st[0] = str(st[0]) + f" {a}"
    add(f, q, "solution_steps", a, "inside solution steps")
for f, u in U.items():
    json.dump(u, open(os.path.join(dst, os.path.basename(f)), "w"))
json.dump(plants, open(exp, "w"), indent=1)
print(len(plants), "plants written to", exp)
