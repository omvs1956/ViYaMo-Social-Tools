"""review_common.py — shared helpers for the review stage (review method v1.3, viyamo-record/design/).

Reads units at a tag straight from the staging clone (git show), never from a working copy, so every
packet is reproducible from (tag, seed). Standard library only.
"""
import json, re, subprocess

TAGS = {}  # social science: the coordinator adds {class: "<staging tag>"} when a class is ready for review
VERDICTS = ["CORRECT", "WRONG", "INCOMPLETE", "UNSURE"]


def git(repo, *a, binary=False):
    r = subprocess.run(["git", "-C", repo, *a], capture_output=True)
    if r.returncode:
        raise SystemExit(f"git {' '.join(a)}: {r.stderr.decode(errors='replace').strip()}")
    return r.stdout if binary else r.stdout.decode("utf-8")


def units_at(staging, tag):
    """[(path, unit_json)] for every question file at the tag, sorted by path."""
    files = sorted(f for f in git(staging, "ls-tree", "-r", "--name-only", tag).split("\n")
                   if "_questions_" in f and f.endswith(".json"))
    return [(f, json.loads(git(staging, "show", f"{tag}:{f}", binary=True))) for f in files]


def unit_name(unit):
    return re.match(r"([a-z]{2,4}-\d+-\d+)", unit["machine_name"])[1]


def options_of(q):
    o = q.get("options")
    return [x for x in o if isinstance(x, dict)] if isinstance(o, list) else []


def has_key(a):
    return any(a.get(k) not in (None, "", [], {}) for k in ("value", "option_id", "option_ids", "pairs", "parts"))


def render_key(q, a=None):
    """The stored answer as one line of text, the way a reader sees it."""
    a = q.get("answer") if a is None else a
    a = a or {}
    k = a.get("kind")
    if k == "option" and a.get("option_id") is not None:
        t = {o.get("id"): o.get("text", "") for o in options_of(q)}.get(a["option_id"], "?")
        return f"({a['option_id']}) {t}"
    if k == "text":
        return str(a.get("value") or "")
    if a.get("pairs"):
        return "; ".join(f"{p.get('left')} → {p.get('right')}" for p in a["pairs"])
    if a.get("parts"):
        return "; ".join(f"{p.get('label') or p.get('id')}: {p.get('value')} {p.get('unit') or ''}".strip()
                         for p in a["parts"] if isinstance(p, dict))
    if a.get("option_ids"):
        return ", ".join(map(str, a["option_ids"]))
    return ""


def match_sides(q):
    o = q.get("options")
    return (o.get("left") or [], o.get("right") or []) if isinstance(o, dict) else ([], [])
