#!/usr/bin/env python3
"""Independent exhaustive check of candidate route labels and fixed oracles."""

import json
import sys
from pathlib import Path


EXPECTED = {
    "half_model": ("ROUTE_STABLE", ["model"], ["model"], -50),
    "plus_80": ("ROUTE_STABLE", ["model"], ["model"], 80),
    "route_switch": (
        "NONSTATIONARY_INTERVENTION",
        ["model"],
        ["alternate"],
        None,
    ),
    "exact_tie": ("TIE_SET", ["model"], ["alternate", "model"], None),
    "max_cost_control": ("ROUTE_STABLE", ["alternate"], ["alternate"], 0),
}


def exhaustive_optima(routes, cost_key, selector):
    scored = [(route["id"], route[cost_key]) for route in routes]
    target = sorted(cost for _, cost in scored)[0 if selector == "min_cost" else -1]
    return sorted(route_id for route_id, cost in scored if cost == target)


def expected_result(fixture):
    before = exhaustive_optima(fixture["routes"], "baseline_ms", fixture["selector"])
    after = exhaustive_optima(fixture["routes"], "intervention_ms", fixture["selector"])
    if len(before) != 1 or len(after) != 1:
        status, delta = "TIE_SET", None
    elif before != after:
        status, delta = "NONSTATIONARY_INTERVENTION", None
    else:
        selected = before[0]
        route = next(route for route in fixture["routes"] if route["id"] == selected)
        status = "ROUTE_STABLE"
        delta = route["intervention_ms"] - route["baseline_ms"]
    return {
        "case_id": fixture["id"],
        "selector": fixture["selector"],
        "baseline_optima": before,
        "intervention_optima": after,
        "status": status,
        "endpoint_delta_ms": delta,
    }


def audit(fixtures, results):
    errors = []
    ids = [fixture.get("id") for fixture in fixtures]
    if ids != list(EXPECTED):
        errors.append({"check": "case_order_and_identity", "got": ids})
    if len(results) != len(fixtures):
        errors.append(
            {"check": "row_count", "expected": len(fixtures), "got": len(results)}
        )
    by_id = {row.get("case_id"): row for row in results}
    for fixture in fixtures:
        case_id = fixture.get("id")
        want = expected_result(fixture)
        got = by_id.get(case_id)
        if got != want:
            errors.append({"check": "independent_enumeration", "case_id": case_id,
                           "expected": want, "got": got})
        literal = EXPECTED.get(case_id)
        if literal and (
            want["status"],
            want["baseline_optima"],
            want["intervention_optima"],
            want["endpoint_delta_ms"],
        ) != literal:
            errors.append({"check": "hand_calculated_oracle", "case_id": case_id,
                           "expected": literal, "got": want})
    return errors


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: audit.py FIXTURES.json CANDIDATE_RAW.json")
    fixtures = json.loads(Path(argv[1]).read_text())
    results = json.loads(Path(argv[2]).read_text())
    errors = audit(fixtures, results)
    print(json.dumps({"status": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
                      "errors": errors, "fixture_count": len(fixtures),
                      "candidate_row_count": len(results)},
                     sort_keys=True, separators=(",", ":")))
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
