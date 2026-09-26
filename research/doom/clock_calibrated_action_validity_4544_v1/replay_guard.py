"""Replay full exact-main RunningActionGuard receipts from retained clocks.

No new clock probe is made. The accepted-program object is a deterministic
fixture input to the guard, not an actual Executor event or physical action.
"""
import argparse
import hashlib
import json
from pathlib import Path


SOURCE_COMMIT = "342d11c09e8cb8fe5cf8677d285b5ef616050539"
SOURCE_BLOBS = {
    "action_validity_admission_v1.py": "31bd30bd9baf6b7d56494cc3a18b2c6c70ffbc5e",
    "running_action_guard_v1.py": "d54047e78bc76f53ef47c6f70fd4a3be6318f09c",
}
SOURCE_SHA256 = {
    "action_validity_admission_v1.py": "f102cbde4f0e46c9f8e974e9f0a7d1c47f3fc662d7c8ba32699d16799d3db98a",
    "running_action_guard_v1.py": "2d5feb69efd59fdca22e0db9e561923411490eb758eab9e2b8379714e20e5c62",
}
MAX_CURRENT_AGE_MS = 30_000
ACTION = [{"action": "advance_fire", "extent": "long"}]
BINDING = {"focus": 7, "surface": 8, "geometry": [0, 0, 640, 480]}
SIGNALS = {"health": {"status": "observed", "value": 90},
           "ammo": {"status": "observed", "value": 12}}


def snapshot(sequence, capture_ns):
    return {"format": "action-admission-snapshot-v1",
            "sequence": sequence, "capture_ns": capture_ns,
            "binding": BINDING, "signals": SIGNALS}


def build_replay(clock_result, validity_module, guard_class, clock_result_sha256):
    samples = clock_result["samples"]
    lower, upper = clock_result["common_offset_host_minus_container_ns"]
    raw_capture = samples[-1]["container_capture_ns"]
    translated_capture = raw_capture + lower
    decision_ns = clock_result["controller_decided_ns"]
    cases = [
        ("raw_mixed_domain", raw_capture),
        ("conservative_same_session_translation", translated_capture),
        ("translated_31s_older_control", translated_capture - 31_000_000_000),
    ]
    observations = []
    for case_id, current_capture in cases:
        source_capture = current_capture - 100_000_000
        contract = {
            "format": "action-validity-contract-v1",
            "action_fingerprint": validity_module.action_fingerprint(ACTION),
            "source": {"sequence": 1, "capture_ns": source_capture - 1,
                       "binding": BINDING, "signals": SIGNALS},
            "max_current_age_ms": MAX_CURRENT_AGE_MS,
            "predicates": [
                {"signal_id": "health", "operator": "minimum", "value": 50},
                {"signal_id": "ammo", "operator": "minimum", "value": 1},
            ],
        }
        initial_snapshot = snapshot(2, source_capture)
        initial_decision_ns = source_capture + 1_000
        initial_validity = validity_module.evaluate_action_validity(
            ACTION, contract, initial_snapshot, initial_decision_ns)
        accepted_fixture = {"event": "accepted", "id": "p1",
                            "accepted_ns": source_capture + 2_000}
        current_snapshot = snapshot(3, current_capture)
        inputs = {
            "action": ACTION,
            "contract": contract,
            "initial_snapshot": initial_snapshot,
            "initial_controller_decided_ns": initial_decision_ns,
            "initial_validity": initial_validity,
            "accepted_program_fixture": accepted_fixture,
            "current_snapshot": current_snapshot,
            "current_controller_decided_ns": decision_ns,
            "executor_process_started": False,
            "physical_input_sent": False,
            "model_call_made": False,
        }
        guard = guard_class(ACTION, contract, initial_validity)
        guard.admit_program(accepted_fixture)
        guard.check_current(current_snapshot, decision_ns)
        receipt = guard.receipt()
        last_validity = receipt["validity_checks"][-1]
        observations.append({
            "case": case_id,
            "inputs": inputs,
            "full_running_action_guard_receipt": receipt,
            "derived": {
                "apparent_age_ns": decision_ns - current_capture,
                "validity_status": last_validity["status"],
                "validity_reason": last_validity["reason"],
                "guard_state": receipt["state"],
                "current_input_authority": receipt["current_input_authority"],
                "requires_new_decision": receipt["requires_new_decision"],
                "invalidation_kind": (None if receipt["invalidation"] is None
                                      else receipt["invalidation"]["kind"]),
            },
        })
    return {
        "format": "clock-calibrated-action-validity-guard-replay-v1",
        "classification": "DETERMINISTIC_REPLAY_ONLY",
        "source_commit": SOURCE_COMMIT,
        "source_blobs": SOURCE_BLOBS,
        "source_sha256": SOURCE_SHA256,
        "clock_result_sha256": clock_result_sha256,
        "clock_result_experiment": clock_result["experiment"],
        "container_image": clock_result["image"],
        "platform": clock_result["platform"],
        "network": clock_result["network"],
        "read_only_root": clock_result["root_read_only"],
        "max_current_age_ms": MAX_CURRENT_AGE_MS,
        "offset_interval_host_minus_container_ns": [lower, upper],
        "offset_uncertainty_ns": upper - lower,
        "controller_decided_ns": decision_ns,
        "observations": observations,
        "scope": ("Re-executes the exact-main guard using retained clock values and "
                  "explicit deterministic fixture inputs. This does not recover the "
                  "original invocation's unretained inputs/receipts, read a WAD, "
                  "or create a physical Executor action."),
    }


def load_production(repo_root):
    import sys
    source_dir = Path(repo_root) / "research" / "live_control"
    for filename in SOURCE_BLOBS:
        content = (source_dir / filename).read_bytes()
        git_blob_sha = hashlib.sha1(
            b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
        if git_blob_sha != SOURCE_BLOBS[filename]:
            raise RuntimeError(f"main source blob mismatch: {filename}")
        if hashlib.sha256(content).hexdigest() != SOURCE_SHA256[filename]:
            raise RuntimeError(f"main source SHA-256 mismatch: {filename}")
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
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    validity_module, guard_class = load_production(args.repo_root)
    clock_bytes = Path(args.clock_result).read_bytes()
    clock_result = json.loads(clock_bytes)
    payload = build_replay(
        clock_result, validity_module, guard_class,
        hashlib.sha256(clock_bytes).hexdigest())
    Path(args.out).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"classification": payload["classification"],
                      "cases": len(payload["observations"]),
                      "output": args.out}, sort_keys=True))


if __name__ == "__main__":
    main()
