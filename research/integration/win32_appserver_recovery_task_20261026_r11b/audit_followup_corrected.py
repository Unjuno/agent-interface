"""Additive R11 audit correcting wrapper-status-only usage comparison."""
import hashlib
import json
from pathlib import Path

PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run"


def verify(path, base):
    failures = []
    rows = path.read_text(encoding="utf-8").splitlines()
    for row in rows:
        expected, relative = row.split("  ", 1)
        target = base / relative
        actual = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
        if actual != expected:
            failures.append({"path": relative, "expected": expected, "actual": actual})
    return {"entries": len(rows), "failures": failures}


pretrial = verify(PACKET / "PRETRIAL_SHA256SUMS", PACKET)
raw = verify(RUN / "SHA256SUMS", RUN)
d = json.loads((RUN / "result.json").read_text(encoding="utf-8"))
model = d["model_decision"]
usage = model["usage"]
backend_usage = model["backend_usage"]
usage_fields_match = (usage.get("status") == "reported" and
    all(usage.get(key) == value for key, value in backend_usage.items()))
recovery = d["recovery_phase"]
fresh = d["fresh_task_preflight"]
oracle = d["task_oracle"]
receipt = oracle["task_effect"]["receipt"]
retained = d["task_retained_result"]
action = retained["action"]
program = d["submitted_task_program"]
pointer = next(op for op in program["ops"] if op.get("op") == "pointer_move")
timing = json.loads((RUN / "effect-verification-audit.json").read_text(encoding="utf-8"))
events = d["task_fixture_events"]
expected = {"saved": True, "text": "office", "clicked": True}
observations = d["compiled_observations"]
first_observation = observations[0]

checks = {
    "phase1_recovery_and_same_generation_readback": recovery["classification"] == "PASS_SCOPED_BOUNDED_RECOVERY" and recovery["release_confirmed"] is True and 0 <= recovery["cleanup_latency_ns"] < 3_000_000_000 and recovery["same_generation_readback_up"] is True,
    "stale_generation_refused_before_input": d["stale_generation_probe"]["refusal_reason"] == "TARGET_GENERATION_CHANGED" and d["stale_generation_probe"]["input_dispatched"] is False,
    "new_pid_and_target_generation": fresh["fixture_pid"] != fresh["previous_fixture_pid"] and fresh["native_identity"]["target_generation"] != recovery["old_target_generation"],
    "one_real_appserver_turn_and_bounded_model_coordinate": model["status"] == "completed" and model["model"] == "gpt-6.1-sol" and model["effort"] == "low" and type(model["answer"]["x"]) is int and type(model["answer"]["y"]) is int and 24 <= model["answer"]["x"] <= 300 and 24 <= model["answer"]["y"] <= 150,
    "provider_usage_fields_match_retained_appserver_journal": usage_fields_match,
    "same_grounded_generation_after_model_wait": model["grounding_generation"] == fresh["native_identity"]["target_generation"] == first_observation["target_generation"] and first_observation["capture_started_ns"] >= model["model_returned_monotonic_ns"],
    "compiled_action_uses_model_coordinate_once": (pointer["x"], pointer["y"]) == (model["answer"]["x"], model["answer"]["y"]) and d["compiled_task_receipt"]["outcome"] == "TASK_SUCCEEDED" and d["compiled_task_receipt"]["standard_action_call_ids"] == [d["task_action_call_id"]],
    "action_release_and_independent_native_neutral_readback": d["task_action_release_confirmed"] is True and action["release_confirmed"] is True and all(d["task_neutral_readback"][key] is False for key in ("SHIFT", "CTRL", "S", "left_button")),
    "fresh_post_action_observation_and_exact_fixture_effect": timing["status"] == "succeeded" and timing["post_observation_fresh_after_dispatch_return"] is True and timing["post_observation_capture_started_ns"] > timing["dispatch_response_returned_ns"] and d["independent_effect"] == expected and sum(e.get("kind") == "click" for e in events) == 1 and [e.get("code") for e in events if e.get("kind") == "char"] == list(map(ord, "office")) and sum(e.get("kind") == "save" for e in events) == 1,
    "independent_task_oracle_exactly_bound": oracle["status"] == "verified" and oracle["task_success"] is True and receipt["outcome"] == "success" and receipt["oracle_id"] == json.loads((PACKET / "conditions.json").read_text(encoding="utf-8"))["task"]["oracle_id"] and receipt["call_id"] == retained["call_id"] == d["task_action_call_id"] and receipt["operation_id"] == action["operation_id"] and receipt["target_generation"] == fresh["native_identity"]["target_generation"],
    "cleanup_and_no_unapproved_runtime": d["cleanup"]["fixture_exit_code"] == 0 and d["cleanup"]["foreground_before"] == d["cleanup"]["foreground_after_restore"] and d["appserver_closed"] is True and d["wslc_used"] is False and d["docker_used"] is False,
}
result = {"attempt_id": d["attempt_id"],
    "original_runner_classification_preserved": d["classification"],
    "classification": "PASS_SCOPED_APP_SERVER_RECOVERY_FRESH_GENERATION_TASK" if all(checks.values()) and not pretrial["failures"] and not raw["failures"] else "FAIL_OR_UNKNOWN",
    "interpretation": "R11b primary audit already passes. This additive pass independently recomputes task gates using the preregistered oracle ID and validates unchanged pretrial/raw hashes.",
    "model_latency_ns": model["model_latency_ns"],
    "appserver_reported_usage": usage,
    "appserver_journal_usage": backend_usage,
    "pretrial_hash_audit": pretrial, "raw_hash_audit": raw,
    "checks": checks, "audit_pass": all(checks.values()) and
        not pretrial["failures"] and not raw["failures"]}
(PACKET / "audit_followup_corrected.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
    encoding="utf-8", newline="\n")
print(json.dumps(result, indent=2, sort_keys=True))
if not result["audit_pass"]:
    raise SystemExit(1)

