import json
import sys
from pathlib import Path


root = Path(sys.argv[1]).resolve()
result = json.loads((root / "result.json").read_text(encoding="utf-8"))
app_server_exit = (root / "process_exit.txt").read_text(encoding="ascii").strip()
runner_exit = (root / "runner_exit.txt").read_text(encoding="ascii").strip()


def passes(row):
    released = row.get("first_response_released_at")
    second = row.get("second_request_at")
    return (
        row.get("disposition") ==
            "PASS_INTERRUPT_ADMITS_FRESH_OBSERVATION_BEFORE_HELD_RESPONSE_RELEASE" and
        row.get("app_server_version") == "codex-cli 0.160.0" and
        row.get("requests_to_loopback_mock_only") == 2 and
        bool(row.get("thread_id")) and
        row.get("same_thread") is True and
        bool(row.get("first_turn_id")) and
        row.get("first_turn_status") == "interrupted" and
        bool(row.get("second_turn_id")) and
        row.get("second_turn_status") == "completed" and
        row.get("second_request_before_first_response_release") is True and
        isinstance(second, (int, float)) and isinstance(released, (int, float)) and
        second < released and
        row.get("second_request_contains_observation_text") is True and
        row.get("second_request_contains_valid_png") is True and
        row.get("app_server_exit_code") == 0 and
        app_server_exit == "0" and runner_exit == "0"
    )


checks = {
    "first_turn_interrupted_and_fresh_turn_completed":
        result.get("first_turn_status") == "interrupted" and
        result.get("second_turn_status") == "completed",
    "fresh_request_precedes_first_response_release":
        result.get("second_request_before_first_response_release") is True and
        isinstance(result.get("second_request_at"), (int, float)) and
        isinstance(result.get("first_response_released_at"), (int, float)) and
        result["second_request_at"] < result["first_response_released_at"],
    "fresh_request_contains_text_and_png":
        result.get("second_request_contains_observation_text") is True and
        result.get("second_request_contains_valid_png") is True,
    "both_processes_exit_zero":
        result.get("app_server_exit_code") == 0 and
        app_server_exit == "0" and runner_exit == "0",
    "control_detects_non_interrupted_first_turn":
        not passes({**result, "first_turn_status": "completed"}),
    "control_detects_late_fresh_request":
        not passes({**result, "second_request_before_first_response_release": False}),
    "control_detects_missing_image":
        not passes({**result, "second_request_contains_valid_png": False}),
    "control_detects_abnormal_app_server_exit":
        not passes({**result, "app_server_exit_code": 1}),
}
audit = {"disposition": "PASS_A05_RESULT_AUDIT" if all(checks.values())
         else "FAIL_A05_RESULT_AUDIT", "checks": checks}
(root / "audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
print(json.dumps(audit, indent=2))
raise SystemExit(0 if all(checks.values()) else 1)

