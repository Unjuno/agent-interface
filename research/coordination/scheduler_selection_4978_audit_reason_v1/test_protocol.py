"""Small deterministic construction checks; not a performance benchmark."""
import runner
import audit


def scenario(name, operations, horizon=10):
    return {"id": name, "horizon": horizon, "operations": operations}


def op(op_id, *, ready=0, duration=1, priority=0, deadline=100, deps=(), resources=()):
    return {"id": op_id, "seq": int(op_id[-1]) if op_id[-1].isdigit() else 0,
            "priority": priority, "deadline": deadline, "release": ready,
            "ready_at": 0, "deps": list(deps), "resource": resources[0] if resources else None}


def test_fifo_head_of_line_but_eligible_policies_dispatch_ready_work():
    s = scenario("hol", [op("A0", ready=0), op("B1")])
    s["operations"][0]["ready_at"] = 5
    fixture = {"locks_until": {}, "horizon": 10}
    assert runner.worker("hol", "FIFO_HEAD", 0, {**fixture, "scenarios": [s]})["trace"][0]["selected"] is None
    assert runner.worker("hol", "STABLE_LIST", 0, {**fixture, "scenarios": [s]})["trace"][0]["selected"] == "B1"
    assert runner.worker("hol", "ELIGIBLE_HEAP", 0, {**fixture, "scenarios": [s]})["trace"][0]["selected"] == "B1"


def test_dependency_and_resource_constraints():
    s = scenario("constraints", [op("A"), op("B", deps=("A",))])
    fixture = {"locks_until": {}, "horizon": 10}
    for policy in ("STABLE_LIST", "ELIGIBLE_HEAP"):
        trace = runner.worker("constraints", policy, 0, {**fixture, "scenarios": [s]})
        assert [d["selected"] for d in trace["trace"] if d["selected"]] == ["A", "B"]


def test_priority_tie_is_stable():
    s = scenario("ties", [op("A0", priority=2), op("B1", priority=2)])
    trace = runner.worker("ties", "ELIGIBLE_HEAP", 0, {"locks_until": {}, "horizon": 10, "scenarios": [s]})
    assert [d["selected"] for d in trace["trace"] if d["selected"]] == ["A0", "B1"]


def test_expiry_and_starvation_horizon_are_observable():
    s = scenario("expiry", [op("late", ready=0, deadline=1)])
    s["operations"][0]["ready_at"] = 2
    trace = runner.worker("expiry", "ELIGIBLE_HEAP", 0, {"locks_until": {}, "horizon": 10, "scenarios": [s]})
    assert trace["states"]["late"]["state"] == "expired"


def test_reference_trace_reason_matches_runner_contract():
    s = scenario("reason", [op("A0", ready=0), op("B1")])
    s["operations"][0]["ready_at"] = 5
    fixture = {"locks_until": {}, "horizon": 10}
    fifo = audit.reference_trace(s, fixture, "FIFO_HEAD")[0][0]
    stable = audit.reference_trace(s, fixture, "STABLE_LIST")[0][0]
    assert fifo["reason"] == "not_before"
    assert stable["reason"] == "priority_deadline_stable_seq"
    assert runner.worker("reason", "FIFO_HEAD", 0, {**fixture, "scenarios": [s]})["trace"][0] == fifo
    assert runner.worker("reason", "STABLE_LIST", 0, {**fixture, "scenarios": [s]})["trace"][0] == stable


if __name__ == "__main__":
    tests = [value for name, value in globals().items() if name.startswith("test_")]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"PASS {len(tests)} construction tests")
