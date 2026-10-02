import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "fulltrace_v3", HERE / "analyze_map01_held_input_occupancy_fulltrace_v3.py")
analysis = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(analysis)

MS = 1_000_000


def partial_cancel():
    return [
        {"event": "command", "command": {"op": "submit", "id": "p", "steps": [
            {"op": "hold", "keys": ["Down", "space"], "duration_ms": 300}]},
         "received_ns": 50 * MS},
        {"event": "step_started", "id": "p", "step": 0,
         "operation": "hold", "issued_ns": 100 * MS},
        {"event": "input_admission", "key": "Down", "admitted_ns": 105 * MS,
         "input_ack_ns": 106 * MS},
        {"event": "command", "command": {"op": "cancel", "id": "p"},
         "received_ns": 120 * MS},
        {"event": "terminal", "id": "p", "status": "cancelled", "steps_completed": 0,
         "interruption": {"record": {"verified": True, "keys_down": [],
             "buttons_down": [], "reason": "cancelled", "verified_ns": 125 * MS}},
         "release": {"verified": True, "keys_down": [], "buttons_down": [],
             "reason": "release", "verified_ns": 126 * MS}, "terminal_ns": 127 * MS},
    ]


def test_partial_key_acquisition_uses_zero_lower_and_verified_release_upper():
    row = analysis.reconstruct_holds(partial_cancel())[0]
    assert row["partial_admission_before_keys_held"] is True
    assert row["requested_keys"] == ["Down", "space"]
    assert row["admitted_keys"] == ["Down"]
    assert row["physical_any_key_occupancy_lower_ms"] == 0.0
    assert row["physical_any_key_occupancy_upper_ms"] == 20.0
    assert row["released_by_ns"] == 125 * MS
    assert row["exact_physical_duration_known"] is False


def test_cancel_before_first_admission_is_exact_zero():
    events = partial_cancel()
    events.pop(2)
    row = analysis.reconstruct_holds(events)[0]
    assert row["no_input_before_admission"] is True
    assert row["physical_any_key_occupancy_lower_ms"] == 0.0
    assert row["physical_any_key_occupancy_upper_ms"] == 0.0


def test_nonprefix_partial_admission_fails_closed():
    events = partial_cancel()
    events[2]["key"] = "space"
    try:
        analysis.reconstruct_holds(events)
    except AssertionError as exc:
        assert "ordered request prefix" in str(exc)
    else:
        raise AssertionError("non-prefix partial admission must be rejected")


def test_observation_during_incomplete_acquisition_fails_closed():
    events = partial_cancel()
    events.insert(3, {"event": "observation", "id": "p", "step": 0,
                      "capture_ns": 110 * MS})
    try:
        analysis.reconstruct_holds(events)
    except AssertionError as exc:
        assert "observation during incomplete" in str(exc)
    else:
        raise AssertionError("unmodeled in-acquisition observation must be rejected")


def test_partial_interval_intersection_with_model_wait():
    holds = analysis.reconstruct_holds(partial_cancel())
    report = {"decisions": [{"iteration": 0,
        "controller_model_started_ns": 110 * MS, "controller_model_ended_ns": 120 * MS,
        "cover_program_ids": ["p"]}]}
    row = analysis.decision_occupancy_bounds(report, holds)[0]
    assert row["physical_any_key_occupancy_lower_ms"] == 0.0
    assert row["physical_any_key_occupancy_upper_ms"] == 10.0


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items())
             if name.startswith("test_")]
    for test in tests:
        test()
    print(f"PASS {len(tests)} fulltrace-v3 tests")
