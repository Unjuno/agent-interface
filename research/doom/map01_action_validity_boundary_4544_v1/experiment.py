"""Small construction experiment for the #4544 action-validity time boundary.

Uses the exact current-main guard and validator; does not launch ViZDoom,
submit input, or mutate their source. All timestamps are deterministic fixture
values, so this tests boundary semantics, not the cause of the consumed run.
"""
import json

from test_running_action_guard_v1 import guard, accepted, snapshot, terminal


def main():
    rows = []
    cases = (
        ("active_decision_after_capture", "active", 3, 300, 301),
        ("active_decision_equal_capture", "active", 3, 300, 300),
        ("active_decision_one_ns_before_capture", "active", 3, 300, 299),
    )
    for name, phase, sequence, capture, decided in cases:
        subject = guard()
        subject.admit_program(accepted())
        try:
            receipt = subject.check_current(snapshot(sequence, capture), decided)
            rows.append({"case": name, "phase": phase, "outcome": "receipt",
                         "state": receipt["state"],
                         "current_input_authority": receipt["current_input_authority"],
                         "invalidation": receipt["invalidation"],
                         "requires_new_decision": receipt["requires_new_decision"]})
        except Exception as exc:
            receipt = subject.receipt()
            rows.append({"case": name, "phase": phase, "outcome": "exception",
                         "exception_type": type(exc).__name__, "message": str(exc),
                         "state_after": receipt["state"],
                         "current_input_authority_after": receipt["current_input_authority"],
                         "invalidation_after": receipt["invalidation"]})

    subject = guard()
    subject.admit_program(accepted())
    subject.check_current(snapshot(3, 300), 301)
    subject.record_completed_terminal(terminal("p1", "completed", 310), final=False)
    try:
        receipt = subject.check_current(snapshot(4, 315), 314)
        rows.append({"case": "between_decision_one_ns_before_capture",
                     "phase": "between", "outcome": "receipt",
                     "state": receipt["state"],
                     "current_input_authority": receipt["current_input_authority"],
                     "invalidation": receipt["invalidation"],
                     "requires_new_decision": receipt["requires_new_decision"]})
    except Exception as exc:
        receipt = subject.receipt()
        rows.append({"case": "between_decision_one_ns_before_capture",
                     "phase": "between", "outcome": "exception",
                     "exception_type": type(exc).__name__, "message": str(exc),
                     "state_after": receipt["state"],
                     "current_input_authority_after": receipt["current_input_authority"],
                     "invalidation_after": receipt["invalidation"]})

    active = [row for row in rows if row["phase"] == "active"]
    inverted_active = next(row for row in active
                           if row["case"] == "active_decision_one_ns_before_capture")
    inverted_between = rows[-1]
    passed = (
        all(row["outcome"] == "receipt" and row["state"] == "INPUT_ACTIVE" and
            row["current_input_authority"] is True for row in active[:2]) and
        inverted_active["outcome"] == "receipt" and
        inverted_active["current_input_authority"] is False and
        inverted_active["invalidation"] is not None and
        inverted_active["requires_new_decision"] is True and
        inverted_between["outcome"] == "receipt" and
        inverted_between["current_input_authority"] is False and
        inverted_between["invalidation"] is not None and
        inverted_between["requires_new_decision"] is True)
    print(json.dumps({
        "experiment": "map01-action-validity-time-boundary-v1",
        "classification": ("PASS_GUARD_LOCAL_FAIL_CLOSED_BOUNDARY" if passed else
                           "FAIL_GUARD_LOCAL_FAIL_CLOSED_BOUNDARY"),
        "provenance": {
            "main_commit": "a778bdd577b149a5ec964bbe19da533311335e2f",
            "source_blobs": {
                "action_validity_admission_v1.py": "31bd30bd9baf6b7d56494cc3a18b2c6c70ffbc5e",
                "running_action_guard_v1.py": "d54047e78bc76f53ef47c6f70fd4a3be6318f09c",
                "test_running_action_guard_v1.py": "a4a423da1118f2da8cca08e9965419fac322461a",
                "test_action_validity_admission_v1.py": "9d5dbf119fcb56c75ac1732da60b18832876e1a5"},
            "container_image": "issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e",
            "platform": "linux/arm64", "network": "none",
            "root_filesystem": "read-only", "source_mount": "read-only"},
        "scope": "deterministic synthetic timestamps against exact current-main guard; no formal allocation/game/model/input",
        "rows": rows}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
