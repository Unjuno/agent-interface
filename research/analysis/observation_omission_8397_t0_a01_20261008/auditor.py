"""Independent raw-only audit for Issue #8397 T0; does not import candidate.py."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def audit(fixture: dict, raw: dict) -> dict:
    problems: list[str] = []
    expected_scenarios = fixture.get("scenarios", [])
    observed_scenarios = raw.get("scenarios", [])
    if raw.get("schema") != "observation-omission-8397-t0-a01-raw-v1":
        problems.append("raw_schema")
    if [s.get("scenario_id") for s in observed_scenarios] != [s.get("scenario_id") for s in expected_scenarios]:
        problems.append("scenario_identity_or_order")

    summary: dict[str, dict[str, dict]] = {}
    for source, recorded in zip(expected_scenarios, observed_scenarios):
        sid = source["scenario_id"]
        raw_arms = recorded.get("arms", [])
        if [a.get("arm_id") for a in raw_arms] != [a["arm_id"] for a in source["arms"]]:
            problems.append(f"{sid}:arm_identity_or_order")
        indexed: dict[str, dict] = {}
        for source_arm, result_arm in zip(source["arms"], raw_arms):
            arm_name = source_arm["arm_id"]
            indexed[arm_name] = result_arm
            expected_ledger: list[dict] = []
            for event in source["events"]:
                inside = any(pair[0] <= event["tick"] and event["tick"] < pair[1] for pair in source_arm["omit_intervals"])
                is_mandatory = event["kind"] == "mandatory_safety"
                is_optional = event["kind"] == "optional"
                still_open = event["tick"] < source["completion_tick"]
                actually_available = bool(event["captured"]) and bool(event["delivered"])
                suppress = bool(inside and still_open and is_optional and actually_available)
                seen = bool(still_open and actually_available and (is_mandatory or not suppress))
                expected_ledger.append({
                    "event_id": event["event_id"],
                    "captured": event["captured"],
                    "delivered": event["delivered"],
                    "requested_omission": inside,
                    "omitted": suppress,
                    "model_visible": seen,
                    "counted_bytes": event["bytes"] if seen else 0,
                })
            if result_arm.get("events") != expected_ledger:
                problems.append(f"{sid}/{arm_name}:event_visibility_or_cost_ledger")
            seen_ids = {row["event_id"] for row in expected_ledger if row["model_visible"]}
            required_ok = all(req in seen_ids for req in source["required_observation_ids"])
            safety_ok = source["safety_event_id"] is not None and source["safety_event_id"] in seen_ids
            outcome_ok = bool(safety_ok) if source["safety_event_id"] is not None else bool(required_ok)
            effect = source["exact_effect"] if outcome_ok else source["failed_effect"]
            safe_stop = bool(safety_ok)
            reason = "mandatory_safety_cue" if safe_stop else ("verified_completion" if outcome_ok else "task_effect_missing")
            totals = {
                "model_visible_count": sum(1 for row in expected_ledger if row["model_visible"]),
                "model_visible_bytes": sum(row["counted_bytes"] for row in expected_ledger),
                "exact_effect": outcome_ok,
                "effect": effect,
                "safe_stop": safe_stop,
                "stop_reason": reason,
            }
            for key, value in totals.items():
                if result_arm.get(key) != value:
                    problems.append(f"{sid}/{arm_name}:{key}")
        summary[sid] = indexed
        baseline = indexed.get("baseline")
        if baseline is None:
            problems.append(f"{sid}:missing_baseline")
            continue
        for name, result_arm in indexed.items():
            expected_regret = result_arm.get("effect") != baseline.get("effect") or result_arm.get("safe_stop") != baseline.get("safe_stop")
            if result_arm.get("regret_vs_baseline") != expected_regret:
                problems.append(f"{sid}/{name}:regret")

    # Frozen discriminator checks are intentionally not inferred from a generic PASS string.
    by_name = {s["scenario_id"]: summary.get(s["scenario_id"], {}) for s in expected_scenarios}
    checks = {
        "early_omission_preserves_effect_and_reduces_cost": _pair(by_name, "before_sensitive_decision", "omit_before_decision", same_effect=True, lower_cost=True),
        "transition_omission_exposes_regret": _pair(by_name, "crosses_relevant_transition", "omit_across_transition", regret=True),
        "completion_suppresses_post_completion_observation": _pair(by_name, "after_verified_completion", "omit_after_completion", no_post_completion=True),
        "captured_undelivered_is_not_visible": _event(by_name, "captured_but_undelivered", "baseline", "undelivered_cue", visible=False, bytes_zero=True),
        "mandatory_safety_bypasses_omission": _event(by_name, "mandatory_safety_cue", "omit_optional_around_safety", "mandatory_revoke", visible=True, not_omitted=True),
    }
    return {"schema": "observation-omission-8397-t0-a01-audit-v1", "disposition": "PASS_METHOD_SCOPED" if not problems and all(checks.values()) else "FAIL_METHOD", "checks": checks, "problems": problems}


def _pair(index: dict, sid: str, arm_name: str, *, same_effect: bool = False, lower_cost: bool = False, regret: bool = False, no_post_completion: bool = False) -> bool:
    arms = index.get(sid, {})
    base, test = arms.get("baseline"), arms.get(arm_name)
    if base is None or test is None:
        return False
    passed = True
    if same_effect:
        passed &= base.get("effect") == test.get("effect") and not test.get("regret_vs_baseline")
    if lower_cost:
        passed &= test.get("model_visible_count", 0) < base.get("model_visible_count", 0) and test.get("model_visible_bytes", 0) < base.get("model_visible_bytes", 0)
    if regret:
        passed &= bool(test.get("regret_vs_baseline")) and test.get("effect") != base.get("effect")
    if no_post_completion:
        source_events = []  # Ledger already has only source-eligible rows; inspect raw-count exclusion via total baseline.
        passed &= test.get("model_visible_count") == base.get("model_visible_count") and test.get("model_visible_bytes") == base.get("model_visible_bytes")
    return bool(passed)


def _event(index: dict, sid: str, arm_name: str, event_id: str, *, visible: bool, bytes_zero: bool = False, not_omitted: bool = False) -> bool:
    arm = index.get(sid, {}).get(arm_name)
    if arm is None:
        return False
    row = next((event for event in arm.get("events", []) if event.get("event_id") == event_id), None)
    if row is None or row.get("model_visible") is not visible:
        return False
    if bytes_zero and row.get("counted_bytes") != 0:
        return False
    if not_omitted and row.get("omitted") is not False:
        return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("raw", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    raw = json.loads(args.raw.read_text(encoding="utf-8"))
    result = audit(fixture, raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": result["disposition"], "problems": len(result["problems"]), "checks": result["checks"]}))
    raise SystemExit(0 if result["disposition"] == "PASS_METHOD_SCOPED" else 1)


if __name__ == "__main__":
    main()
