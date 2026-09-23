"""Contract-only Docker IPC schema bridge; no authority or GUI operations."""
from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class BridgeResult:
    status: str
    request_id: str
    authority_granted: bool
    usage: dict[str, Any] | None
    reason: str | None = None

def extract_schema_payload(jsonl: str) -> dict[str, Any]:
    """Extract exactly one JSON agent message from Codex JSONL output.

    Lifecycle events such as ``turn.completed`` are not schema payloads.
    """
    messages = []
    for line in jsonl.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError("invalid_jsonl_event") from exc
        item = event.get("item") if isinstance(event, dict) else None
        if (event.get("type") == "item.completed" and isinstance(item, dict)
                and item.get("type") == "agent_message"):
            text = item.get("text")
            if not isinstance(text, str):
                raise ValueError("agent_message_text_required")
            try:
                payload = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError("agent_message_not_json") from exc
            if not isinstance(payload, dict):
                raise ValueError("schema_payload_object_required")
            messages.append(payload)
    if len(messages) != 1:
        raise ValueError("exactly_one_schema_agent_message_required")
    return messages[0]

def validate_response(request: dict[str, Any], response: dict[str, Any]) -> BridgeResult:
    rid = request.get("request_id")
    if type(rid) is not str or not rid:
        return BridgeResult("REFUSED", "", False, None, "request_id_required")
    if type(response) is not dict or response.get("request_id") != rid:
        return BridgeResult("REFUSED", rid, False, None, "request_id_mismatch")
    if response.get("authority_granted") is not False:
        return BridgeResult("REFUSED", rid, False, None, "authority_must_remain_false")
    if response.get("status") not in {"ok", "error"}:
        return BridgeResult("REFUSED", rid, False, None, "status_required")
    usage = response.get("usage")
    if usage is not None and type(usage) is not dict:
        return BridgeResult("REFUSED", rid, False, None, "usage_must_be_object")
    if response["status"] == "error":
        return BridgeResult("YIELD", rid, False, usage, response.get("error", "broker_error"))
    payload = response.get("payload")
    if type(payload) is not dict:
        return BridgeResult("REFUSED", rid, False, usage, "schema_payload_required")
    return BridgeResult("COMPATIBLE", rid, False, usage)

def encode_request(request_id: str, schema_sha256: str, prompt: str) -> str:
    if not request_id or len(schema_sha256) != 64 or not isinstance(prompt, str):
        raise ValueError("request identity/schema/prompt required")
    return json.dumps({"request_id": request_id, "schema_sha256": schema_sha256,
                       "prompt": prompt, "authority_granted": False}, sort_keys=True)
