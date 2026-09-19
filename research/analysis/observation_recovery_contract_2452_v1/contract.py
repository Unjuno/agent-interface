"""Finite fail-closed model for observation-only recovery contracts."""
from __future__ import annotations
from typing import Any, Mapping

SCHEMA = "agent-interface/observation-recovery-v1"
_ALLOWED_FIELDS = {"schema","request_id","session_id","surface_id","freshness_seq","deadline_ms",
                   "want","rejected_action_id","reason"}
_ALLOWED_WANT = {"focus","surface","geometry","motor","observation"}
_REQUIRED_WANT = {"focus","surface","observation"}
_FORBIDDEN_RESULT_KEYS = {"input_ops","lease_extension","lease_transfer",
                          "task_success","effect_verified","authority_granted"}


def _unknown_keys(row: Mapping[str, Any], allowed: set[str]) -> bool:
    return set(row) - allowed


def validate_request(request: Mapping[str, Any]) -> str | None:
    if _unknown_keys(request, _ALLOWED_FIELDS):
        return "UNKNOWN_REQUEST_FIELD"
    if request.get("schema") != SCHEMA:
        return "SCHEMA_MISMATCH"
    if not isinstance(request.get("request_id"), str) or not request["request_id"]:
        return "REQUEST_ID_INVALID"
    if not isinstance(request.get("session_id"), str) or not request["session_id"]:
        return "SESSION_INVALID"
    if not isinstance(request.get("surface_id"), str) or not request["surface_id"]:
        return "SURFACE_INVALID"
    if not isinstance(request.get("freshness_seq"), int) or request["freshness_seq"] < 0:
        return "FRESHNESS_INVALID"
    if not isinstance(request.get("deadline_ms"), int) or not 0 < request["deadline_ms"] <= 60000:
        return "DEADLINE_INVALID"
    if not isinstance(request.get("want"), list) or not request["want"]:
        return "WANT_INVALID"
    if not set(request["want"]) <= _ALLOWED_WANT or not _REQUIRED_WANT <= set(request["want"]):
        return "WANT_INVALID"
    return None


def validate_result(request: Mapping[str, Any], result: Mapping[str, Any],
                    current_seq: int) -> str | None:
    if validate_request(request):
        return "REQUEST_INVALID"
    allowed = {"schema","request_id","session_id","surface_id","freshness_seq",
               "status","focus","surface","geometry","motor","observation",
               "rejection_reason","uncertainty","authority"} | (_FORBIDDEN_RESULT_KEYS - {"authority_granted"})
    if _unknown_keys(result, allowed) or result.get("schema") != SCHEMA:
        return "RESULT_SCHEMA_INVALID"
    if result.get("request_id") != request["request_id"] or result.get("session_id") != request["session_id"]:
        return "IDENTITY_MISMATCH"
    if result.get("surface_id") != request["surface_id"]:
        return "SURFACE_MISMATCH"
    if result.get("freshness_seq") != current_seq:
        return "STALE_RESULT"
    if result.get("authority") is not False:
        return "AUTHORITY_ESCALATION"
    if any(key in result for key in _FORBIDDEN_RESULT_KEYS):
        return "FORBIDDEN_RESULT_FIELD"
    if result.get("status") not in {"READY","UNKNOWN","REJECTED"}:
        return "STATUS_INVALID"
    if result["status"] == "REJECTED" and not isinstance(result.get("rejection_reason"), str):
        return "REJECTION_REASON_MISSING"
    return None
