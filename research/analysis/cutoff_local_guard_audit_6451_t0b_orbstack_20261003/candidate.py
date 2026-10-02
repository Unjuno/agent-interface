"""Candidate for a fresh #6451 T0b allocation; emits complete durable raw JSON."""
import json
import sys
from pathlib import Path


def mean(values):
    if not values:
        raise ValueError("empty mean")
    return sum(values) / len(values)


def make_rows(case, intercept, slope):
    rows = []
    for side, count, uptake in ((-1, case["left_count"], case["left_takeup"]),
                                (1, case["right_count"], case["right_takeup"])):
        candidates = [age for age in case["ages"] if age * side > 0]
        for ordinal in range(count):
            age = candidates[ordinal % len(candidates)]
            treated = int(side == 1 and ordinal < round(uptake * count))
            baseline = intercept + slope * age
            rows.append({"id": f"{case['id']}-{side}-{ordinal}", "age": age,
                         "assigned": int(side == 1), "treated": treated,
                         "transition": case["transition_left"] if side < 0 else case["transition_right"],
                         "outcome": baseline + case["effect"] * treated})
    return rows


def local_jump(rows, field, bandwidth):
    distances = sorted({abs(row["age"]) for row in rows if 0 < abs(row["age"]) <= bandwidth})
    paired = []
    for distance in distances:
        left = [row[field] for row in rows if row["age"] == -distance]
        right = [row[field] for row in rows if row["age"] == distance]
        if left and right:
            paired.append((distance, mean(right) - mean(left)))
    if not paired:
        return None
    xbar = mean([point[0] for point in paired])
    ybar = mean([point[1] for point in paired])
    denom = sum((x - xbar) ** 2 for x, _ in paired)
    slope = 0.0 if denom == 0 else sum((x - xbar) * (y - ybar) for x, y in paired) / denom
    return ybar - slope * xbar


def evaluate(spec, case):
    rows = make_rows(case, spec["baseline_intercept"], spec["baseline_slope"])
    bandwidth = spec["local_bandwidth"]
    local = [row for row in rows if 0 < abs(row["age"]) <= bandwidth]
    left_all = [row for row in rows if row["age"] < 0]
    right_all = [row for row in rows if row["age"] > 0]
    left_local = [row for row in local if row["age"] < 0]
    right_local = [row for row in local if row["age"] > 0]
    # Corrected comparator: both sides are restricted to the frozen bandwidth.
    naive_local = mean([r["outcome"] for r in right_local]) - mean([r["outcome"] for r in left_local])
    first_stage = local_jump(rows, "treated", bandwidth)
    outcome_jump = local_jump(rows, "outcome", bandwidth)
    if case["transition_left"] != case["transition_right"]:
        decision, effect = "REFUSE_COINCIDENT_TRANSITION", None
    elif case["timestamp_resolution_ms"] > spec["maximum_timestamp_resolution_ms"]:
        decision, effect = "REFUSE_TIMESTAMP_HEAPING", None
    elif min(len(left_local), len(right_local)) == 0 or max(len(left_local), len(right_local)) / min(len(left_local), len(right_local)) > spec["minimum_side_count_ratio"]:
        decision, effect = "REFUSE_SORTING", None
    elif first_stage is None or first_stage < spec["minimum_first_stage_jump"]:
        decision, effect = "REFUSE_WEAK_FIRST_STAGE", None
    elif first_stage < 1.0:
        decision, effect = "ESTIMATE_LOCAL_FUZZY", outcome_jump / first_stage
    else:
        decision, effect = "ESTIMATE_LOCAL", outcome_jump
    return {"case_id": case["id"], "denominator": len(rows), "local_denominator": len(local),
            "left_local_n": len(left_local), "right_local_n": len(right_local), "rows": rows,
            "naive_near_cutoff_difference": naive_local, "first_stage_jump": first_stage,
            "local_outcome_jump": outcome_jump, "decision": decision, "local_effect": effect}


def run(spec):
    return {"schema": "cutoff-local-rd-candidate-v2", "allocation": spec["allocation"],
            "bandwidth": spec["local_bandwidth"], "attempted_cases": len(spec["cases"]),
            "results": [evaluate(spec, case) for case in spec["cases"]]}


if __name__ == "__main__":
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = Path(sys.argv[2])
    out.write_text(json.dumps(run(spec), sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"status": "RAW_CAPTURED", "bytes": out.stat().st_size}, sort_keys=True))
