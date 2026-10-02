import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "fulltrace_v4", HERE / "analyze_map01_held_input_occupancy_fulltrace_v4.py")
analysis = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(analysis)

MS = 1_000_000


def cancel_races_ack():
    return [
        {"event": "command", "command": {"op": "submit", "id": "p", "steps": [
            {"op": "hold", "keys": ["Down", "space"], "duration_ms": 300}]},
         "received_ns": 50 * MS},
        {"event": "step_started", "id": "p", "step": 0,
         "operation": "hold", "issued_ns": 100 * MS},
        {"event": "command", "command": {"op": "cancel", "id": "p"},
         "received_ns": 105 * MS},
        {"event": "input_admission", "key": "Down", "admitted_ns": 104 * MS,
         "input_ack_ns": 106 * MS},
        {"event": "terminal", "id": "p", "status": "cancelled", "steps_completed": 0,
         "interruption": {"record": {"verified": True, "keys_down": [],
             "buttons_down": [], "reason": "cancelled", "verified_ns": 125 * MS}},
         "release": {"verified": True, "keys_down": [], "buttons_down": [],
             "reason": "release", "verified_ns": 126 * MS}, "terminal_ns": 127 * MS},
    ]


def test_pre_cancel_admission_late_ack_keeps_zero_lower_bound():
    row = analysis.reconstruct_holds(cancel_races_ack())[0]
    assert row["cancel_raced_input_ack"] is True
    assert row["admitted_keys"] == ["Down"]
    assert row["first_key_admitted_ns"] == 104 * MS
    assert row["first_key_ack_ns"] == 106 * MS
    assert row["physical_any_key_occupancy_lower_ms"] == 0.0
    assert row["physical_any_key_occupancy_upper_ms"] == 21.0
    assert row["exact_physical_duration_known"] is False


def test_admission_after_cancel_fails_closed():
    events = cancel_races_ack()
    events[3]["admitted_ns"] = 106 * MS
    try:
        analysis.reconstruct_holds(events)
    except AssertionError as exc:
        assert "input acknowledgement after cancellation" in str(exc)
    else:
        raise AssertionError("post-cancel admission must not be reclassified as an in-flight call")


def test_cancel_before_all_admissions_and_ack_after_cancel_is_bounded():
    events = cancel_races_ack()
    events.insert(4, {"event": "input_admission", "key": "space",
                      "admitted_ns": 104.5 * MS, "input_ack_ns": 107 * MS})
    row = analysis.reconstruct_holds(events)[0]
    assert row["admitted_keys"] == ["Down", "space"]
    assert row["physical_any_key_occupancy_lower_ms"] == 0.0
    assert row["physical_any_key_occupancy_upper_ms"] == 21.0


def test_window_intersection_uses_admission_and_release_not_late_ack():
    holds = analysis.reconstruct_holds(cancel_races_ack())
    report = {"decisions": [{"iteration": 0,
        "controller_model_started_ns": 103 * MS, "controller_model_ended_ns": 110 * MS,
        "cover_program_ids": ["p"]}]}
    row = analysis.base.decision_occupancy_bounds(report, holds)[0]
    assert row["physical_any_key_occupancy_lower_ms"] == 0.0
    assert row["physical_any_key_occupancy_upper_ms"] == 6.0


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items())
             if name.startswith("test_")]
    for test in tests:
        test()
    print(f"PASS {len(tests)} fulltrace-v4 tests")
