"""Fail-closed validation for the Docker-to-host schema preflight boundary."""
from __future__ import annotations
from typing import Any, Mapping


class BridgeRefused(ValueError):
    pass


def validate(request: Mapping[str, Any], events: list[Mapping[str, Any]], broker: Mapping[str, Any], process: Mapping[str, Any]) -> dict[str, Any]:
    request_id = request.get("request_id")
    if not request_id: raise BridgeRefused("missing_request_id")
    if broker.get("request_id") != request_id: raise BridgeRefused("request_id_mismatch")
    if broker.get("authority_granted") is not False or process.get("authority_granted") is not False:
        raise BridgeRefused("authority_not_false")
    if broker.get("returncode") != 0: raise BridgeRefused("broker_nonzero_or_missing_returncode")
    turns = [row for row in events if row.get("type") == "turn.completed"]
    messages = [row for row in events if row.get("type") == "item.completed"]
    failures = [row for row in events if row.get("type") in {"error", "turn.failed"}]
    if failures: raise BridgeRefused("response_contains_failure")
    if len(turns) != 1 or len(messages) != 1: raise BridgeRefused("not_one_completed_turn_and_message")
    usage = turns[0].get("usage")
    if not isinstance(usage, Mapping): raise BridgeRefused("missing_usage")
    if process.get("request_id") != request_id or process.get("exit_code") != 0:
        raise BridgeRefused("process_receipt_mismatch")
    return {"status": "PASS_DOCKER_IPC_SCHEMA_BRIDGE", "request_id": request_id,
            "authority_granted": False, "turns": 1, "messages": 1,
            "usage": dict(usage), "scope": "schema preflight only; no GUI/input authority"}
