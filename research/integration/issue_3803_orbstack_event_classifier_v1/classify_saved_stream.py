"""Classify a frozen Codex JSONL stream without invoking any external service."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

EXPECTED_EVENT_SHA256 = "b6db1cc383a4491ca58b54dd1b81acc090588ac518e5f2d09ea98a63aed247a1"
EXPECTED_SCHEMA_SHA256 = "0631ab7b7ba0aaf77a4cbdf758a8dbfba557dfb5120a9d5aa789223c97944291"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify(raw: bytes, schema_bytes: bytes, require_frozen: bool = False) -> tuple[dict, dict]:
    event_sha = hashlib.sha256(raw).hexdigest()
    schema_sha = hashlib.sha256(schema_bytes).hexdigest()
    if require_frozen and (event_sha != EXPECTED_EVENT_SHA256 or schema_sha != EXPECTED_SCHEMA_SHA256):
        raise ValueError("frozen replay input hash mismatch")
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    schema = json.loads(schema_bytes)
    completed = [row["item"] for row in rows
                 if row.get("type") == "item.completed" and isinstance(row.get("item"), dict)]
    assistants = [item for item in completed if item.get("type") == "agent_message"]
    auxiliary_errors = [item for item in completed if item.get("type") == "error"]
    turns = [row for row in rows if row.get("type") == "turn.completed"]
    if len(turns) != 1 or not isinstance(turns[0].get("usage"), dict):
        raise ValueError("expected exactly one completed turn with usage")
    if len(assistants) != 1:
        raise ValueError("expected exactly one completed assistant message")
    text = assistants[0].get("text")
    if not isinstance(text, str):
        raise ValueError("assistant message text is missing")
    output = json.loads(text)
    if not isinstance(output, dict):
        raise ValueError("assistant JSON must be an object")
    from jsonschema import Draft202012Validator
    Draft202012Validator(schema).validate(output)
    receipt = {
        "status": "PASS_SAVED_STREAM_CLASSIFIED",
        "authority_granted": False,
        "external_invocations": 0,
        "model_invocations": 0,
        "task_submissions": 0,
        "gui_actions": 0,
        "ipc_requests": 0,
        "event_count": len(rows),
        "completed_assistant_message_count": len(assistants),
        "completed_auxiliary_error_count": len(auxiliary_errors),
        "auxiliary_error_types": [item.get("type") for item in auxiliary_errors],
        "usage": turns[0]["usage"],
        "assistant_json_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "schema_valid": True,
    }
    inventory = {
        "event_sha256": event_sha,
        "schema_sha256": schema_sha,
        "receipt_sha256": hashlib.sha256((json.dumps(receipt, sort_keys=True) + "\n").encode()).hexdigest(),
    }
    return receipt, inventory


def main() -> int:
    events, schema, output = map(Path, sys.argv[1:4])
    receipt, inventory = classify(events.read_bytes(), schema.read_bytes(), require_frozen=True)
    output.mkdir(parents=True, exist_ok=False)
    (output / "process.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    (output / "input-inventory.json").write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "event_sha256": inventory["event_sha256"],
                      "assistant_messages": receipt["completed_assistant_message_count"],
                      "auxiliary_errors": receipt["completed_auxiliary_error_count"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
