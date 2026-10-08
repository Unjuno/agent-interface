"""Candidate evaluator for the finite Issue #8397 observation-omission T0."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def in_omission(tick: int, intervals: list[list[int]]) -> bool:
    return any(start <= tick < end for start, end in intervals)


def evaluate_arm(scenario: dict, arm: dict) -> dict:
    completion = scenario["completion_tick"]
    intervals = arm["omit_intervals"]
    ledger = []
    for event in scenario["events"]:
        before_completion = event["tick"] < completion
        captured_and_delivered = event["captured"] and event["delivered"]
        mandatory = event["kind"] == "mandatory_safety"
        requested_omission = in_omission(event["tick"], intervals)
        omitted = (
            before_completion
            and captured_and_delivered
            and event["kind"] == "optional"
            and requested_omission
        )
        visible = before_completion and captured_and_delivered and (mandatory or not omitted)
        ledger.append(
            {
                "event_id": event["event_id"],
                "captured": event["captured"],
                "delivered": event["delivered"],
                "requested_omission": requested_omission,
                "omitted": omitted,
                "model_visible": visible,
                "counted_bytes": event["bytes"] if visible else 0,
            }
        )

    visible_ids = {row["event_id"] for row in ledger if row["model_visible"]}
    required_visible = set(scenario["required_observation_ids"]).issubset(visible_ids)
    safety_visible = scenario["safety_event_id"] is not None and scenario["safety_event_id"] in visible_ids
    safe_stop = bool(safety_visible)
    exact = safe_stop if scenario["safety_event_id"] is not None else required_visible
    effect = scenario["exact_effect"] if exact else scenario["failed_effect"]
    return {
        "arm_id": arm["arm_id"],
        "events": ledger,
        "model_visible_count": sum(row["model_visible"] for row in ledger),
        "model_visible_bytes": sum(row["counted_bytes"] for row in ledger),
        "exact_effect": exact,
        "effect": effect,
        "safe_stop": safe_stop,
        "stop_reason": "mandatory_safety_cue" if safe_stop else ("verified_completion" if exact else "task_effect_missing"),
    }


def evaluate(fixture: dict) -> dict:
    output = {"schema": "observation-omission-8397-t0-a01-raw-v1", "scenarios": []}
    for scenario in fixture["scenarios"]:
        arms = [evaluate_arm(scenario, arm) for arm in scenario["arms"]]
        baseline = next(arm for arm in arms if arm["arm_id"] == "baseline")
        for arm in arms:
            arm["regret_vs_baseline"] = (
                arm["effect"] != baseline["effect"] or arm["safe_stop"] != baseline["safe_stop"]
            )
        output["scenarios"].append({"scenario_id": scenario["scenario_id"], "arms": arms})
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    result = evaluate(fixture)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"scenarios": len(result["scenarios"]), "arms": sum(len(x["arms"]) for x in result["scenarios"]), "output": str(args.output)}))


if __name__ == "__main__":
    main()
