import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "held", HERE / "analyze_map01_held_input_occupancy_v1.py")
held = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(held)

MS = 1_000_000

def submit(identifier, keys, duration=200):
    return {"event":"command","command":{"op":"submit","id":identifier,
        "steps":[{"op":"hold","keys":keys,"duration_ms":duration}]},"received_ns":1}

def normal_events():
    return [
        submit("p", ["a","space"]),
        {"event":"step_started","id":"p","step":0,"operation":"hold","issued_ns":100*MS},
        {"event":"input_admission","key":"a","admitted_ns":110*MS,"input_ack_ns":112*MS},
        {"event":"input_admission","key":"space","admitted_ns":113*MS,"input_ack_ns":115*MS},
        {"event":"keys_held","id":"p","step":0,"keys":["a","space"],"input_ack_ns":116*MS},
        {"event":"observation","id":"p","step":0,"capture_ns":200*MS},
        {"event":"observation","id":"p","step":0,"capture_ns":300*MS},
        {"event":"step_completed","id":"p","step":0,"completed_ns":350*MS},
        {"event":"terminal","id":"p","status":"completed","release":
            {"verified":True,"keys_down":[],"verified_ns":360*MS},"terminal_ns":361*MS},
    ]

def cancelled_events():
    return [
        submit("p", ["a"], 500),
        {"event":"step_started","id":"p","step":0,"operation":"hold","issued_ns":100*MS},
        {"event":"input_admission","key":"a","admitted_ns":110*MS,"input_ack_ns":112*MS},
        {"event":"keys_held","id":"p","step":0,"keys":["a"],"input_ack_ns":113*MS},
        {"event":"observation","id":"p","step":0,"capture_ns":200*MS},
        {"event":"command","command":{"op":"cancel","id":"p"},"received_ns":250*MS},
        {"event":"cancel_requested","id":"p","matched":True,"requested_ns":255*MS},
        {"event":"input_released","id":"p","owner_release":
            {"verified":True,"keys_down":[],"reason":"cancelled","verified_ns":280*MS}},
        {"event":"terminal","id":"p","status":"cancelled","interruption":{"record":
            {"verified":True,"keys_down":[],"reason":"cancelled","verified_ns":280*MS}},"release":
            {"verified":True,"keys_down":[],"reason":"release","verified_ns":320*MS},"terminal_ns":321*MS},
    ]

def async_release_events():
    events = cancelled_events()
    events = [row for row in events if not (row.get("event") == "command" and row.get("command",{}).get("op") == "cancel")]
    for row in events:
        if row.get("event") == "terminal":
            row["status"] = "expired"
            if row.get("interruption"):
                row["interruption"]["record"]["reason"] = "expired"
        if row.get("event") == "input_released":
            row["owner_release"]["reason"] = "expired"
    return events

def cancelled_after_focus_release_events():
    events = cancelled_events()
    for row in events:
        if row.get("event") == "input_released":
            row["owner_release"]["reason"] = "focus_changed"
            row["owner_release"]["verified_ns"] = 210*MS
        if row.get("event") == "terminal":
            row["interruption"]["record"]["reason"] = "focus_changed"
            row["interruption"]["record"]["verified_ns"] = 210*MS
    return events

