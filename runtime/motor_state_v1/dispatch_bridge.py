"""Pure, explicit-context bridge for native dispatch results.

This module does not call a backend, mint authority, or infer task effect.
"""
from __future__ import annotations

from typing import Any, Mapping

from .adapter import SCHEMA, validate

_ALLOWED = {"accepted", "rejected", "failed", "released"}


def bridge_dispatch_result(
    result: Mapping[str, Any],
    context: Mapping[str, Any] | None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Map a raw dispatch result plus caller-owned context into MotorState."""
    report: dict[str, Any] = {"bridge": "dispatch-result-v1", "accepted": False}
    if not isinstance(result, Mapping):
        report["reason"] = "result_not_mapping"
        return None, report
    status = result.get("status")
    if status not in _ALLOWED:
        report["reason"] = "status"
        return None, report
    report["source_status"] = status
    if context is None or not isinstance(context, Mapping):
        report["reason"] = "explicit_context_required"
        return None, report

    required = ("state_id", "owner_id", "owner_revision", "observation_id",
                "surface_id", "coordinate_frame")
    if any(key not in context for key in required):
        report["reason"] = "context_incomplete"
        return None, report
    if type(context["owner_revision"]) is not int or context["owner_revision"] < 0:
        report["reason"] = "context_owner_revision"
        return None, report

    release = result.get("release")
    if not isinstance(release, Mapping):
        release = {"status": "NOT_TERMINAL", "retained": False}
    else:
        release = dict(release)
    events = list(context.get("events", []))
    if not isinstance(events, list):
        report["reason"] = "context_events"
        return None, report
    if status in {"released", "failed"}:
        events.append({"type": "RELEASE_TRANSITION", "source": "dispatch_result"})

    row = {
        "schema": SCHEMA,
        "state_id": context["state_id"],
        "owner_id": context["owner_id"],
        "owner_revision": context["owner_revision"],
        "observation_id": context["observation_id"],
        "surface_id": context["surface_id"],
        "coordinate_frame": context["coordinate_frame"],
        "commanded_pointer": dict(context.get("commanded_pointer", {})),
        "observed_pointer": context.get("observed_pointer"),
        "held_keys": list(context.get("held_keys", [])),
        "held_buttons": list(context.get("held_buttons", [])),
        "input_ack": dict(context.get("input_ack", {"id": "unknown", "status": "UNKNOWN"})),
        "release": release,
        "uncertainty": context.get("uncertainty", "OS_UNCONFIRMED"),
        "events": events,
    }
    ok, reason = validate(row)
    report["validation"] = reason
    report["accepted"] = ok and status == "accepted"
    if not ok:
        report["reason"] = "motor_state_validation"
        return None, report
    if status != "accepted":
        report["reason"] = "dispatch_not_accepted"
        return None, report
    return row, report