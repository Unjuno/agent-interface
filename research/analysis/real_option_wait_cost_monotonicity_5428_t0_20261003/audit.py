"""Independent exhaustive reconstruction; deliberately does not import candidate.py."""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path


def oracle(case: dict) -> tuple[str, str]:
    gates = (case["authorized"], case["fresh"], case["hard_safety_pass"], case["commit_window_open"])
    if any(value is not True for value in gates):
        return "HOLD", "HARD_GATE"
    if case["priceable"] is not True:
        return "HOLD", "UNPRICEABLE"
    if case["wait_deadline_remaining"] <= 0 or case["wait_route"] is not True:
        return "COMMIT", "WAIT_UNAVAILABLE"
    adjusted_commit = case["commit_value"] + (-case["lost_flexibility_cost"])
    net_wait = case["future_gross_value"] + (-case["wait_cost"])
    if adjusted_commit < net_wait:
        return "WAIT", "PAIRWISE_NET_VALUE"
    return "COMMIT", "PAIRWISE_NET_VALUE"


def expected_cases(design: dict) -> list[dict]:
    axes = design["numeric_grid"]
    out = []
    i = 0
    for now in axes["commit_value"]:
        for future in axes["future_gross_value"]:
            for wait_cost in axes["wait_cost"]:
                for lost_flex in axes["lost_flexibility_cost"]:
                    out.append({
                        "id": f"grid-{i:03d}", "authorized": True,
                        "fresh": True, "hard_safety_pass": True,
                        "commit_window_open": True,
                        "priceable": True, "commit_value": now,
                        "future_gross_value": future, "wait_cost": wait_cost,
                        "lost_flexibility_cost": lost_flex, "wait_route": True,
                        "wait_deadline_remaining": 1, "information_available": True,
                    })
                    i += 1
    return out + design["corner_cases"]


def audit(design: dict, result: dict) -> dict:
    errors = []
    if result.get("schema") != "real-option-wait-cost-result-v1":
        errors.append("schema")
    if result.get("allocation") != "REAL-OPTION-WAIT-COST-MONOTONICITY-5428-T0-20261003-01":
        errors.append("allocation")
    expected = expected_cases(design)
    rows = result.get("rows", [])
    if len(rows) != len(expected):
        errors.append(f"row_count:{len(rows)}!={len(expected)}")
    if [row.get("id") for row in rows] != [case["id"] for case in expected]:
        errors.append("identity_or_order")
    by_id = {row.get("id"): row for row in rows}
    if len(by_id) != len(rows):
        errors.append("duplicate_id")

    decisions = {}
    for case in expected:
        row = by_id.get(case["id"])
        if row is None:
            errors.append(f"missing:{case['id']}")
            continue
        for key, value in case.items():
            if row.get(key) != value:
                errors.append(f"input:{case['id']}:{key}")
        decision, reason = oracle(case)
        if row.get("decision") != decision:
            errors.append(f"decision:{case['id']}")
        if row.get("reason") != reason:
            errors.append(f"reason:{case['id']}")
        decisions[case["id"]] = decision

    grid = [case for case in expected if case["id"].startswith("grid-")]
    def key(case):
        return (case["commit_value"], case["future_gross_value"],
                case["wait_cost"], case["lost_flexibility_cost"])
    grid_decision = {key(case): decisions.get(case["id"]) for case in grid}
    for now, future, lost in itertools.product(
        design["numeric_grid"]["commit_value"],
        design["numeric_grid"]["future_gross_value"],
        design["numeric_grid"]["lost_flexibility_cost"],
    ):
        path = [grid_decision[(now, future, cost, lost)]
                for cost in design["numeric_grid"]["wait_cost"]]
        seen_commit = False
        for value in path:
            if value == "COMMIT":
                seen_commit = True
            elif value == "WAIT" and seen_commit:
                errors.append(f"wait_cost_nonmonotonic:{now}:{future}:{lost}")
                break
    for now, future, cost in itertools.product(
        design["numeric_grid"]["commit_value"],
        design["numeric_grid"]["future_gross_value"],
        design["numeric_grid"]["wait_cost"],
    ):
        path = [grid_decision[(now, future, cost, loss)]
                for loss in design["numeric_grid"]["lost_flexibility_cost"]]
        seen_wait = False
        for value in path:
            if value == "WAIT":
                seen_wait = True
            elif value == "COMMIT" and seen_wait:
                errors.append(f"lost_flex_nonmonotonic:{now}:{future}:{cost}")
                break
    summary = {
        "grid_rows": len(grid), "corner_rows": len(expected) - len(grid),
        "total_rows": len(expected), "commit": sum(v == "COMMIT" for v in decisions.values()),
        "wait": sum(v == "WAIT" for v in decisions.values()),
        "hold": sum(v == "HOLD" for v in decisions.values()),
        "wait_cost_monotonicity_violations": sum(e.startswith("wait_cost_nonmonotonic:") for e in errors),
        "lost_flexibility_monotonicity_violations": sum(e.startswith("lost_flex_nonmonotonic:") for e in errors),
        "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
        "errors": errors,
    }
    return summary


if __name__ == "__main__":
    design = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    result = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    Path(sys.argv[3]).write_text(
        json.dumps(audit(design, result), sort_keys=True, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )
