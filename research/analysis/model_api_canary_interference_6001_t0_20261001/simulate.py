#!/usr/bin/env python3
"""Issue #6001 T0: canary-induced shared-service interference fixture.

No provider/model calls. Each replicate runs A then B on a deterministic FCFS
shared service. The bracket probe occurs between route blocks. The semantic
response generator is orthogonal to queue timing, allowing the audit to
distinguish a behavior shift from probe workload interference.
"""
import json
import random
import sys

SEED = 6001001
REPLICATES = 240
POLICIES = ("no_probe", "shared_canary", "shared_sham", "isolated_canary")
SCENARIOS = ("null", "interference_only", "semantic_shift", "both")


def run(policy, scenario, trial):
    rng = random.Random(SEED + trial)
    shifted = scenario in ("semantic_shift", "both")
    service = {"A": 10.0 + rng.uniform(0, 0.2),
               "B": 10.0 + rng.uniform(0, 0.2)}
    queue_free = 0.0
    events = []
    # A route block then its bracket canary/sham, followed by B.
    for arm in ("A", "B"):
        submitted = 0.0 if arm == "A" else events[0]["finish"]
        start = max(queue_free, submitted)
        finish = start + service[arm]
        events.append({"kind": "route", "arm": arm, "submitted": submitted, "start": start,
                       "finish": finish, "service": service[arm],
                       "eligible": True})
        queue_free = finish
        if arm == "A" and policy != "no_probe":
            duration = 6.0  # frozen matched canary/sham service demand
            if policy in ("shared_canary", "shared_sham"):
                pstart = queue_free
                pfinish = pstart + duration
                queue_free = pfinish
            else:
                pstart, pfinish = 0.0, duration  # independent service pool
            events.append({"kind": "probe" if policy != "shared_sham" else "sham",
                           "arm": "bracket", "start": pstart,
                           "finish": pfinish, "service": duration,
                           "eligible": True})
    # Fixed non-action canary semantic score: Bernoulli task-class correctness.
    # Under shift, post-bracket B distribution drops from .90 to .55.
    p = 0.55 if shifted else 0.90
    canary = int(rng.random() < p)
    return {"trial": trial, "policy": policy, "scenario": scenario,
            "events": events, "canary_post": canary,
            "semantic_shift_planted": shifted}


def main(path):
    rows = [run(policy, scenario, trial)
            for scenario in SCENARIOS for policy in POLICIES
            for trial in range(REPLICATES)]
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"rows": len(rows), "seed": SEED,
                      "replicates_per_cell": REPLICATES, "output": path}))


if __name__ == "__main__":
    main(sys.argv[1])
