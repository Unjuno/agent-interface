"""Independent preregistration/raw and end-to-end R09 audit."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run"


def verify(path, base):
    rows = path.read_text(encoding="utf-8").splitlines()
    errors = []
    for row in rows:
        expected, relative = row.split("  ", 1)
        target = base / relative
        actual = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
        if actual != expected:
            errors.append({"path": relative, "expected": expected, "actual": actual})
    return {"entries": len(rows), "errors": errors}


pretrial = verify(PACKET / "PRETRIAL_SHA256SUMS", ROOT)
raw = verify(RUN / "SHA256SUMS", RUN)
d = json.loads((RUN / "result.json").read_text(encoding="utf-8"))
oracle = d["task_oracle"]
oracle_receipt = oracle["task_effect"]["receipt"]
action = d["task_retained_result"]["action"]
timing = json.loads((RUN / "effect-verification-audit.json").read_text(encoding="utf-8"))
expected_effect = {"saved": True, "text": "office", "clicked": True}
events = d["task_fixture_events"]
checks = {
    "attempt_and_final_classification": d["attempt_id"] == "win32-native-sendinput-r09-20261026" and d["classification"] == "PASS_RECOVERY_FRESH_GENERATION_TASK",
    "bounded_phase1_recovery": d["recovery_phase"]["classification"] == "PASS_SCOPED_BOUNDED_RECOVERY" and d["recovery_phase"]["release_confirmed"] is True and 0 <= d["recovery_phase"]["cleanup_latency_ns"] < 3_000_000_000,
    "phase1_same_generation_readback": d["recovery_phase"]["same_generation_readback_up"] is True,
    "old_fixture_retired_before_fresh": d["recovery_fixture_exit_code"] == 0 and d["fresh_task_preflight"]["fixture_pid"] != d["fresh_task_preflight"]["previous_fixture_pid"],
    "fresh_generation_differs": d["fresh_task_preflight"]["native_identity"]["target_generation"] != d["recovery_phase"]["old_target_generation"],
    "old_generation_refusal_before_input": d["stale_generation_probe"]["refusal_reason"] == "TARGET_GENERATION_CHANGED" and d["stale_generation_probe"]["input_dispatched"] is False and d["stale_generation_probe"]["effect_file_present"] is False,
    "one_compiled_standard_action": d["compiled_task_receipt"]["outcome"] == "TASK_SUCCEEDED" and len(d["compiled_task_receipt"]["standard_action_call_ids"]) == 1 and d["compiled_task_receipt"]["standard_action_call_ids"][0] == d["task_action_call_id"],
    "action_release_confirmed": d["task_action_release_confirmed"] is True and action["release_confirmed"] is True,
    "native_fresh_generation_neutral_readback": d["task_neutral_readback"]["target_generation"] == d["fresh_task_preflight"]["native_identity"]["target_generation"] and all(d["task_neutral_readback"][key] is False for key in ("SHIFT", "CTRL", "S", "left_button")),
    "exact_fixture_effect_and_event_order": d["independent_effect"] == expected_effect and sum(e.get("kind") == "click" for e in events) == 1 and [e.get("code") for e in events if e.get("kind") == "char"] == list(map(ord, "office")) and sum(e.get("kind") == "save" for e in events) == 1,
    "post_observation_after_action_response": timing["status"] == "succeeded" and timing["post_observation_fresh_after_dispatch_return"] is True and timing["post_observation_capture_started_ns"] > timing["dispatch_response_returned_ns"],
    "independent_oracle_exact_binding": oracle["status"] == "verified" and oracle["task_success"] is True and oracle_receipt["outcome"] == "success" and oracle_receipt["oracle_id"] == "9cf3b010d1aa4c4cb19188c6c6040008" and oracle_receipt["call_id"] == d["task_retained_result"]["call_id"] == d["task_action_call_id"] and oracle_receipt["operation_id"] == action["operation_id"] and oracle_receipt["target_generation"] == d["fresh_task_preflight"]["native_identity"]["target_generation"],
    "cleanup_and_foreground_restoration": d["cleanup"]["fixture_exit_code"] == 0 and d["cleanup"]["foreground_before"] == d["cleanup"]["foreground_after_restore"],
    "no_wslc_or_docker": d["wslc_used"] is False and d["docker_used"] is False,
}
audit = {"attempt_id": d["attempt_id"], "classification": d["classification"],
    "pretrial_hash_audit": pretrial, "raw_hash_audit": raw,
    "checks": checks, "audit_pass": all(checks.values()) and
        not pretrial["errors"] and not raw["errors"]}
(PACKET / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n",
    encoding="utf-8", newline="\n")
print(json.dumps(audit, indent=2, sort_keys=True))
if not audit["audit_pass"]:
    raise SystemExit(1)
