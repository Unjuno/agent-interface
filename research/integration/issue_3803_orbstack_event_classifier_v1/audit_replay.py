"""Independent read-only audit of replay output and retained inputs."""
import hashlib
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

events, schema, receipt_path = map(Path, sys.argv[1:4])
raw = events.read_bytes()
rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
completed_items = [row.get("item", {}) for row in rows if row.get("type") == "item.completed"]
assistant_items = [item for item in completed_items if item.get("type") == "agent_message"]
error_items = [item for item in completed_items if item.get("type") == "error"]
turns = [row for row in rows if row.get("type") == "turn.completed"]
schema_value = json.loads(schema.read_text(encoding="utf-8"))
message = json.loads(assistant_items[0]["text"]) if len(assistant_items) == 1 else None
checks = {
    "raw_stream_identity": receipt.get("event_sha256") == hashlib.sha256(raw).hexdigest(),
    "one_turn_with_usage": len(turns) == 1 and isinstance(turns[0].get("usage"), dict),
    "one_assistant_only": len(assistant_items) == 1 and receipt.get("completed_assistant_message_count") == 1,
    "auxiliary_error_retained": len(error_items) == 1 and receipt.get("completed_auxiliary_error_count") == 1,
    "json_schema_valid": isinstance(message, dict) and not list(Draft202012Validator(schema_value).iter_errors(message)),
    "no_external_authority_or_side_effect": all(receipt.get(key) == 0 for key in (
        "external_invocations", "model_invocations", "task_submissions", "gui_actions", "ipc_requests"))
        and receipt.get("authority_granted") is False,
    "classifier_disposition": receipt.get("status") == "PASS_SAVED_STREAM_CLASSIFIED" and receipt.get("schema_valid") is True,
}
print(json.dumps({"audit_status": "PASS" if all(checks.values()) else "FAIL",
                  "checks": checks, "completed_item_types": [item.get("type") for item in completed_items]},
                 sort_keys=True))
raise SystemExit(0 if all(checks.values()) else 1)
