"""Independent raw-only reconstruction; deliberately imports no candidate module."""
import json
from pathlib import Path
import sys


def avg(values):
    return sum(values) / len(values)


def reconstruct(case, spec):
    result = []
    for sign, count, uptake in [(-1, case["left_count"], case["left_takeup"]),
                                (1, case["right_count"], case["right_takeup"])]:
        allowed = tuple(v for v in case["ages"] if (v < 0 if sign == -1 else v > 0))
        for ordinal in range(count):
            x = allowed[ordinal % len(allowed)]
            received = 1 if sign == 1 and ordinal < round(uptake * count) else 0
            baseline = spec["baseline_intercept"] + spec["baseline_slope"] * x
            result.append({"id": "%s-%d-%d" % (case["id"], sign, ordinal),
                           "age": x, "assigned": 1 if sign == 1 else 0,
                           "treated": received,
                           "transition": case["transition_left"] if sign == -1 else case["transition_right"],
                           "y0": baseline,
                           "outcome": baseline + case["effect"] * received})
    return result


def jump_at_zero(rows, field, bandwidth):
    differences = []
    for point in sorted(set(abs(row["age"]) for row in rows if abs(row["age"]) <= bandwidth)):
        minus = [row[field] for row in rows if row["age"] == -point]
        plus = [row[field] for row in rows if row["age"] == point]
        if minus and plus:
            differences.append((point, avg(plus) - avg(minus)))
    xbar = avg([item[0] for item in differences])
    ybar = avg([item[1] for item in differences])
    denom = sum((x - xbar) ** 2 for x, _ in differences)
    beta = 0 if denom == 0 else sum((x - xbar) * (y - ybar) for x, y in differences) / denom
    return ybar - beta * xbar


def audit(spec, raw):
    errors = []
    expected_ids = [c["id"] for c in spec["cases"]]
    if raw.get("schema") != "cutoff-local-rd-candidate-v1": errors.append("candidate_schema")
    if raw.get("allocation") != "CUTOFF-LOCAL-GUARD-AUDIT-6451-T0-20261002-01": errors.append("allocation")
    if raw.get("attempted_cases") != len(expected_ids): errors.append("attempted_denominator")
    results = raw.get("results")
    if not isinstance(results, list) or [r.get("case_id") for r in results] != expected_ids:
        errors.append("case_order_or_missing_attempt")
        results = results if isinstance(results, list) else []
    reconstructed = 0
    for index, case in enumerate(spec["cases"]):
        if index >= len(results):
            continue
        observed = results[index]
        rows = reconstruct(case, spec)
        reconstructed += 1
        if observed.get("rows") != rows: errors.append(case["id"] + ":raw_rows")
        if observed.get("denominator") != len(rows): errors.append(case["id"] + ":denominator")
        left = [r for r in rows if r["age"] < 0]
        right = [r for r in rows if r["age"] > 0]
        naive = avg([r["outcome"] for r in right]) - avg([r["outcome"] for r in left])
        stage = jump_at_zero(rows, "treated", spec["local_bandwidth"])
        outcome = jump_at_zero(rows, "outcome", spec["local_bandwidth"])
        if observed.get("naive_near_cutoff_difference") != naive: errors.append(case["id"] + ":naive")
        if observed.get("first_stage_jump") != stage: errors.append(case["id"] + ":first_stage")
        if observed.get("local_outcome_jump") != outcome: errors.append(case["id"] + ":outcome_jump")
        if case["transition_left"] != case["transition_right"]:
            decision, effect = "REFUSE_COINCIDENT_TRANSITION", None
        elif case["timestamp_resolution_ms"] > spec["maximum_timestamp_resolution_ms"]:
            decision, effect = "REFUSE_TIMESTAMP_HEAPING", None
        elif max(len(left), len(right)) / min(len(left), len(right)) > 1.5:
            decision, effect = "REFUSE_SORTING", None
        elif stage < spec["minimum_first_stage_jump"]:
            decision, effect = "REFUSE_WEAK_FIRST_STAGE", None
        elif stage < 1:
            decision, effect = "ESTIMATE_LOCAL_FUZZY", outcome / stage
        else:
            decision, effect = "ESTIMATE_LOCAL", outcome
        if observed.get("decision") != decision: errors.append(case["id"] + ":decision")
        if observed.get("local_effect") != effect: errors.append(case["id"] + ":effect")
    return {"schema": "cutoff-local-rd-independent-audit-v1",
            "status": "PASS_METHOD_SCOPED" if not errors and reconstructed == len(expected_ids) else "FAIL_AUDIT",
            "attempted_case_ids": expected_ids, "reconstructed_cases": reconstructed,
            "errors": errors}


if __name__ == "__main__":
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    raw = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    print(json.dumps(audit(spec, raw), sort_keys=True, separators=(",", ":")))
