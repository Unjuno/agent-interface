import itertools
import json
import sys
from collections import Counter
from pathlib import Path

f = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
rows = f["cases"]
train = [r for r in rows if r["split"] == "train"]
positive = [r for r in train if r["outcome"] == "success"]
negative = [r for r in train if r["outcome"] == "failure"]
atoms = [
    ("target_current=true", lambda r: r["target_current"] is True),
    ("age=fresh", lambda r: r["age"] == "fresh"),
    ("route=A", lambda r: r["route"] == "A"),
    ("version=v1", lambda r: r["version"] == "v1"),
]

chosen = None
for width in range(1, len(atoms) + 1):
    for terms in itertools.combinations(range(len(atoms)), width):
        matches = lambda r: all(atoms[i][1](r) for i in terms)
        if all(matches(r) for r in positive) and not any(matches(r) for r in negative):
            chosen = terms
            break
    if chosen is not None:
        break
if chosen is None:
    raise SystemExit("no consistent conjunction")

def applies(r):
    return all(atoms[i][1](r) for i in chosen)

covered = [r for r in train if applies(r)]
counts = Counter(r["outcome"] for r in covered)
support = {}
for route in f["declared_domain"]["route"]:
    for age in f["declared_domain"]["age"]:
        for current in f["declared_domain"]["target_current"]:
            key = f"{route}|{age}|{int(current)}"
            group = [r for r in rows if r["route"] == route and r["age"] == age and r["target_current"] is current]
            failures = sum(r["outcome"] == "failure" for r in group)
            successes = sum(r["outcome"] == "success" for r in group)
            support[key] = {"n": len(group), "success": successes, "failure": failures,
                            "status": "UNKNOWN_SUPPORT" if failures == 0 else "OBSERVED_FAILURE"}

counterexamples = sorted(r["id"] for r in rows if r["split"] in {"falsifier", "heldout"} and applies(r) and r["outcome"] == "failure")
noise_invariant = all(applies({**r, "noise": value}) == applies(r) for r in rows for value in f["declared_domain"]["noise"])
print(json.dumps({
    "main_sha": f["freeze"]["main_sha"], "allocation": f["freeze"]["allocation"],
    "learned_conjunction": [atoms[i][0] for i in chosen], "train_candidate_n": len(covered),
    "train_candidate_outcomes": dict(counts), "train_accuracy": counts["success"] / len(covered),
    "counterexamples": counterexamples, "support": support,
    "noise_invariant": noise_invariant, "authority_effect": "none"
}, sort_keys=True, separators=(",", ":")))
