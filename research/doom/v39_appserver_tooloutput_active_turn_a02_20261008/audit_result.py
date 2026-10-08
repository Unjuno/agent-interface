import json
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent
result = json.loads((root / "result.json").read_text(encoding="utf-8"))
exit_code = (root / "process_exit.txt").read_text(encoding="ascii").strip()

def accept(row):
    return (
        row.get("app_server_version") == "codex-cli 0.160.0" and
        row.get("requests_to_loopback_mock_only") == 2 and
        row.get("same_turn") is True and
        row.get("tool_output_text_present_in_followup_request") is True and
        row.get("valid_png_b64_present_in_followup_request") is True and
        row.get("followup_request_after_first_response_completed") is True and
        row.get("seconds_from_tool_output_send_to_first_response_completion", 0) >= 1.0 and
        row.get("followup_request_ms_after_first_response_completion", -1) >= 0.0 and
        row.get("terminal_status") == "completed" and
        row.get("mock_transport_errors") == []
    )

checks = {
    "retained_run_exit_zero": exit_code == "0",
    "same_turn_and_two_loopback_requests": result.get("same_turn") is True and result.get("requests_to_loopback_mock_only") == 2,
    "followup_has_text_and_valid_image": result.get("tool_output_text_present_in_followup_request") is True and result.get("valid_png_b64_present_in_followup_request") is True,
    "followup_waits_for_first_response": result.get("followup_request_after_first_response_completed") is True and result.get("followup_request_ms_after_first_response_completion", -1) >= 0.0,
    "control_detects_same_turn_mutation": not accept({**result, "same_turn": False}),
    "control_detects_missing_image_mutation": not accept({**result, "valid_png_b64_present_in_followup_request": False}),
    "control_detects_early_followup_mutation": not accept({**result, "followup_request_after_first_response_completed": False}),
    "control_detects_missing_request_mutation": not accept({**result, "requests_to_loopback_mock_only": 1}),
}
out = {"disposition": "PASS_RETAINED_RESULT_SCOPE_AUDIT" if all(checks.values()) else "FAIL_RETAINED_RESULT_SCOPE_AUDIT", "checks": checks}
(root / "audit.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
print(json.dumps(out, indent=2))
raise SystemExit(0 if all(checks.values()) else 1)

