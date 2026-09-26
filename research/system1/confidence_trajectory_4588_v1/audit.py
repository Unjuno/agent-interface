#!/usr/bin/env python3
"""Independent raw-only reconstruction for the frozen first-rung corpus."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


POLICIES = (
    "CURRENT_ONLY",
    "LEVEL_PLUS_VELOCITY",
    "LEVEL_PLUS_VELOCITY_PLUS_ACCEL",
    "SMOOTHED_TRAJECTORY",
)
PERTURBATIONS = (-0.010, -0.006, -0.002, 0.002, 0.006, 0.010)


def reference_cases() -> list[dict]:
    expected = []

    def family(label, state, answer, values, clock=(0, 100, 200), history="VALID"):
        for index, offset in enumerate(PERTURBATIONS):
            expected.append({
                "case_id": f"{label}-{index:02d}",
                "family": label,
                "rep": index,
                "intent_id": "intent-fixed-A",
                "candidate_id": "candidate-fixed-A",
                "state": state,
                "truth": answer,
                "scores": [round(value + offset, 6) for value in values],
                "times_ms": list(clock),
                "history_status": history,
                "current_valid": True,
            })

    family("second_order_alias_action", "ACTION_REQUIRED", "ACTION", (.95, .70, .80))
    family("second_order_alias_yield", "ACTION_REQUIRED", "YIELD", (.45, .70, .80))
    family("low_confidence_rising_action", "ACTION_REQUIRED", "ACTION", (.14, .32, .60))
    family("high_confidence_falling_yield", "ACTION_REQUIRED", "YIELD", (.94, .87, .77))
    family("self_correcting_noop", "SELF_CORRECTING", "NO_OP", (.65, .75, .90))
    family("uncertain_yield", "UNCERTAIN", "YIELD", (.40, .80, .55))
    family("transient_spike_yield", "ACTION_REQUIRED", "YIELD", (.40, .95, .55))
    family("irregular_interval_rise_yield", "ACTION_REQUIRED", "YIELD", (.20, .40, .65), (0, 20, 180))
    family("plateau_action", "ACTION_REQUIRED", "ACTION", (.80, .80, .80))
    family("overshoot_yield", "ACTION_REQUIRED", "YIELD", (.70, .92, .70))
    family("oscillatory_acceleration_noise_yield", "ACTION_REQUIRED", "YIELD", (.95, .05, .53))
    for status in ("STALE_PREVIOUS", "MISSING_PREVIOUS", "EPOCH_MISMATCH"):
        family(f"invalid_history_{status.lower()}", "ACTION_REQUIRED", "ACTION", (.55, .72, .95), history=status)
    return expected


def reference_features(case):
    p0, p1, p2 = case["scores"]
    t0, t1, t2 = case["times_ms"]
    v_early = (p1 - p0) * 100.0 / (t1 - t0)
    v_recent = (p2 - p1) * 100.0 / (t2 - t1)
    return v_early, v_recent, v_recent - v_early


def reference_mean(case):
    p0, p1, p2 = case["scores"]
    t0, t1, t2 = case["times_ms"]
    numerator = (p0 + p1) * (t1 - t0) + (p1 + p2) * (t2 - t1)
    return numerator / (2 * (t2 - t0))


def reference_prediction(case, policy):
    if case["current_valid"] is False:
        return {"decision": "YIELD", "source": "CURRENT_INVALID", "features_used": []}
    if case["state"] == "SELF_CORRECTING":
        return {"decision": "NO_OP", "source": "CURRENT_STATE", "features_used": ["state"]}
    if case["state"] == "UNCERTAIN":
        return {"decision": "YIELD", "source": "CURRENT_STATE", "features_used": ["state"]}
    current = case["scores"][2]
    if policy == "CURRENT_ONLY" or case["history_status"] != "VALID":
        return {
            "decision": "ACTION" if current >= .75 else "YIELD",
            "source": "CURRENT_ONLY" if policy == "CURRENT_ONLY" else "CURRENT_ONLY_FALLBACK",
            "features_used": ["current_confidence"],
        }
    _, velocity, accel = reference_features(case)
    velocity_accepts = (current >= .75 and velocity >= 0) or (current >= .55 and velocity >= .20)
    if policy == "LEVEL_PLUS_VELOCITY":
        decision, used = ("ACTION" if velocity_accepts else "YIELD"), ["current_confidence", "velocity"]
    elif policy == "LEVEL_PLUS_VELOCITY_PLUS_ACCEL":
        rescue = current >= .50 and velocity >= .20 and accel >= .50
        decision = "ACTION" if (velocity_accepts and accel >= 0) or rescue else "YIELD"
        used = ["current_confidence", "velocity", "acceleration"]
    elif policy == "SMOOTHED_TRAJECTORY":
        decision = "ACTION" if reference_mean(case) >= .75 else "YIELD"
        used = ["causal_time_weighted_mean"]
    else:
        raise ValueError(policy)
    return {"decision": decision, "source": policy, "features_used": used}


def audit_rows(rows: list[dict]) -> list[str]:
    errors = []
    expected = reference_cases()
    expected_by_id = {case["case_id"]: case for case in expected}
    seen = set()
    for index, row in enumerate(rows):
        case = row.get("input")
        if not isinstance(case, dict):
            errors.append(f"row[{index}]: missing input")
            continue
        cid = case.get("case_id")
        if cid in seen:
            errors.append(f"row[{index}]: duplicate case_id")
        seen.add(cid)
        expected_case = expected_by_id.get(cid)
        if expected_case is None or case != expected_case:
            errors.append(f"row[{index}]: input differs from frozen corpus")
            continue
        predictions = row.get("predictions")
        if not isinstance(predictions, dict) or set(predictions) != set(POLICIES):
            errors.append(f"row[{index}]: policy set mismatch")
            continue
        for policy in POLICIES:
            if predictions[policy] != reference_prediction(case, policy):
                errors.append(f"row[{index}]: {policy} mismatch")
        if any(not math.isfinite(value) or value < 0 or value > 1 for value in case["scores"]):
            errors.append(f"row[{index}]: invalid score range")
    if len(rows) != len(expected):
        errors.append(f"row count {len(rows)} != {len(expected)}")
    if seen != set(expected_by_id):
        errors.append("case-id denominator mismatch")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.raw.read_text(encoding="utf-8").splitlines()]
    errors = audit_rows(rows)
    result = {"rows": len(rows), "checks": len(rows) * (1 + len(POLICIES)), "errors": errors}
    output = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
