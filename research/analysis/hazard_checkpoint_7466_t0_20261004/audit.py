#!/usr/bin/env python3
"""Independent raw-row audit for the #7466 exploratory T0 simulator."""

import json
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

path = Path(sys.argv[1])
rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
assert len(rows) == 400 * 2 * 3, f"row count: {len(rows)}"
cells = defaultdict(list)
for row in rows:
    assert set(row) == {"seed", "cohort", "policy", "total_cost", "lost_work", "interruptions", "checkpoints"}
    assert 0 <= row["seed"] < 400
    assert row["cohort"] in {"informative", "uninformative"}
    assert row["policy"] in {"fixed", "event", "adaptive"}
    assert row["total_cost"] == row["lost_work"] + 3.0 * row["checkpoints"]
    cells[(row["seed"], row["cohort"], row["policy"])].append(row)
assert all(len(v) == 1 for v in cells.values()) and len(cells) == len(rows), "duplicate/missing keys"

def independent_replay(seed, cohort, policy):
    """Rebuild one row from the declared model without importing candidate code."""
    rng = random.Random(seed)
    last = count = lost = failures = 0
    for tick in range(80):
        signal = cohort == "informative" and tick % 20 in (8, 9, 10, 11)
        boundary = (tick + 1) % 5 == 0
        if policy == "fixed":
            take = (tick + 1) % 10 == 0
        elif policy == "event":
            take = boundary
        else:
            take = (signal and 0.25 * 16 > 3.0) or (boundary and cohort == "uninformative")
        hazard = (0.25 if signal else 0.01) if cohort == "informative" else 0.05
        if rng.random() < hazard:
            failures += 1
            lost += tick - last
            last = tick
            count += 1
        if take:
            count += 1
            last = tick + 1
    return {"seed": seed, "cohort": cohort, "policy": policy,
            "total_cost": lost + count * 3.0, "lost_work": lost,
            "interruptions": failures, "checkpoints": count}

for key, grouped in cells.items():
    row = grouped[0]
    assert row == independent_replay(*key), f"independent replay mismatch {key}"
for seed in range(400):
    # In the uninformative cohort, adaptive is explicitly the event fallback;
    # identical costs across every paired seed demonstrate abstention, not gain.
    event = cells[(seed, "uninformative", "event")][0]
    adaptive = cells[(seed, "uninformative", "adaptive")][0]
    assert (event["total_cost"], event["lost_work"], event["checkpoints"]) == (
        adaptive["total_cost"], adaptive["lost_work"], adaptive["checkpoints"]
    ), f"fallback mismatch seed {seed}"
for cohort in ("informative", "uninformative"):
    for policy in ("fixed", "event", "adaptive"):
        vals = [cells[(seed, cohort, policy)][0]["total_cost"] for seed in range(400)]
        print(cohort, policy, "n=400", "mean=%.3f" % statistics.mean(vals),
              "median=%.3f" % statistics.median(vals))
print("PASS: 2400 rows; independent per-seed replay; exact cost reconstruction; uninformative fallback identical on 400/400 paired seeds")
