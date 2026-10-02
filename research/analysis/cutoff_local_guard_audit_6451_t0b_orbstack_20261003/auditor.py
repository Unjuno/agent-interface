"""Independent raw-only #6451 audit; does not import or execute candidate.py."""
import json
import math
import sys
from pathlib import Path


def avg(xs):
    if not xs:
        return None
    return sum(xs) / len(xs)


def reconstruct(case, intercept, slope):
    expected = []
    for side in (-1, 1):
        count = case["left_count"] if side == -1 else case["right_count"]
        takeup = case["left_takeup"] if side == -1 else case["right_takeup"]
        ages = [x for x in case["ages"] if x * side > 0]
        for ordinal in range(count):
            age = ages[ordinal % len(ages)]
            treated = int(side == 1 and ordinal < round(takeup * count))
            expected.append({"id": f"{case['id']}-{side}-{ordinal}", "age": age,
                             "assigned": int(side == 1), "treated": treated,
                             "transition": case["transition_left"] if side == -1 else case["transition_right"],
                             "outcome": intercept + slope * age + case["effect"] * treated})
    return expected


def discontinuity(rows, field, bandwidth):
    distances = sorted({abs(r["age"]) for r in rows if 0 < abs(r["age"]) <= bandwidth})
    pairs = []
    for d in distances:
        minus = [r[field] for r in rows if r["age"] == -d]
        plus = [r[field] for r in rows if r["age"] == d]
        if minus and plus:
            pairs.append((d, avg(plus) - avg(minus)))
    if not pairs:
        return None
    mx, my = avg([p[0] for p in pairs]), avg([p[1] for p in pairs])
    sxx = sum((x - mx) ** 2 for x, _ in pairs)
    b = 0.0 if sxx == 0 else sum((x - mx) * (y - my) for x, y in pairs) / sxx
    return my - b * mx


def expected_case(spec, case):
    rows = reconstruct(case, spec["baseline_intercept"], spec["baseline_slope"])
    bw = spec["local_bandwidth"]
    within = [r for r in rows if 0 < abs(r["age"]) <= bw]
    left = [r for r in within if r["age"] < 0]
    right = [r for r in within if r["age"] > 0]
    fs = discontinuity(rows, "treated", bw)
    dy = discontinuity(rows, "outcome", bw)
    if case["transition_left"] != case["transition_right"]:
        decision, effect = "REFUSE_COINCIDENT_TRANSITION", None
    elif case["timestamp_resolution_ms"] > spec["maximum_timestamp_resolution_ms"]:
        decision, effect = "REFUSE_TIMESTAMP_HEAPING", None
    elif min(len(left), len(right)) == 0 or max(len(left), len(right)) / min(len(left), len(right)) > spec["minimum_side_count_ratio"]:
        decision, effect = "REFUSE_SORTING", None
    elif fs is None or fs < spec["minimum_first_stage_jump"]:
        decision, effect = "REFUSE_WEAK_FIRST_STAGE", None
    elif fs < 1.0:
        decision, effect = "ESTIMATE_LOCAL_FUZZY", dy / fs
    else:
        decision, effect = "ESTIMATE_LOCAL", dy
    return {"rows": rows, "denominator": len(rows), "local_denominator": len(within),
            "left_local_n": len(left), "right_local_n": len(right),
            "naive_near_cutoff_difference": avg([r["outcome"] for r in right]) - avg([r["outcome"] for r in left]),
            "first_stage_jump": fs, "local_outcome_jump": dy,
            "decision": decision, "local_effect": effect}


def audit(spec, raw):
    errors = []
    ids = [c["id"] for c in spec["cases"]]
    if raw.get("schema") != "cutoff-local-rd-candidate-v2": errors.append("schema")
    if raw.get("allocation") != spec["allocation"]: errors.append("allocation")
    if raw.get("bandwidth") != spec["local_bandwidth"]: errors.append("bandwidth")
    got = raw.get("results")
    if not isinstance(got, list) or [x.get("case_id") for x in got if isinstance(x, dict)] != ids:
        errors.append("attempted_case_denominator_or_order")
        got = got if isinstance(got, list) else []
    if raw.get("attempted_cases") != len(ids): errors.append("attempted_cases")
    n = 0
    for i, case in enumerate(spec["cases"]):
        if i >= len(got) or not isinstance(got[i], dict):
            continue
        n += 1
        want = expected_case(spec, case)
        row = got[i]
        for field, value in want.items():
            observed = row.get(field)
            if field in {"first_stage_jump", "local_outcome_jump", "naive_near_cutoff_difference", "local_effect"}:
                same = (observed is None and value is None) or (isinstance(observed, (float, int)) and isinstance(value, (float, int)) and math.isclose(observed, value, rel_tol=0, abs_tol=1e-12))
            else:
                same = observed == value
            if not same:
                errors.append(f"{case['id']}:{field}")
    if n != len(ids): errors.append("reconstructed_cases")
    return {"schema": "cutoff-local-rd-audit-v2", "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
            "attempted_case_ids": ids, "reconstructed_cases": n, "errors": errors,
            "scope": "frozen synthetic method fixture only"}


def controls(spec, raw):
    cases = []
    x = json.loads(json.dumps(raw)); x["results"].pop(); cases.append(("drop_case", x, "results"))
    x = json.loads(json.dumps(raw)); x["results"][0]["rows"][0]["outcome"] += 1; cases.append(("alter_raw_row", x, "results"))
    x = json.loads(json.dumps(raw)); x["results"][2]["decision"] = "ESTIMATE_LOCAL"; cases.append(("alter_decision", x, "results"))
    x = json.loads(json.dumps(raw)); x["results"][1]["denominator"] -= 1; cases.append(("alter_denominator", x, "results"))
    x = json.loads(json.dumps(raw)); x["bandwidth"] = 0.5; cases.append(("alter_bandwidth", x, "bandwidth"))
    result = []
    for name, mutant, field in cases:
        effective = mutant.get(field) != raw.get(field)
        rejected = audit(spec, mutant)["status"] != "PASS_METHOD_SCOPED"
        result.append({"name": name, "effective": effective, "rejected": rejected})
    return {"status": "PASS_CONTROLS" if all(c["effective"] and c["rejected"] for c in result) else "FAIL_CONTROLS",
            "rejected": sum(c["rejected"] for c in result), "total": len(result), "controls": result}


if __name__ == "__main__":
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    raw = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    receipt = audit(spec, raw)
    receipt["controls"] = controls(spec, raw)
    out = Path(sys.argv[3])
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"audit_status": receipt["status"], "errors": len(receipt["errors"]),
                      "controls_status": receipt["controls"]["status"]}, sort_keys=True))
    if receipt["status"] != "PASS_METHOD_SCOPED" or receipt["controls"]["status"] != "PASS_CONTROLS":
        raise SystemExit(1)