def retained_v39_cancel_sample():
    # Exact timestamps copied from BASE bc21199 retained raw v39 events:
    # research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl
    return [
        {"event":"command","command":{"op":"submit","id":"plan-3-primary-0-1",
            "steps":[{"op":"hold","keys":["Down","space"],"duration_ms":500},
                     {"op":"hold","keys":["a"],"duration_ms":350}]},
         "received_ns":55531888988407},
        {"event":"step_started","id":"plan-3-primary-0-1","step":0,
         "operation":"hold","issued_ns":55531909404452},
        {"event":"input_admission","key":"Down","admitted_ns":55531922546329,
         "input_ack_ns":55531922893265},
        {"event":"input_admission","key":"space","admitted_ns":55531936554866,
         "input_ack_ns":55531936828861},
        {"event":"keys_held","id":"plan-3-primary-0-1","step":0,
         "keys":["Down","space"],"input_ack_ns":55531947530392},
        {"event":"observation","id":"plan-3-primary-0-1","step":0,
         "sequence":114,"capture_ns":55531965617433},
        {"event":"observation","id":"plan-3-primary-0-1","step":0,
         "sequence":115,"capture_ns":55532110564498},
        {"event":"command","command":{"op":"cancel","id":"plan-3-primary-0-1"},
         "received_ns":55532135752840},
        {"event":"input_released","id":"plan-3-primary-0-1",
         "owner_release":{"verified":True,"keys_down":[],"buttons_down":[],
             "reason":"cancelled","verified_ns":55532149408597}},
        {"event":"terminal","id":"plan-3-primary-0-1","status":"cancelled",
         "interruption":{"record":{"verified":True,"keys_down":[],"buttons_down":[],
             "reason":"cancelled","verified_ns":55532149408597}},
         "release":{"verified":True,"keys_down":[],"buttons_down":[],
             "reason":"release","verified_ns":55532202283558},
         "terminal_ns":55532202369534},
    ]

def test_normal_interval():
    row = held.reconstruct_holds(normal_events())[0]
    assert row["physical_any_key_occupancy_lower_ms"] == 88.0
    assert row["physical_any_key_occupancy_upper_ms"] == 190.0
    assert row["occupancy_interval_width_ms"] == 102.0
    assert row["confirmed_any_key_held_until_ns"] == 200*MS
    assert row["released_by_ns"] == 300*MS
    assert not row["exact_physical_duration_known"]

def test_cancel_interval_uses_precancel_capture_and_earliest_verified_release():
    row = held.reconstruct_holds(cancelled_events())[0]
    assert row["physical_any_key_occupancy_lower_ms"] == 88.0
    assert row["physical_any_key_occupancy_upper_ms"] == 170.0
    assert row["released_by_ns"] == 280*MS

def test_async_release_does_not_overclaim_observation_as_held():
    row = held.reconstruct_holds(async_release_events())[0]
    assert row["confirmed_any_key_held_until_ns"] == 112*MS
    assert row["physical_any_key_occupancy_lower_ms"] == 0.0
    assert row["physical_any_key_occupancy_upper_ms"] == 170.0

def test_cancel_status_after_focus_release_stays_conservative():
    row = held.reconstruct_holds(cancelled_after_focus_release_events())[0]
    assert row["release_reason"] == "focus_changed"
    assert row["confirmed_any_key_held_until_ns"] == 112*MS
    assert row["physical_any_key_occupancy_lower_ms"] == 0.0

def test_retained_v39_cancel_sample_bounds():
    row = held.reconstruct_holds(retained_v39_cancel_sample())[0]
    assert row["release_reason"] == "cancelled"
    assert row["confirmed_any_key_held_until_ns"] == 55532110564498
    assert row["released_by_ns"] == 55532149408597
    assert row["physical_any_key_occupancy_lower_ms"] == 187.671
    assert row["physical_any_key_occupancy_upper_ms"] == 226.862
    assert row["occupancy_interval_width_ms"] == 39.191

def test_model_wait_intersection_is_bounded():
    holds = held.reconstruct_holds(normal_events())
    report = {"decisions":[{"iteration":0,"controller_model_started_ns":150*MS,
        "controller_model_ended_ns":280*MS,"cover_program_ids":["p"]}]}
    row = held.decision_occupancy_bounds(report, holds)[0]
    assert row["physical_any_key_occupancy_lower_ms"] == 50.0
    assert row["physical_any_key_occupancy_upper_ms"] == 130.0
    assert row["occupancy_interval_width_ms"] == 80.0

def test_admission_order_mismatch_fails_closed():
    events = normal_events()
    events[2], events[3] = events[3], events[2]
    try:
        held.reconstruct_holds(events)
    except AssertionError as exc:
        assert "input admissions do not match" in str(exc)
    else:
        raise AssertionError("mismatched admission order must fail")

if __name__ == "__main__":
    tests = [value for name,value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"PASS {len(tests)} tests")
