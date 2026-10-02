"""Deterministic synthetic cutoff-local audit candidate; standard library only."""
import json
from pathlib import Path
import sys


def observations(case, intercept, slope):
    rows = []
    ages = case["ages"]
    for side, count, takeup in ((-1, case["left_count"], case["left_takeup"]),
                                (1, case["right_count"], case["right_takeup"])):
        selected = [a for a in ages if (a < 0 if side < 0 else a > 0)]
        for i in range(count):
            age = selected[i % len(selected)]
            treated = int(side > 0 and i < round(takeup * count))
            rows.append({"id": f"{case['id']}-{side}-{i}", "age": age,
                         "assigned": int(side > 0), "treated": treated,
                         "transition": case["transition_left"] if side < 0 else case["transition_right"],
                         "y0": intercept + slope * age,
                         "outcome": intercept + slope * age + case["effect"] * treated})
    return rows


def mean(values):
    return sum(values) / len(values)


def local_linear_jump(rows, key, bandwidth):
    paired = {}
    for side in (-1, 1):
        for distance in sorted({abs(r["age"]) for r in rows if r["age"] * side > 0 and abs(r["age"]) <= bandwidth}):
            values = [r[key] for r in rows if r["age"] * side > 0 and abs(r["age"]) == distance]
            paired.setdefault(distance, {})[side] = mean(values)
    points = [(d, v[1] - v[-1]) for d, v in paired.items() if 1 in v and -1 in v]
    xbar, ybar = mean([p[0] for p in points]), mean([p[1] for p in points])
    variance = sum((x - xbar) ** 2 for x, _ in points)
    slope = 0.0 if variance == 0 else sum((x - xbar) * (y - ybar) for x, y in points) / variance
    return ybar - slope * xbar


def evaluate(case, spec=None):
    if spec is None:
        spec = {"baseline_intercept": 100, "baseline_slope": 3,
                "local_bandwidth": 1.5, "maximum_timestamp_resolution_ms": 10,
                "minimum_first_stage_jump": 0.25}
    rows = observations(case, spec["baseline_intercept"], spec["baseline_slope"])
    left = [r for r in rows if r["age"] < 0]
    right = [r for r in rows if r["age"] > 0]
    near_l = [r for r in left if abs(r["age"]) <= spec["local_bandwidth"]]
    near_r = [r for r in right if abs(r["age"]) <= spec["local_bandwidth"]]
    naive = mean([r["outcome"] for r in right]) - mean([r["outcome"] for r in left])
    first_stage = local_linear_jump(rows, "treated", spec["local_bandwidth"])
    outcome_jump = local_linear_jump(rows, "outcome", spec["local_bandwidth"])
    if case["transition_left"] != case["transition_right"]:
        decision, effect = "REFUSE_COINCIDENT_TRANSITION", None
    elif case["timestamp_resolution_ms"] > spec["maximum_timestamp_resolution_ms"]:
        decision, effect = "REFUSE_TIMESTAMP_HEAPING", None
    elif max(len(left), len(right)) / min(len(left), len(right)) > 1.5:
        decision, effect = "REFUSE_SORTING", None
    elif first_stage < spec["minimum_first_stage_jump"]:
        decision, effect = "REFUSE_WEAK_FIRST_STAGE", None
    elif first_stage < 1.0:
        decision, effect = "ESTIMATE_LOCAL_FUZZY", outcome_jump / first_stage
    else:
        decision, effect = "ESTIMATE_LOCAL", outcome_jump
    return {"case_id": case["id"], "denominator": len(rows), "rows": rows,
            "naive_near_cutoff_difference": naive, "first_stage_jump": first_stage,
            "local_outcome_jump": outcome_jump, "decision": decision,
            "local_effect": effect}


def run(spec):
    return {"schema": "cutoff-local-rd-candidate-v1",
            "allocation": "CUTOFF-LOCAL-GUARD-AUDIT-6451-T0-20261002-01",
            "attempted_cases": len(spec["cases"]),
            "results": [evaluate(c, spec) for c in spec["cases"]]}


if __name__ == "__main__":
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps(run(spec), sort_keys=True, separators=(",", ":")))
