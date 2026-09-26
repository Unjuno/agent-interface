"""Independent replay audit against exact pinned main guard sources."""
import copy
import hashlib


EXPECTED = {
    "raw_mixed_domain": ("REJECTED_STALE", "CANCEL_REQUIRED", False, True),
    "conservative_same_session_translation": ("VALID_CURRENT", "INPUT_ACTIVE", True, False),
    "translated_31s_older_control": ("REJECTED_STALE", "CANCEL_REQUIRED", False, True),
}


def _fail(condition, message):
    if not condition:
        raise AssertionError(message)


def audit(clock_result, replay, validity_module, guard_class):
    _fail(replay["format"] == "clock-calibrated-action-validity-guard-replay-v1",
          "replay format mismatch")
    _fail(replay["classification"] == "DETERMINISTIC_REPLAY_ONLY",
          "scope classification mismatch")
    _fail(replay["source_blobs"] == {
        "action_validity_admission_v1.py": "31bd30bd9baf6b7d56494cc3a18b2c6c70ffbc5e",
        "running_action_guard_v1.py": "d54047e78bc76f53ef47c6f70fd4a3be6318f09c",
    }, "source blob provenance mismatch")
    _fail(replay["source_sha256"] == {
        "action_validity_admission_v1.py": "f102cbde4f0e46c9f8e974e9f0a7d1c47f3fc662d7c8ba32699d16799d3db98a",
        "running_action_guard_v1.py": "2d5feb69efd59fdca22e0db9e561923411490eb758eab9e2b8379714e20e5c62",
    }, "source hash provenance mismatch")
    _fail(replay["clock_result_sha256"] == clock_result["artifact_sha256"],
          "retained clock result identity mismatch")
    _fail(replay["container_image"] == clock_result["image"],
          "container image mismatch")
    samples = clock_result["samples"]
    _fail(len(samples) == 3, "exactly three retained samples required")
    lows, highs = [], []
    for row in samples:
        _fail(row["host_after_ns"] >= row["host_before_ns"],
              "invalid bracket order")
        lows.append(row["host_before_ns"] - row["container_capture_ns"])
        highs.append(row["host_after_ns"] - row["container_capture_ns"])
    lower, upper = max(lows), min(highs)
    _fail([lower, upper] == replay["offset_interval_host_minus_container_ns"],
          "offset intersection mismatch")
    _fail(upper >= lower, "empty common offset interval")
    _fail(upper - lower == replay["offset_uncertainty_ns"],
          "uncertainty mismatch")
    _fail(replay["offset_uncertainty_ns"] <= 1_000_000_000,
          "uncertainty exceeds gate")
    decision_ns = clock_result["controller_decided_ns"]
    _fail(replay["controller_decided_ns"] == decision_ns,
          "decision timestamp mismatch")
    raw = samples[-1]["container_capture_ns"]
    translated = raw + lower
    expected_capture = {
        "raw_mixed_domain": raw,
        "conservative_same_session_translation": translated,
        "translated_31s_older_control": translated - 31_000_000_000,
    }
    _fail(len(replay["observations"]) == 3, "three guard arms required")
    for row in replay["observations"]:
        case = row["case"]
        _fail(case in EXPECTED, "unexpected guard case")
        inputs = row["inputs"]
        _fail(inputs["current_snapshot"]["capture_ns"] == expected_capture[case],
              "current snapshot capture mismatch")
        _fail(inputs["current_snapshot"]["sequence"] == 3,
              "current snapshot sequence mismatch")
        _fail(inputs["current_controller_decided_ns"] == decision_ns,
              "guard decision operand mismatch")
        _fail(inputs["executor_process_started"] is False and
              inputs["physical_input_sent"] is False and
              inputs["model_call_made"] is False,
              "scope violation recorded in fixture")
        initial = validity_module.evaluate_action_validity(
            inputs["action"], inputs["contract"], inputs["initial_snapshot"],
            inputs["initial_controller_decided_ns"])
        _fail(initial == inputs["initial_validity"],
              "initial validity receipt does not recompute")
        guard = guard_class(inputs["action"], inputs["contract"], initial)
        guard.admit_program(inputs["accepted_program_fixture"])
        guard.check_current(inputs["current_snapshot"],
                            inputs["current_controller_decided_ns"])
        recomputed = guard.receipt()
        _fail(recomputed == row["full_running_action_guard_receipt"],
              "full guard receipt does not replay from exact sources")
        derived = row["derived"]
        actual = recomputed["validity_checks"][-1]
        expected_status, expected_state, expected_authority, expected_new_decision = EXPECTED[case]
        _fail(actual["status"] == expected_status, "unexpected validator status")
        _fail(recomputed["state"] == expected_state, "unexpected guard state")
        _fail(recomputed["current_input_authority"] is expected_authority,
              "unexpected guard authority")
        _fail(recomputed["requires_new_decision"] is expected_new_decision,
              "unexpected decision requirement")
        _fail(derived["validity_status"] == actual["status"] and
              derived["validity_reason"] == actual["reason"] and
              derived["guard_state"] == recomputed["state"] and
              derived["current_input_authority"] == recomputed["current_input_authority"] and
              derived["requires_new_decision"] == recomputed["requires_new_decision"],
              "hand-derived summary disagrees with full receipts")
        _fail(derived["apparent_age_ns"] ==
              decision_ns - inputs["current_snapshot"]["capture_ns"],
              "apparent-age arithmetic mismatch")
    _fail({row["case"] for row in replay["observations"]} == set(EXPECTED),
          "case set incomplete")
    return True


def corruption_controls(clock_result, replay, validity_module, guard_class):
    mutations = (
        lambda value: value["observations"][0]["inputs"]["current_snapshot"].update(
            capture_ns=value["observations"][0]["inputs"]["current_snapshot"]["capture_ns"] + 1),
        lambda value: value["observations"][1]["full_running_action_guard_receipt"].update(
            state="CANCEL_REQUIRED"),
        lambda value: value["observations"][2]["inputs"].update(
            current_controller_decided_ns=value["controller_decided_ns"] - 31_000_000_000),
        lambda value: value["observations"][0]["inputs"].update(
            physical_input_sent=True),
    )
    for mutate in mutations:
        changed = copy.deepcopy(replay)
        mutate(changed)
        try:
            audit(clock_result, changed, validity_module, guard_class)
        except (AssertionError, KeyError, TypeError, ValueError):
            continue
        raise AssertionError("corrupted replay was accepted")
    return len(mutations)
