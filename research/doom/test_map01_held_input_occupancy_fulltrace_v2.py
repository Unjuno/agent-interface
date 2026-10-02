import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "fulltrace_v2", HERE / "analyze_map01_held_input_occupancy_fulltrace_v2.py")
analysis = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(analysis)

MS = 1_000_000


def no_input_cancel():
    return [
        {"event": "command", "command": {"op": "submit", "id": "p", "steps": [
            {"op": "hold", "keys": ["Down", "space"], "duration_ms": 300}]},
         "received_ns": 50 * MS},
        {"event": "step_started", "id": "p", "step": 0,
         "operation": "hold", "issued_ns": 100 * MS},
        {"event": "command", "command": {"op": "cancel", "id": "p"},
         "received_ns": 120 * MS},
        {"event": "terminal", "id": "p", "status": "cancelled", "steps_completed": 0,
         "interruption": {"record": {"verified": True, "keys_down": [],
             "buttons_down": [], "reason": "cancelled", "verified_ns": 125 * MS}},
         "release": {"verified": True, "keys_down": [], "buttons_down": [],
             "reason": "release", "verified_ns": 126 * MS}, "terminal_ns": 127 * MS},
    ]


def test_cancel_before_first_admission_is_zero_occupancy():
    row = analysis.reconstruct_holds(no_input_cancel())[0]
    assert row["no_input_before_admission"] is True
    assert row["requested_keys"] == ["Down", "space"]
    assert row["physical_any_key_occupancy_lower_ms"] == 0.0
    assert row["physical_any_key_occupancy_upper_ms"] == 0.0
    assert row["released_by_ns"] == 125 * MS


def test_cancel_after_focus_release_is_not_zero_input_cancellation():
    events = no_input_cancel()
    events[-1]["interruption"]["record"]["reason"] = "focus_changed"
    try:
        analysis.reconstruct_holds(events)
    except AssertionError as exc:
        assert "not proven zero-input cancellation" in str(exc)
    else:
        raise AssertionError("asynchronous release must not satisfy cancel contract")


def test_partial_input_admission_fails_closed():
    events = no_input_cancel()
    events.insert(2, {"event": "input_admission", "key": "Down",
                      "admitted_ns": 105 * MS, "input_ack_ns": 106 * MS})
    try:
        analysis.reconstruct_holds(events)
    except AssertionError as exc:
        assert "partial/unacknowledged input" in str(exc)
    else:
        raise AssertionError("partial input requires a distinct conservative bound")


def test_no_input_row_contributes_zero_model_wait_occupancy():
    holds = analysis.reconstruct_holds(no_input_cancel())
    report = {"decisions": [{"iteration": 0,
        "controller_model_started_ns": 90 * MS, "controller_model_ended_ns": 150 * MS,
        "cover_program_ids": ["p"]}]}
    row = analysis.decision_occupancy_bounds(report, holds)[0]
    assert row["model_wait_ms"] == 60.0
    assert row["physical_any_key_occupancy_lower_ms"] == 0.0
    assert row["physical_any_key_occupancy_upper_ms"] == 0.0
    assert row["hold_steps"] == ["p:0"]


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items())
             if name.startswith("test_")]
    for test in tests:
        test()
    print(f"PASS {len(tests)} fulltrace-v2 tests")
