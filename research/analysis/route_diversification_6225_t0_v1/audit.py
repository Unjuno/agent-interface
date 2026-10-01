#!/usr/bin/env python3
"""Independent raw-only enumeration and corruption audit for Issue #6225 T0."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
POLICIES = ("best_mean_reactive", "context_gated", "prospective_mixture", "oracle_diagnostic")


def oracle(case: dict, policy: str) -> dict:
    regimes = tuple(case["regimes"])
    n = len(regimes)
    if policy == "prospective_mixture":
        schedule = tuple("A" for _ in regimes) if case["routes"].get("B") is None else tuple(case["mixture_schedule"])
    elif policy == "context_gated":
        schedule = tuple("B" if case["observable"] and r == "shock" and case["routes"].get("B") is not None else "A" for r in regimes)
    elif policy == "oracle_diagnostic":
        schedule = tuple("B" if r != "stable" and case["routes"].get("B") is not None else "A" for r in regimes)
    else:
        schedule = tuple("A" for _ in regimes)
    generated = []
    b_uses = 0
    previous_route = None
    for i, route in enumerate(schedule):
        r = regimes[i]
        table = case["routes"].get(route)
        if table is None:
            record = {"qualified": False, "success": 0, "wrong_effect": 0, "latency": 0}
        else:
            outcome_key = "idle_after_two" if route == "B" and b_uses >= 2 and "idle_after_two" in table else r
            outcome = table.get(outcome_key)
            record = {"qualified": False, "success": 0, "wrong_effect": 0, "latency": 0} if outcome is None else {"qualified": True, **outcome}
        if previous_route == "B" and record["qualified"]:
            record["latency"] += case.get("carryover_latency_after_b", 0)
        if route == "B":
            b_uses += 1
        generated.append({"task": i + 1, "regime_hidden_from_policy": r, "selected_route": route, **record})
        previous_route = route
        if record["wrong_effect"]:
            break
    executed = len(generated)
    not_run = n - executed
    unresolved = not_run + sum(not row["success"] and not row["wrong_effect"] for row in generated)
    return {
        "case": case["id"], "policy": policy, "route_schedule": list(schedule),
        "offered_tasks": n, "executed_tasks": executed,
        "verified_successes": sum(row["success"] for row in generated),
        "wrong_effects": sum(row["wrong_effect"] for row in generated),
        "unresolved_obligations": unresolved,
        "mission_survival": int(not any(row["wrong_effect"] for row in generated)),
        "latency": sum(row["latency"] for row in generated), "rows": generated,
    }


def corruptions(raw: dict, expected: list[dict], fixture: dict) -> dict:
    tests = {}
    omitted = dict(raw); omitted["rows"] = raw["rows"][1:]
    tests["omitted_policy_row_rejected"] = len(omitted["rows"]) != len(expected)
    swapped = json.loads(json.dumps(raw)); swapped["rows"][0]["case"] = "other-session"
    tests["session_identity_swap_rejected"] = swapped["rows"] != expected
    leaked = json.loads(json.dumps(raw)); leaked["rows"][4]["route_schedule"] = ["B"] * 4
    tests["hidden_regime_leak_rejected"] = leaked["rows"] != expected
    false_success = json.loads(json.dumps(raw)); false_success["rows"][8]["mission_survival"] = 1
    tests["false_safety_pass_rejected"] = false_success["rows"] != expected
    drop_failure = json.loads(json.dumps(raw)); drop_failure["rows"][0]["wrong_effects"] = 0
    tests["failure_omission_rejected"] = drop_failure["rows"] != expected
    stale_ready = json.loads(json.dumps(raw))
    stale_case = next(row for row in stale_ready["rows"] if row["case"] == "b_idle_decay" and row["policy"] == "prospective_mixture")
    stale_row = next(row for row in stale_case["rows"] if row["task"] == 6)
    stale_row["success"] = 1
    tests["stale_b_readiness_rejected"] = stale_ready["rows"] != expected
    reset_carryover = json.loads(json.dumps(raw))
    carry_case = next(row for row in reset_carryover["rows"] if row["case"] == "route_induced_queue_carryover" and row["policy"] == "prospective_mixture")
    carry_task = next(row for row in carry_case["rows"] if row["task"] == 3)
    carry_task["latency"] -= 3
    tests["silent_queue_reset_rejected"] = reset_carryover["rows"] != expected
    denom = json.loads(json.dumps(raw)); denom["rows"][0]["offered_tasks"] -= 1
    tests["offered_denominator_loss_rejected"] = denom["rows"] != expected
    wrong_fixture = json.loads(json.dumps(raw)); wrong_fixture["fixture_sha256"] = "0" * 64
    tests["fixture_hash_mutation_rejected"] = wrong_fixture["fixture_sha256"] != hashlib.sha256(json.dumps(fixture, sort_keys=True, indent=2).encode()).hexdigest()
    return tests


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
    raw = json.loads(args.raw.read_text(encoding="utf-8"))
    expected = [oracle(case, policy) for case in fixture["cases"] for policy in POLICIES]
    errors = []
    if raw.get("allocation") != fixture["allocation"]:
        errors.append("allocation mismatch")
    fixture_hash = hashlib.sha256((HERE / "fixture.json").read_bytes()).hexdigest()
    if raw.get("fixture_sha256") != fixture_hash:
        errors.append("fixture hash mismatch")
    if raw.get("rows") != expected:
        errors.append("candidate rows disagree with independent enumeration")
    by_case = {case["id"]: case for case in fixture["cases"]}
    for row in expected:
        want = by_case[row["case"]]["expect"][row["policy"]]
        keys = ("mission_survival", "verified_successes", "wrong_effects", "latency") if "latency" in want else ("mission_survival", "verified_successes", "wrong_effects")
        observed = {key: row[key] for key in keys}
        if observed != want:
            errors.append(f"hand-calculated expectation mismatch: {row['case']}/{row['policy']}")
    control_results = corruptions(raw, expected, fixture)
    if not all(control_results.values()):
        errors.append("one or more mutation controls were not rejected")
    summaries = {row["case"]: {row["policy"]: {k: row[k] for k in ("mission_survival", "verified_successes", "wrong_effects", "unresolved_obligations", "latency")} for row in expected if row["case"] == case["id"]} for case in fixture["cases"]}
    result = {
        "schema": "route-diversification-6225-audit-v1", "allocation": fixture["allocation"],
        "candidate_rows": len(raw.get("rows", [])), "independent_rows": len(expected),
        "case_summaries": summaries, "mutation_controls": control_results,
        "errors": errors, "disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": result["disposition"], "rows": len(expected), "errors": errors, "mutation_controls": sum(control_results.values())}, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
