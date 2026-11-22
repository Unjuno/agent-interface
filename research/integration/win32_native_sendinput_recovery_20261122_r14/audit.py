"""Independent raw and result audit for current-main Win32 R10."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run"


def verify_manifest(path, base):
    errors = []
    rows = path.read_text(encoding="ascii").splitlines()
    seen = set()
    for row in rows:
        expected, relative = row.split("  ", 1)
        if relative in seen or Path(relative).is_absolute() or ".." in Path(relative).parts:
            errors.append({"path": relative, "error": "invalid_or_duplicate_path"})
            continue
        seen.add(relative)
        target = base / relative
        actual = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
        if actual != expected:
            errors.append({"path": relative, "expected": expected, "actual": actual})
    return {"entries": len(rows), "errors": errors}


pretrial = verify_manifest(PACKET / "PRETRIAL_SHA256SUMS", ROOT)
raw = verify_manifest(RUN / "SHA256SUMS", RUN)
d = json.loads((RUN / "result.json").read_text(encoding="utf-8"))
expiry = d["pre_expiry_cancel"]["deadline_monotonic_ns"]
pre_cancel = d["pre_expiry_cancel"]
post_cancel = d["cancel"]
retained = d["retained_result"]
cancellation = retained.get("cancellation") or {}
custody = cancellation.get("result") or {}
horizon = d["post_recovery_late_input_horizon"]
events = d["fixture_events"]
timing = json.loads((RUN / "effect-verification-audit.json").read_text(encoding="utf-8"))
oracle = d["task_oracle"]
receipt = (oracle.get("task_effect") or {}).get("receipt") or {}
action = (d["task_retained_result"].get("action") or {})
task_events = d["task_fixture_events"]
expected_effect = {"saved": True, "text": "office", "clicked": True}
checks = {
    "attempt_and_final_classification": d["attempt_id"] == "win32-native-sendinput-r14-20261122"
        and d["classification"] == "PASS_RECOVERY_FRESH_GENERATION_TASK",
    "frozen_source_matches": d.get("source_commit") == "1839894946aac582ccc49b84bdebab68a3282807",
    "phase1_neutral_state_witnessed": d["preflight"].get("shift_down") is False
        and d["preflight"].get("target_generation") is not None
        and bool(d["preflight"].get("state_query_witness")),
    "phase1_computer_use_exact_activation": d["phase1_computer_use_activation"].get("stage") == "recovery"
        and d["phase1_computer_use_activation"].get("fixture_window_id") == d["target_hwnd"]
        and d["phase1_computer_use_activation"].get("activate_call_returned") is True
        and d["window_preflight"].get("foreground_hwnd") == d["target_hwnd"],
    "phase2_computer_use_exact_activation": d["fresh_task_preflight"]["computer_use_activation"].get("stage") == "fresh-task"
        and d["fresh_task_preflight"]["computer_use_activation"].get("fixture_window_id") == d["fresh_task_preflight"]["window"].get("hwnd")
        and d["fresh_task_preflight"]["computer_use_activation"].get("activate_call_returned") is True
        and d["fresh_task_preflight"]["window"].get("foreground_hwnd") == d["fresh_task_preflight"]["window"].get("hwnd"),
    "pre_expiry_cancel_refused": pre_cancel["body"].get("status") == "cancel_not_due"
        and pre_cancel["started_monotonic_ns"] < expiry,
    "post_expiry_public_cancel": d["cancel_started_monotonic_ns"] >= expiry
        and post_cancel.get("status") == "recovered"
        and retained.get("deadline_cancel_policy") == "public_caller"
        and retained.get("deadline_cancel_route") == "public_interface_cancel",
    "bounded_verified_release": cancellation.get("status") == "recovered"
        and cancellation.get("release_confirmed") is True
        and custody.get("release_confirmed") is True
        and custody.get("cleanup_requested_monotonic_ns", 0) >= expiry
        and type(custody.get("cleanup_latency_ns")) is int
        and 0 <= custody["cleanup_latency_ns"] < 3_000_000_000
        and d["state_after_recovery"]["shift_down"] is False
        and d["state_after_recovery"]["target_generation"] == d["recovery_phase"]["old_target_generation"],
    "blocked_producer_stopped": d["blocked_producer_after_recovery"]["alive"] is False
        and d["blocked_producer_after_recovery"]["exit_code"] is not None,
    "post_recovery_delayed_input_horizon": horizon["duration_ns"] >= 1_900_000_000
        and horizon["sample_count"] >= 20
        and type(horizon["max_sample_gap_ns"]) is int
        and horizon["max_sample_gap_ns"] <= 100_000_000
        and horizon["all_shift_up"] is True and horizon["one_generation"] is True
        and horizon["target_generation"] == d["recovery_phase"]["old_target_generation"],
    "no_phase1_fixture_effect": d["effect_file_present"] is False
        and all(e.get("kind") == "ready" for e in events),
    "old_fixture_retired_before_fresh": d["recovery_fixture_exit_code"] == 0
        and d["fresh_task_preflight"]["fixture_pid"] != d["fresh_task_preflight"]["previous_fixture_pid"],
    "fresh_generation_differs": d["fresh_task_preflight"]["native_identity"]["target_generation"]
        != d["recovery_phase"]["old_target_generation"],
    "old_generation_refusal_before_input": d["stale_generation_probe"]["refusal_reason"] == "TARGET_GENERATION_CHANGED"
        and d["stale_generation_probe"]["input_dispatched"] is False
        and d["stale_generation_probe"]["effect_file_present"] is False,
    "one_compiled_standard_action": d["compiled_task_receipt"]["outcome"] == "TASK_SUCCEEDED"
        and len(d["compiled_task_receipt"]["standard_action_call_ids"]) == 1
        and d["compiled_task_receipt"]["standard_action_call_ids"][0] == d["task_action_call_id"],
    "exact_independent_task_effect": d["independent_effect"] == expected_effect
        and oracle.get("status") == "verified" and oracle.get("task_success") is True
        and receipt.get("outcome") == "success" and receipt.get("oracle_id") == "9cf3b010d1aa4c4cb19188c6c6040008"
        and receipt.get("call_id") == d["task_action_call_id"]
        and receipt.get("operation_id") == action.get("operation_id")
        and receipt.get("target_generation") == d["fresh_task_preflight"]["native_identity"]["target_generation"],
    "fresh_action_release_and_neutral_readback": d["task_action_release_confirmed"] is True
        and all(d["task_neutral_readback"][k] is False for k in ("SHIFT", "CTRL", "S", "left_button"))
        and all(bool(d["task_neutral_readback"]["state_query_witnesses"][k]) for k in ("SHIFT", "CTRL", "S", "left_button"))
        and d["task_neutral_readback"]["target_generation"]
            == d["fresh_task_preflight"]["native_identity"]["target_generation"],
    "exact_fixture_event_sequence_and_observation_order": sum(e.get("kind") == "click" for e in task_events) == 1
        and [e.get("code") for e in task_events if e.get("kind") == "char"] == list(map(ord, "office"))
        and sum(e.get("kind") == "save" for e in task_events) == 1
        and timing["status"] == "succeeded"
        and timing["post_observation_fresh_after_dispatch_return"] is True
        and timing["post_observation_capture_started_ns"] > timing["dispatch_response_returned_ns"],
    "cleanup_and_foreground_restoration": d["cleanup"]["fixture_exit_code"] == 0
        and d["cleanup"]["foreground_before"] == d["cleanup"]["foreground_after_restore"],
    "no_wslc_or_docker": d["wslc_used"] is False and d["docker_used"] is False,
}
audit = {"attempt_id": d["attempt_id"], "classification": d["classification"],
    "pretrial_hash_audit": pretrial, "raw_hash_audit": raw, "checks": checks,
    "audit_pass": all(checks.values()) and not pretrial["errors"] and not raw["errors"]}
(PACKET / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n",
    encoding="utf-8", newline="\n")
print(json.dumps(audit, indent=2, sort_keys=True))
if not audit["audit_pass"]:
    raise SystemExit(1)

