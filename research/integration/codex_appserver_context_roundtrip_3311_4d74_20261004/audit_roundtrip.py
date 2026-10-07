"""Read-only audit for the local app-server context round trip."""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
RAW_PATH = ROOT / "RAW.json"
AUDIT_PATH = ROOT / "AUDIT.json"
EXPECTED_IMAGE = "6331fd4bb0f62dbb6d8492e0c71a4ad6bf1b98091f39b452e2279e7cfd3e6bcf"
MARKER = (
    "PARTIAL_STATE=SAFE_YIELD; reason=effect_unavailable; "
    "completed_transitions=1; second_requested_input=NOT_RUN; "
    "saved_cells=13,41,533; next_row=BLANK"
)


def main() -> int:
    if AUDIT_PATH.exists():
        raise SystemExit("refusing to overwrite existing AUDIT.json")
    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    errors = []
    requests = raw.get("mock_responses_requests")
    if raw.get("disposition") != "OBSERVED_LOCAL_APP_SERVER_CONTEXT_ROUNDTRIP":
        errors.append("runner disposition")
    if type(requests) is not list or len(requests) != 2:
        errors.append("expected exactly two mock Responses requests")
        requests = requests if type(requests) is list else []
    second = requests[1] if len(requests) > 1 else {}
    if not any(MARKER in text for text in second.get("text_fragments", [])):
        errors.append("partial-state marker missing from second request")
    if EXPECTED_IMAGE not in second.get("data_image_sha256s", []):
        errors.append("source PNG bytes missing from second request")
    if raw.get("dynamic_tool_calls") != 1 or raw.get("tool_result_success") is not True:
        errors.append("dynamic-tool result count/status")
    if raw.get("turn_status") != "completed":
        errors.append("app-server turn completion")
    if raw.get("rpc_errors"):
        errors.append("JSON-RPC stdout errors")
    if raw.get("source_image_sha256") != EXPECTED_IMAGE:
        errors.append("frozen source image identity")
    expected_version = "codex-cli 0.159.0-alpha.12.1"
    if raw.get("app_server_version") != expected_version:
        errors.append("app-server version identity")
    result = {
        "disposition": "PASS_LOCAL_SERIALIZATION_SCOPED" if not errors else "FAIL_LOCAL_SERIALIZATION_SCOPED",
        "errors": errors,
        "app_server_version": raw.get("app_server_version"),
        "app_server_binary_sha256": raw.get("app_server_binary_sha256"),
        "mock_request_count": len(requests),
        "dynamic_tool_calls": raw.get("dynamic_tool_calls"),
        "second_request_marker_present": any(MARKER in text for text in second.get("text_fragments", [])),
        "second_request_image_sha256s": second.get("data_image_sha256s", []),
        "scope": "local app-server outbound request serialization only; not provider ingestion, comprehension, GUI, native effect, or task completion",
    }
    AUDIT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
