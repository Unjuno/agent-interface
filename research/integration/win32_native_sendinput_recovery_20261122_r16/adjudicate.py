"""Independent post-run adjudication preserving the frozen runner's raw verdict."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PACKET = Path(__file__).resolve().parent
ROOT = PACKET.parents[2]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_ok(root: Path, manifest: Path) -> bool:
    if not manifest.is_file():
        return False
    for line in manifest.read_text(encoding="ascii").splitlines():
        if not line:
            continue
        expected, rel = line.split("  ", 1)
        path = (root / rel).resolve()
        try:
            path.relative_to(root.resolve())
        except ValueError:
            return False
        if not path.is_file() or digest(path) != expected:
            return False
    return True


def main() -> int:
    conditions = json.loads((PACKET / "conditions.json").read_text(encoding="utf-8"))
    result = json.loads((PACKET / "run" / "result.json").read_text(encoding="utf-8"))
    cleanup = json.loads((PACKET / "POSTRUN_CLEANUP.json").read_text(encoding="utf-8"))
    response = result["recovery_terminal_response"]
    receipt = response["recovery_receipt"]
    readback = receipt["readback"]
    before = result["fence_before"]
    after = result["fence_after"]
    last = after["state"].get("last_resolved")
    required_fenced = {conditions["source_evidence"]["target_generation"],
                       result["recovery_generation"]}
    events_path = PACKET / "run" / "fixture" / "events.jsonl"
    events = ([json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
        if events_path.is_file() else [])
    effect_path = PACKET / "run" / "fixture" / "effect.json"
    checks = {
        "pretrial_inputs_intact": manifest_ok(ROOT, PACKET / "PRETRIAL_SHA256SUMS"),
        "r14_source_bytes_pinned": digest(ROOT / conditions["source_evidence"]["result"])
            == conditions["source_evidence"]["result_sha256"],
        "fence_preimage_exact": before["sha256"]
            == conditions["persistent_fence"]["expected_sha256_before"],
        "producer_exact_identity_absent": result.get("source_process_identity_check", {}).get(
            "identity") == conditions["source_evidence"]["producer_identity"]
            and result["source_process_identity_check"].get("observed_producer_live") is False,
        "fresh_distinct_recovery_generation": result.get("recovery_generation")
            != conditions["source_evidence"]["target_generation"]
            and result.get("recovery_generation") == result.get(
                "native_recovery_target_preflight", {}).get("target_generation"),
        "one_recovery_no_task_dispatch": result.get("public_recovery_attempt_count") == 1
            and result.get("task_dispatch_attempted") is False
            and response.get("call_id") == result.get("recovery_initial_response", {}).get("call_id"),
        "public_recovery_terminal_success": response.get("status") == "recovered"
            and response.get("recovery_status") == "recovered"
            and response.get("release_confirmed") is True,
        "source_unknown_and_not_replayed": response.get("source_action_status") == "unknown"
            and response.get("task_success") is None and response.get("replay_allowed") is False
            and response.get("source_operation_id") == conditions["source_evidence"]["operation_id"]
            and response.get("source_target_generation")
                == conditions["source_evidence"]["target_generation"]
            and response.get("next_action_requires_fresh_generation") is True,
        "neutral_recovery_readback": readback.get("operation_id")
            == conditions["source_evidence"]["operation_id"]
            and readback.get("source_target_generation")
                == conditions["source_evidence"]["target_generation"]
            and readback.get("target_generation") == result.get("recovery_generation")
            and readback.get("recovery_id") == receipt.get("recovery_id")
            and readback.get("neutral") is True
            and readback.get("key_button_states") == [False],
        "bounded_native_late_input_horizon": receipt.get("late_input_horizon_verified") is True
            and receipt.get("late_input_horizon_ns") == 2_000_000_000
            and receipt.get("late_input_observation_count", 0) >= 20
            and receipt.get("late_input_max_observed_gap_ns", 10**18) <= 100_000_000
            and receipt.get("late_input_max_sample_gap_ns", 0) <= 100_000_000
            and receipt.get("late_input_observation_end_monotonic_ns", 0)
                - receipt.get("late_input_release_received_monotonic_ns", 10**18)
                >= 2_000_000_000,
        "public_api_resolved_and_fenced_both_generations": after["state"].get("status") == "clear"
            and after["state"].get("pending") is None
            and isinstance(last, dict)
            and last.get("operation_id") == conditions["source_evidence"]["operation_id"]
            and last.get("target_generation") == conditions["source_evidence"]["target_generation"]
            and required_fenced.issubset(set(after["state"].get("fenced_generations", []))),
        "no_fixture_task_effect": not effect_path.exists()
            and len(events) == 1 and events[0].get("kind") == "ready",
        "postrun_fixture_and_foreground_cleanup": cleanup["postrun_cleanup"].get(
            "fixture_process_exited") is True
            and cleanup["postrun_cleanup"].get("fixture_window_absent_after_close") is True
            and cleanup["postrun_cleanup"].get("original_foreground_activated") is True
            and cleanup["postrun_cleanup"].get("post_cleanup_native_foreground_hwnd")
                == cleanup["postrun_cleanup"].get("original_foreground_hwnd"),
        "raw_runner_mischeck_identified": result.get("classification")
            == "FAIL_OR_UNKNOWN_FENCE_RETAINED"
            and result.get("acceptance_checks", {}).get("no_task_success_or_replay") is False
            and "no_task_success_or_replay" in result.get("error", ""),
        "raw_run_manifest_intact": manifest_ok(PACKET / "run", PACKET / "run" / "SHA256SUMS"),
    }
    report = {"adjudication": "R16_POSTRUN_RECOVERY_GATE",
        "classification": ("PASS_SCOPED_ORPHAN_RECOVERY_WITH_HORIZON"
            if all(checks.values()) else "HOLD_ADJUDICATION_CHECKS_FAILED"),
        "checks": checks,
        "raw_runner_classification_preserved": result.get("classification"),
        "public_operation_invoked_field_present": "operation_invoked" in response,
        "public_task_dispatch_not_attempted": result.get("task_dispatch_attempted") is False,
        "public_task_success": response.get("task_success"),
        "public_replay_allowed": response.get("replay_allowed"),
        "fence_after_sha256": after.get("sha256"),
        "fixture_exit_code_observed_after_cua": cleanup["postrun_cleanup"].get(
            "fixture_process_exited"),
    }
    print(json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
