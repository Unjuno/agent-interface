"""Independent recomputation of retained guard-replay inputs and receipts."""
import argparse
import copy
import hashlib
import json
from pathlib import Path


EXPECTED = {
    "raw_mixed_domain": ("REJECTED_STALE", "CANCEL_REQUIRED", False, True),
    "conservative_same_session_translation": ("VALID_CURRENT", "INPUT_ACTIVE", True, False),
    "translated_31s_older_control": ("REJECTED_STALE", "CANCEL_REQUIRED", False, True),
}
ACTION = [{"action": "advance_fire", "extent": "long"}]
BINDING = {"focus": 7, "surface": 8, "geometry": [0, 0, 640, 480]}
SIGNALS = {"health": {"status": "observed", "value": 90},
           "ammo": {"status": "observed", "value": 12}}
SOURCE_BLOBS = {
    "action_validity_admission_v1.py": "31bd30bd9baf6b7d56494cc3a18b2c6c70ffbc5e",
    "running_action_guard_v1.py": "d54047e78bc76f53ef47c6f70fd4a3be6318f09c",
}
SOURCE_SHA256 = {
    "action_validity_admission_v1.py": "f102cbde4f0e46c9f8e974e9f0a7d1c47f3fc662d7c8ba32699d16799d3db98a",
    "running_action_guard_v1.py": "2d5feb69efd59fdca22e0db9e561923411490eb758eab9e2b8379714e20e5c62",
}
SOURCE_COMMIT = "91b5143989403754b360738c445f72b68b673718"


def _fail(condition, message):
    if not condition:
        raise AssertionError(message)


def _snapshot(sequence, capture_ns):
    return {"format": "action-admission-snapshot-v1",
            "sequence": sequence, "capture_ns": capture_ns,
            "binding": BINDING, "signals": SIGNALS}


def audit(clock_result, replay, validity_module, guard_class,
          clock_result_sha256):
    _fail(replay["format"] == "clock-calibrated-action-validity-guard-replay-v1",
          "replay format mismatch")
    _fail(replay["classification"] == "DETERMINISTIC_REPLAY_ONLY",
          "scope classification mismatch")
    _fail(replay["source_commit"] == SOURCE_COMMIT, "source commit mismatch")
    _fail(replay["source_blobs"] == SOURCE_BLOBS, "source blob mismatch")
    _fail(replay["source_sha256"] == SOURCE_SHA256, "source SHA-256 mismatch")
    _fail(replay["clock_result_sha256"] == clock_result_sha256,
          "retained clock result identity mismatch")
    _fail(replay["container_image"] == clock_result["image"],
          "container image mismatch")
    _fail(replay["platform"] == "linux/arm64" and
          replay["network"] == "none" and replay["read_only_root"] is True,
          "container constraints mismatch")
    _fail(replay["clock_result_experiment"] ==
          "clock_calibrated_action_validity_4544_v1", "clock source mismatch")
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
    _fail(upper - lower == replay["offset_uncertainty_ns"] <= 1_000_000_000,
          "offset width mismatch/exceeds gate")
    decision_ns = clock_result["controller_decided_ns"]
    _fail(replay["controller_decided_ns"] == decision_ns,
          "decision timestamp mismatch")
    raw = samples[-1]["container_capture_ns"]
    translated = raw + lower
    captures = {
        "raw_mixed_domain": raw,
        "conservative_same_session_translation": translated,
        "translated_31s_older_control": translated - 31_000_000_000,
    }
    observations = replay["observations"]
    _fail(len(observations) == 3, "three guard arms required")
    _fail({row["case"] for row in observations} == set(EXPECTED),
          "case set mismatch")
    for row in observations:
        case = row["case"]
        inputs = row["inputs"]
        current_capture = captures[case]
        source_capture = current_capture - 100_000_000
        expected_contract = {
            "format": "action-validity-contract-v1",
            "action_fingerprint": validity_module.action_fingerprint(ACTION),
            "source": {"sequence": 1, "capture_ns": source_capture - 1,
                       "binding": BINDING, "signals": SIGNALS},
            "max_current_age_ms": 30_000,
            "predicates": [
                {"signal_id": "health", "operator": "minimum", "value": 50},
                {"signal_id": "ammo", "operator": "minimum", "value": 1},
            ],
        }
        initial_snapshot = _snapshot(2, source_capture)
        initial_decision_ns = source_capture + 1_000
        current_snapshot = _snapshot(3, current_capture)
        accepted_fixture = {"event": "accepted", "id": "p1",
                            "accepted_ns": source_capture + 2_000}
        _fail(inputs["action"] == ACTION, "action fixture mismatch")
        _fail(inputs["contract"] == expected_contract, "contract fixture mismatch")
        _fail(inputs["initial_snapshot"] == initial_snapshot,
              "initial snapshot fixture mismatch")
        _fail(inputs["initial_controller_decided_ns"] == initial_decision_ns,
              "initial decision mismatch")
        _fail(inputs["accepted_program_fixture"] == accepted_fixture,
              "accepted-program fixture mismatch")
        _fail(inputs["current_snapshot"] == current_snapshot,
              "current snapshot fixture mismatch")
        _fail(inputs["current_controller_decided_ns"] == decision_ns,
              "current decision mismatch")
        _fail(inputs["executor_process_started"] is False and
              inputs["physical_input_sent"] is False and
              inputs["model_call_made"] is False,
              "scope violation in stored inputs")
        initial = validity_module.evaluate_action_validity(
            inputs["action"], inputs["contract"], inputs["initial_snapshot"],
            inputs["initial_controller_decided_ns"])
        _fail(initial == inputs["initial_validity"],
              "initial validity receipt does not recompute")
        guard = guard_class(inputs["action"], inputs["contract"], initial)
        guard.admit_program(inputs["accepted_program_fixture"])
        guard.check_current(inputs["current_snapshot"],
                            inputs["current_controller_decided_ns"])
        receipt = guard.receipt()
        _fail(receipt == row["full_running_action_guard_receipt"],
              "complete guard receipt does not recompute from pinned sources")
        validity = receipt["validity_checks"][-1]
        status, state, authority, requires_new = EXPECTED[case]
        _fail(validity["status"] == status, "validator status mismatch")
        _fail(receipt["state"] == state, "guard state mismatch")
        _fail(receipt["current_input_authority"] is authority,
              "guard authority mismatch")
        _fail(receipt["requires_new_decision"] is requires_new,
              "decision requirement mismatch")
        summary = row["derived"]
        _fail(summary["apparent_age_ns"] ==
              decision_ns - current_capture, "age arithmetic mismatch")
        _fail(summary["validity_status"] == validity["status"] and
              summary["validity_reason"] == validity["reason"] and
              summary["guard_state"] == receipt["state"] and
              summary["current_input_authority"] ==
              receipt["current_input_authority"] and
              summary["requires_new_decision"] ==
              receipt["requires_new_decision"],
              "summary differs from recomputed receipt")
    return True


