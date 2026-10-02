#!/usr/bin/env python3
"""Deterministic policy materializer for the Issue #6225 finite T0."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
POLICIES = ("best_mean_reactive", "context_gated", "prospective_mixture", "oracle_diagnostic")


def route_outcome(case: dict, route: str, regime: str, b_count: int) -> dict:
    table = case["routes"].get(route)
    if table is None:
        return {"qualified": False, "success": 0, "wrong_effect": 0, "latency": 0}
    key = "idle_after_two" if route == "B" and b_count >= 2 and "idle_after_two" in table else regime
    value = table.get(key)
    if value is None:
        return {"qualified": False, "success": 0, "wrong_effect": 0, "latency": 0}
    return {"qualified": True, **value}


def policy_schedule(case: dict, policy: str) -> list[str | None]:
    regimes = case["regimes"]
    if policy == "prospective_mixture":
        if case["routes"].get("B") is None:
            return ["A"] * len(regimes)
        return list(case["mixture_schedule"])
    if policy == "context_gated":
        return ["B" if case["observable"] and regime == "shock" and case["routes"].get("B") is not None else "A" for regime in regimes]
    if policy == "oracle_diagnostic":
        return ["B" if regime != "stable" and case["routes"].get("B") is not None else "A" for regime in regimes]
    if policy != "best_mean_reactive":
        raise ValueError(policy)
    schedule, detected_failure = [], False
    for _ in regimes:
        route = "B" if detected_failure and case["routes"].get("B") is not None else "A"
        schedule.append(route)
        # The fixed four-task detection delay means a failure is not available
        # to the selector within this four-task mission.
    return schedule


def run_case(case: dict, policy: str) -> dict:
    schedule = policy_schedule(case, policy)
    rows, b_count, unresolved, previous_route = [], 0, 0, None
    for task_index, (regime, route) in enumerate(zip(case["regimes"], schedule), start=1):
        outcome = {"qualified": False, "success": 0, "wrong_effect": 0, "latency": 0} if route is None else route_outcome(case, route, regime, b_count)
        if previous_route == "B" and outcome["qualified"]:
            outcome["latency"] += case.get("carryover_latency_after_b", 0)
        if route == "B":
            b_count += 1
        if not outcome["success"] and not outcome["wrong_effect"]:
            unresolved += 1
        rows.append({"task": task_index, "regime_hidden_from_policy": regime, "selected_route": route, **outcome})
        previous_route = route
        if outcome["wrong_effect"]:
            break
    completed = len(rows)
    return {
        "case": case["id"],
        "policy": policy,
        "route_schedule": schedule,
        "offered_tasks": len(case["regimes"]),
        "executed_tasks": completed,
        "verified_successes": sum(row["success"] for row in rows),
        "wrong_effects": sum(row["wrong_effect"] for row in rows),
        "unresolved_obligations": unresolved + (len(case["regimes"]) - completed),
        "mission_survival": int(not any(row["wrong_effect"] for row in rows)),
        "latency": sum(row["latency"] for row in rows),
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
    rows = [run_case(case, policy) for case in fixture["cases"] for policy in POLICIES]
    result = {"schema": "route-diversification-6225-candidate-v1", "allocation": fixture["allocation"], "fixture_sha256": hashlib.sha256((HERE / "fixture.json").read_bytes()).hexdigest(), "rows": rows}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "cases": len(fixture["cases"]), "policies": list(POLICIES)}, sort_keys=True))


if __name__ == "__main__":
    main()
