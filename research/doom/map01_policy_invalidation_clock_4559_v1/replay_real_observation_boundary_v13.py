"""Replay captured MAP01 typed observations through the production guard boundary.

This is a controlled timestamp-boundary experiment, not a natural-clock
reproduction. It submits no physical input and does not invoke a model.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DOOM = REPO / "research" / "doom"
LIVE = REPO / "research" / "live_control"
sys.path[:0] = [str(DOOM), str(LIVE)]


def load_events(path: Path) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    events = [row for row in rows if row.get("event") == "typed_observation"]
    if len(events) < 3:
        raise ValueError("at least three real typed observations required")
    return events[:3]


def run_case(controller, source: dict, current: dict, decided_ns: int, log: Path) -> dict:
    action = {"commands": [{"action": "forward", "extent": "short"}]}
    contract = controller.build_action_contract(
        action["commands"], {
            "critical_health_minimum": 1,
            "maximum_health_loss": 0,
            "minimum_ammo": 0,
            "max_current_age_ms": 1000,
        }, source["signals"]["health"])
    initial = controller.build_typed_action_snapshot(source, contract)
    initial_decision = source["capture_ns"] + 10_000_000
    validity = controller.evaluate_action_validity(action["commands"], contract,
                                                    initial, initial_decision)
    guard = controller.RunningActionGuard(action["commands"], contract, validity)
    guard.admit_program({"event": "accepted", "id": "controlled-replay",
                         "accepted_ns": initial_decision + 1})
    monitor = controller.DoomRunningActionMonitor(guard, None, None)
    monitor.clock_boundary_log = log
    error = None
    try:
        monitor.observe(current, decided_ns=decided_ns)
    except ValueError as exc:
        error = str(exc)
    rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    receipt = guard.receipt()
    return {"controller_decided_ns": decided_ns,
            "capture_ns": current["capture_ns"],
            "observation_sequence": current["sequence"],
            "delta_ns": decided_ns - current["capture_ns"],
            "logged_before_result": len(rows) == 1,
            "guard_state": receipt["state"],
            "logical_authority_still_active": receipt["current_input_authority"],
            "error": error,
            "row": rows[0] if rows else None}


def boundary_case_is_valid(result: dict, expected_delta: int, expected_error: str | None) -> bool:
    """Require an exact durable operand row and an accepted live guard receipt."""
    row = result.get("row")
    if not isinstance(row, dict) or result.get("logged_before_result") is not True:
        return False
    event = row.get("observation_event")
    if not isinstance(event, dict):
        return False
    if result.get("delta_ns") != expected_delta:
        return False
    if result.get("error") != expected_error:
        return False
    if result.get("guard_state") != "INPUT_ACTIVE":
        return False
    if result.get("logical_authority_still_active") is not True:
        return False
    if row.get("schema") != "running-action-clock-check-v1":
        return False
    if row.get("capture_ns") != result.get("capture_ns"):
        return False
    if row.get("controller_decided_ns") != result.get("controller_decided_ns"):
        return False
    if row.get("comparison_delta_ns") != expected_delta:
        return False
    if row.get("sequence") != result.get("observation_sequence"):
        return False
    if event.get("sequence") != result.get("observation_sequence"):
        return False
    if event.get("capture_ns") != result.get("capture_ns"):
        return False
    return True


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--controller", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location("effective_map01_controller", args.controller)
    controller = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(controller)
    source, inverted, equal = load_events(args.events)
    ordered = dict(equal)
    paths = [args.out / name for name in ("inverted.jsonl", "equal.jsonl", "ordered.jsonl")]
    inverted_result = run_case(controller, source, inverted,
                               inverted["capture_ns"] - 1, paths[0])
    equal_result = run_case(controller, source, equal,
                            equal["capture_ns"], paths[1])
    ordered_result = run_case(controller, source, ordered,
                              ordered["capture_ns"] + 1, paths[2])
    results = {"schema": "map01-real-observation-clock-boundary-v1",
               "scope": "controlled timestamp injection; no model; no physical input",
               "source_sequence": source["sequence"],
               "cases": {"inverted": inverted_result, "equal": equal_result,
                         "ordered": ordered_result}}
    expected = (
        boundary_case_is_valid(inverted_result, -1,
                               "controller decision precedes current snapshot")
        and boundary_case_is_valid(equal_result, 0, None)
        and boundary_case_is_valid(ordered_result, 1, None)
    )
    results["pass"] = expected
    (args.out / "summary.json").write_text(json.dumps(results, indent=2) + "\n",
                                           encoding="utf-8")
    print(json.dumps({"pass": expected, "cases": list(results["cases"])}))
    if not expected:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
