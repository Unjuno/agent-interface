"""Synthetic regression for analyze_retained_hold_bounds_v1.py."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE / "analyze_retained_hold_bounds_v1.py"


def load():
    spec = importlib.util.spec_from_file_location("hold_bounds", TARGET)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    m = load()
    report = {"decisions": [{
        "iteration": 0,
        "controller_model_started_ns": 0,
        "controller_model_ended_ns": 1_000_000_000,
    }]}
    events = [
        {"event": "command", "command": {"op": "submit", "id": "normal", "steps": [
            {"op": "hold", "keys": ["a"], "duration_ms": 350}]}},
        {"event": "keys_held", "id": "normal", "step": 0, "keys": ["a"],
         "input_ack_ns": 100_000_000, "emit_ns": 101_000_000},
        {"event": "observation", "id": "normal", "step": 0, "capture_ns": 300_000_000},
        {"event": "observation", "id": "normal", "step": 0, "capture_ns": 480_000_000},
        {"event": "step_completed", "id": "normal", "step": 0, "completed_ns": 500_000_000},
        {"event": "terminal", "id": "normal", "status": "completed",
         "release": {"verified": True, "verified_ns": 510_000_000}},
        {"event": "command", "command": {"op": "submit", "id": "cancelled", "steps": [
            {"op": "hold", "keys": ["space"], "duration_ms": 500}]}},
        {"event": "keys_held", "id": "cancelled", "step": 0, "keys": ["space"],
         "input_ack_ns": 700_000_000, "emit_ns": 701_000_000},
        {"event": "input_released", "id": "cancelled",
         "owner_release": {"verified": True, "verified_ns": 800_000_000}},
        {"event": "terminal", "id": "cancelled", "status": "cancelled",
         "release": {"verified": True, "verified_ns": 820_000_000}},
        {"event": "post_control_score", "kill_count": 1, "death_count": 0},
    ]
    result = m.analyze_events(report, events)
    rows = {row["id"]: row for row in result["hold_steps"]}

    normal = rows["normal"]
    assert normal["status"] == "completed_release_bounded"
    assert normal["release_lower_ns"] == 451_000_000
    assert normal["release_upper_ns"] == 480_000_000
    assert normal["release_bound_width_ms"] == 29.0
    assert normal["all_keys_down_duration_lower_ms"] == 351.0
    assert normal["all_keys_down_duration_upper_ms"] == 380.0
    assert normal["model_wait_overlaps"] == [{
        "iteration": 0,
        "model_wait_overlap_lower_ms": 351.0,
        "model_wait_overlap_upper_ms": 380.0,
    }]

    cancelled = rows["cancelled"]
    assert cancelled["status"] == "interrupted_empty_upper_bounded"
    assert cancelled["release_lower_ns"] == 700_000_000
    assert cancelled["release_upper_ns"] == 800_000_000
    assert cancelled["all_keys_down_duration_lower_ms"] == 0.0
    assert cancelled["all_keys_down_duration_upper_ms"] == 100.0

    summary = result["summary"]
    assert summary["first_independent_useful_outcome_time"] == "unavailable"
    assert summary["terminal_independent_score_events"] == 1
    print("PASS retained hold-bound synthetic regression")


if __name__ == "__main__":
    main()
