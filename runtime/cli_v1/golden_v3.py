"""Public golden-v3 result boundary over the existing CLI dispatch API."""
from __future__ import annotations

from typing import Any, Mapping

from .api import dispatch

STATUSES = {"invalid_request", "backend_unavailable", "runtime_failed", "returned"}
LIFECYCLE = {"doctor", "model_attempt", "observation", "dispatch", "refusal", "effect", "repair", "release", "cleanup"}
NESTED_REFUSAL_STATUSES = {"refused", "invalid_request", "backend_unavailable", "runtime_failed"}


def adapt_dispatch_result(
    result: dict[str, Any],
    *,
    usage: Mapping[str, Any] | None = None,
    lifecycle: list[str] | None = None,
) -> dict[str, Any]:
    status = result.get("status")
    states = list(lifecycle) if lifecycle is not None else ["dispatch"]
    if status not in STATUSES:
        return _reject("UNKNOWN_STATUS", result, usage)
    if any(state not in LIFECYCLE for state in states):
        return _reject("UNKNOWN_LIFECYCLE", result, usage)

    cleanup = result.get("cleanup_error")
    nested = result.get("result") if isinstance(result.get("result"), dict) else {}
    nested_status = nested.get("status")
    diagnostic = result.get("error")
    if isinstance(nested.get("error"), str):
        diagnostic = nested["error"]

    program_completed = nested.get("program_completed") is True
    task_success = nested.get("task_success") is True

    if cleanup is not None:
        mapped = "cleanup_failed"
        task_success = False
    elif status in {"invalid_request", "backend_unavailable"}:
        mapped = "refused"
        program_completed = False
        task_success = False
    elif status == "runtime_failed":
        mapped = "partial"
        task_success = False
    elif nested_status in NESTED_REFUSAL_STATUSES:
        mapped = "refused"
        program_completed = False
        task_success = False
    else:
        mapped = "success" if program_completed and task_success else "partial"

    row = {
        "schema": "golden-v3-result-v1",
        "program_completed": program_completed,
        "task_success": task_success,
        "authority_granted": False,
        "status": mapped,
        "partial_effects": nested.get("partial_effects", []),
        "cleanup_error": cleanup,
        "lifecycle": states,
        "usage": dict(usage or result.get("usage") or {}),
    }
    if diagnostic is not None:
        row["diagnostic"] = diagnostic
    return row


def _reject(
    reason: str,
    result: dict[str, Any],
    usage: Mapping[str, Any] | None,
) -> dict[str, Any]:
    return {
        "schema": "golden-v3-result-v1",
        "program_completed": False,
        "task_success": False,
        "authority_granted": False,
        "status": "refused",
        "partial_effects": [],
        "cleanup_error": None,
        "lifecycle": [],
        "usage": dict(usage or result.get("usage") or {}),
        "adapter_error": reason,
        "diagnostic": result.get("error"),
    }


def dispatch_golden_v3(
    program: dict[str, Any],
    targets: Mapping[str, int],
    *,
    current_observation_seq: int,
    current_binding_revision: int,
    display_name: str | None = None,
    usage: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    raw = dispatch(
        program,
        targets,
        current_observation_seq=current_observation_seq,
        current_binding_revision=current_binding_revision,
        display_name=display_name,
    )
    return adapt_dispatch_result(raw, usage=usage)
