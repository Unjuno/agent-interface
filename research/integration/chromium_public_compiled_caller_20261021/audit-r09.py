from __future__ import annotations
import hashlib, json, re
from pathlib import Path

PACKET = Path(__file__).resolve().parent
RAW = PACKET / "raw" / "r09"
CONDITIONS = json.loads((PACKET / "CONDITIONS-r09.json").read_text(encoding="utf-8"))
RUN = json.loads((RAW / "run.json").read_text(encoding="utf-8"))
TERMINAL = json.loads((RAW / "public-compiled-terminal.json").read_text(encoding="utf-8"))
INVOKE = json.loads((RAW / "public-compiled-invoke.json").read_text(encoding="utf-8"))
POSTS = json.loads((RAW / "fixture-post.json").read_text(encoding="utf-8"))
SCORE = json.loads((RAW / "independent-score.json").read_text(encoding="utf-8"))
CLOSE = json.loads((RAW / "public-close.json").read_text(encoding="utf-8"))
X_LIFECYCLE = json.loads((RAW.parent / "xvfb-lifecycle-r09.json").read_text(encoding="utf-8"))
METHOD = TERMINAL["method_receipt"]
EVENTS = []
for path in (RAW / "mcp").rglob("*-event.json"):
    try:
        event = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        continue
    event["_path"] = path.relative_to(RAW).as_posix()
    EVENTS.append(event)
OBSERVATIONS = {item["evidence_ref"]: item for item in METHOD.get("observations", [])}
PENDING = [item for item in EVENTS if item.get("event") == "effect_observation_pending" and item.get("action") == "submit_form"]
PENDING_OBSERVATIONS = [OBSERVATIONS[item["evidence_ref"]] for item in PENDING if item.get("evidence_ref") in OBSERVATIONS]
POST = POSTS[0] if len(POSTS) == 1 else {}
SUCCESS_EFFECTS = [item for item in EVENTS if item.get("event") == "effect_checked" and item.get("action") == "submit_form" and item.get("status") == "succeeded"]
TRANSITIONS = METHOD.get("transitions", [])
PROVIDER = RUN.get("provider_attempt", {})
TOKEN = CONDITIONS["task"]["token"]
RESPONSE_READY = POST.get("response_ready_monotonic_ns")
FIRST_PENDING = min((x["captured_ns"] for x in PENDING_OBSERVATIONS), default=None)
EFFECT_CAPTURE = SUCCESS_EFFECTS[0].get("effect_observation_captured_ns") if len(SUCCESS_EFFECTS) == 1 else None

checks = {
    "run_id_matches_frozen_conditions": RUN.get("run_id") == CONDITIONS["run_id"] == "chromium-public-compiled-standard-caller-live-r09-20261021",
    "exactly_one_post_with_frozen_token": len(POSTS) == 1 and POST.get("path") == "/submit" and POST.get("submitted_values") == [TOKEN],
    "controlled_response_delay_at_least_1500ms": POST.get("response_delay_actual_ns", 0) >= 1_500_000_000,
    "pending_effect_event_retained": len(PENDING) >= 1,
    "pending_observation_precedes_response_ready": FIRST_PENDING is not None and RESPONSE_READY is not None and FIRST_PENDING < RESPONSE_READY,
    "later_success_observation_follows_response_ready": EFFECT_CAPTURE is not None and RESPONSE_READY is not None and EFFECT_CAPTURE > RESPONSE_READY,
    "public_compiled_method_succeeded": METHOD.get("outcome") == "TASK_SUCCEEDED" and RUN.get("public_call", {}).get("call_id") == TERMINAL.get("call_id"),
    "two_action_releases_verified": len(TRANSITIONS) == 2 and all(x.get("release_verified") is True for x in TRANSITIONS),
    "no_replay_and_runtime_task_success_unset": TERMINAL.get("replay_allowed") is False and TERMINAL.get("task_success") is None,
    "independent_scorer_passed": SCORE.get("success") is True and SCORE.get("submission_count") == 1 and SCORE.get("runtime_task_success") is None,
    "session_close_release_verified": CLOSE.get("release_confirmed") is True and CLOSE.get("session", {}).get("state") == "closed",
    "owner_process_exited_cleanly": CLOSE.get("session", {}).get("owner_process", {}).get("alive") is False and CLOSE.get("session", {}).get("owner_process", {}).get("exitcode") == 0 and CLOSE.get("session", {}).get("target_queries", {}).get("thread_alive") is False,
    "browser_appserver_fixture_closed": RUN.get("cleanup", {}).get("browser_exitcode") == 0 and RUN.get("cleanup", {}).get("appserver_closed") is True and RUN.get("cleanup", {}).get("fixture_server_closed") is True,
    "xvfb_reaped": X_LIFECYCLE.get("reaped") is True and X_LIFECYCLE.get("exit_status") == 0,
    "provider_usage_retained": bool(PROVIDER.get("turn_id")) and bool(PROVIDER.get("thread_id")) and PROVIDER.get("usage", {}).get("input_tokens", 0) > 0 and PROVIDER.get("turn_id") in (RAW / "provider-protocol.jsonl").read_text(encoding="utf-8"),
    "screenshots_retained": (RAW / "source-observation.png").is_file() and (RAW / "post-model-fresh-observation.png").is_file(),
}
result = {
    "schema": "agent-interface/chromium-public-compiled-caller-audit-v1",
    "run_id": CONDITIONS["run_id"],
    "status": "PASS_POLLING_BRANCH_SCOPED_SINGLE_TRIAL" if all(checks.values()) else "HOLD_AUDIT_CHECK_FAILED",
    "checks": checks,
    "measurements": {
        "controlled_delay_ms": CONDITIONS["task"]["controlled_response_delay_ms"],
        "actual_response_delay_ns": POST.get("response_delay_actual_ns"),
        "post_received_ns": POST.get("received_monotonic_ns"),
        "first_pending_observation_ns": FIRST_PENDING,
        "response_ready_ns": RESPONSE_READY,
        "later_success_observation_ns": EFFECT_CAPTURE,
        "pending_submit_events": len(PENDING),
        "total_critical_events": len(EVENTS),
        "model": RUN.get("model"),
        "provider_attempt": PROVIDER,
        "task_outcome": METHOD.get("outcome"),
        "transition_count": len(TRANSITIONS),
        "independent_score": SCORE,
        "runtime_task_success": TERMINAL.get("task_success"),
        "replay_allowed": TERMINAL.get("replay_allowed"),
        "close_release_confirmed": CLOSE.get("release_confirmed"),
        "xvfb_lifecycle": X_LIFECYCLE,
    },
}
out = PACKET / "audit-r09.json"
out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"status": result["status"], "failed_checks": [k for k, v in checks.items() if not v],
                  "pending_events": len(PENDING), "first_pending_observation_ns": FIRST_PENDING,
                  "response_ready_ns": RESPONSE_READY, "later_success_observation_ns": EFFECT_CAPTURE,
                  "audit": out.name}, indent=2))
