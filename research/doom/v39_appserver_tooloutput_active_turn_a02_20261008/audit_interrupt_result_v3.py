import json
import sys
from pathlib import Path


root = Path(sys.argv[1]).resolve()
result = json.loads((root / "result.json").read_text(encoding="utf-8"))
app_server_exit = (root / "process_exit.txt").read_text(encoding="ascii").strip()
runner_exit = (root / "runner_exit.txt").read_text(encoding="ascii").strip()


def passes(row, server_exit=app_server_exit, runner_status=runner_exit):
    return (
        row.get("disposition") ==
            "PASS_INTERRUPT_ADMITS_FRESH_OBSERVATION_BEFORE_HELD_RESPONSE_RELEASE" and
        row.get("app_server_version") == "codex-cli 0.160.0" and
        row.get("requests_to_loopback_mock_only") == 2 and
        bool(row.get("thread_id")) and row.get("same_thread") is True and
        row.get("first_turn_status") == "interrupted" and
        row.get("second_turn_status") == "completed" and
        row.get("second_request_before_first_response_release") is True and
        row.get("second_request_contains_observation_text") is True and
        row.get("second_request_contains_valid_png") is True and
        row.get("late_first_response_write_finished") is True and
        row.get("late_response_transport_outcome") in ("sent", "peer_closed") and
        row.get("first_turn_completion_notification_count") == 1 and
        row.get("second_turn_completion_notification_count") == 1 and
        row.get("stale_sentinel_observed_in_app_server_output") is False and
        row.get("app_server_exit_code") == 0 and server_exit == "0" and
        runner_status == "0"
    )


checks = {
    "one_interrupted_and_one_completed_turn":
        result.get("first_turn_status") == "interrupted" and
        result.get("second_turn_status") == "completed" and
        result.get("first_turn_completion_notification_count") == 1 and
        result.get("second_turn_completion_notification_count") == 1,
    "fresh_request_precedes_release_and_contains_observation":
        result.get("second_request_before_first_response_release") is True and
        result.get("second_request_contains_observation_text") is True and
        result.get("second_request_contains_valid_png") is True,
    "late_stale_response_has_terminal_transport_outcome":
        result.get("late_first_response_write_finished") is True and
        result.get("late_response_transport_outcome") in ("sent", "peer_closed"),
    "stale_output_not_emitted":
        result.get("stale_sentinel_observed_in_app_server_output") is False,
    "both_processes_exit_zero":
        result.get("app_server_exit_code") == 0 and
        app_server_exit == "0" and runner_exit == "0",
    "control_detects_stale_output":
        not passes({**result, "stale_sentinel_observed_in_app_server_output": True}),
    "control_detects_duplicate_old_turn_completion":
        not passes({**result, "first_turn_completion_notification_count": 2}),
    "control_detects_missing_fresh_image":
        not passes({**result, "second_request_contains_valid_png": False}),
    "control_detects_late_fresh_request":
        not passes({**result, "second_request_before_first_response_release": False}),
    "control_detects_abnormal_app_server_exit":
        not passes(result, server_exit="1"),
}
audit = {"disposition": "PASS_A07_STALE_RESPONSE_AUDIT_V3" if all(checks.values())
         else "FAIL_A07_STALE_RESPONSE_AUDIT_V3", "checks": checks}
(root / "audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
print(json.dumps(audit, indent=2))
raise SystemExit(0 if all(checks.values()) else 1)

