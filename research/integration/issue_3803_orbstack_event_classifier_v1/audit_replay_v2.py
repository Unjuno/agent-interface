"""Corrected independent audit of immutable replay output and its input inventory."""
import hashlib
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

events_path, schema_path, receipt_path, inventory_path, output_path = map(Path, sys.argv[1:6])
raw = events_path.read_bytes()
rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
schema = json.loads(schema_path.read_text(encoding="utf-8"))
items = [row.get("item", {}) for row in rows if row.get("type") == "item.completed"]
assistants = [item for item in items if item.get("type") == "agent_message"]
auxiliary = [item for item in items if item.get("type") == "error"]
turns = [row for row in rows if row.get("type") == "turn.completed"]
message = json.loads(assistants[0]["text"]) if len(assistants) == 1 else None
raw_sha = hashlib.sha256(raw).hexdigest()
schema_sha = hashlib.sha256(schema_path.read_bytes()).hexdigest()
checks = {
    "raw_stream_matches_inventory": inventory.get("event_sha256") == raw_sha,
    "schema_matches_inventory": inventory.get("schema_sha256") == schema_sha,
    "one_turn_with_usage": len(turns) == 1 and isinstance(turns[0].get("usage"), dict),
    "one_completed_assistant": len(assistants) == 1 and receipt.get("completed_assistant_message_count") == 1,
    "auxiliary_error_preserved": len(auxiliary) == 1 and receipt.get("completed_auxiliary_error_count") == 1,
    "assistant_json_satisfies_schema": isinstance(message, dict) and not list(Draft202012Validator(schema).iter_errors(message)),
    "no_authority_or_external_side_effect": receipt.get("authority_granted") is False and all(
        receipt.get(key) == 0 for key in ("external_invocations", "model_invocations", "task_submissions", "gui_actions", "ipc_requests")),
    "receipt_status": receipt.get("status") == "PASS_SAVED_STREAM_CLASSIFIED" and receipt.get("schema_valid") is True,
}
result = {"audit_status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
          "completed_item_types": [item.get("type") for item in items],
          "raw_stream_sha256": raw_sha, "schema_sha256": schema_sha}
output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if all(checks.values()) else 1)