def corruption_controls(clock_result, replay, validity_module, guard_class,
                        clock_result_sha256):
    mutations = (
        lambda value: value["observations"][0]["inputs"]["current_snapshot"].update(
            capture_ns=value["observations"][0]["inputs"]["current_snapshot"]["capture_ns"] + 1),
        lambda value: value["observations"][1]["full_running_action_guard_receipt"].update(
            state="CANCEL_REQUIRED"),
        lambda value: value["observations"][2]["inputs"].update(
            current_controller_decided_ns=value["controller_decided_ns"] - 31_000_000_000),
        lambda value: value["observations"][0]["inputs"].update(physical_input_sent=True),
        lambda value: value["observations"][2]["inputs"]["contract"]["predicates"].clear(),
    )
    for mutate in mutations:
        changed = copy.deepcopy(replay)
        mutate(changed)
        try:
            audit(clock_result, changed, validity_module, guard_class,
                  clock_result_sha256)
        except (AssertionError, KeyError, TypeError, ValueError):
            continue
        raise AssertionError("corrupted replay was accepted")
    return len(mutations)


def load_production(repo_root):
    import sys
    source_dir = Path(repo_root) / "research" / "live_control"
    for filename in SOURCE_BLOBS:
        content = (source_dir / filename).read_bytes()
        git_blob_sha = hashlib.sha1(
            b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
        _fail(git_blob_sha == SOURCE_BLOBS[filename], "Git blob mismatch: " + filename)
        _fail(hashlib.sha256(content).hexdigest() == SOURCE_SHA256[filename],
              "SHA-256 mismatch: " + filename)
    sys.path.insert(0, str(source_dir))
    from action_validity_admission_v1 import evaluate_action_validity, action_fingerprint
    from running_action_guard_v1 import RunningActionGuard
    class ValidityModule:
        pass
    module = ValidityModule()
    module.evaluate_action_validity = evaluate_action_validity
    module.action_fingerprint = action_fingerprint
    return module, RunningActionGuard


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--clock-result", required=True)
    parser.add_argument("--replay", required=True)
    args = parser.parse_args()
    validity, guard = load_production(args.repo_root)
    clock_bytes = Path(args.clock_result).read_bytes()
    clock_result = json.loads(clock_bytes)
    replay = json.loads(Path(args.replay).read_bytes())
    clock_hash = hashlib.sha256(clock_bytes).hexdigest()
    audit(clock_result, replay, validity, guard, clock_hash)
    rejected = corruption_controls(clock_result, replay, validity, guard, clock_hash)
    print(json.dumps({"audit": "PASS_FULL_RECEIPT_REPLAY",
                      "corruption_rejections": rejected}, sort_keys=True))


if __name__ == "__main__":
    main()
