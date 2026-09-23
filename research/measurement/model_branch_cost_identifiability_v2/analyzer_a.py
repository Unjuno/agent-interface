#!/usr/bin/env python3
import argparse, itertools, json
from pathlib import Path

KEYS=("run","i","img","input","cached","output","reasoning","model_ns","effect","state","primary","branches","session")
REQUIRED=("exact_image","effect_memory","action_state","primary_shape","cache_counters","session_state")

def row(values):
    return dict(zip(KEYS, values))

def gates(a,b):
    return {
        "exact_image": a["img"] == b["img"],
        "effect_memory": a["effect"] == b["effect"],
        "action_state": a["state"] == b["state"],
        "primary_shape": a["primary"] == b["primary"],
        "cache_counters": (a["input"],a["cached"]) == (b["input"],b["cached"]),
        "session_state": a["session"] == b["session"],
        "branch_count_diff": a["branches"] != b["branches"],
    }

def analyze(path):
    data=json.loads(Path(path).read_text())
    rows=[row(x) for x in data["rows"]]
    grouped=[x for x in rows if x["run"]=="grouped"]
    ungrouped=[x for x in rows if x["run"]=="ungrouped"]
    failures={k:0 for k in REQUIRED}
    admissible=[]
    same_image=0
    all_fail=True
    for a,b in itertools.product(grouped,ungrouped):
        g=gates(a,b)
        same_image += int(g["exact_image"])
        for k in REQUIRED:
            failures[k] += int(not g[k])
        matched=all(g[k] for k in REQUIRED)
        if matched and g["branch_count_diff"]:
            admissible.append([a["i"],b["i"]])
        if all(g[k] for k in REQUIRED):
            all_fail=False
    return {
        "analyzer":"A_cartesian_gate_vector",
        "rows":len(rows),
        "grouped_rows":len(grouped),
        "ungrouped_rows":len(ungrouped),
        "candidate_pairs":len(grouped)*len(ungrouped),
        "same_image_pairs":same_image,
        "admissible_pairs":admissible,
        "admissible_pair_count":len(admissible),
        "all_pairs_fail_at_least_one_required_gate":all_fail,
        "gate_failure_counts":failures,
        "causal_per_branch_estimate":None
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("ledger")
    p.add_argument("out")
    a=p.parse_args()
    Path(a.out).write_text(json.dumps(analyze(a.ledger),indent=2,sort_keys=True)+"\n")
