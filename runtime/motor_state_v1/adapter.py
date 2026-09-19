"""Validate planner-facing motor state without granting authority."""
from __future__ import annotations

from typing import Any

SCHEMA = "agent-interface/motor-state-v1"
ALLOWED_UNCERTAINTY = {"NONE", "OS_UNCONFIRMED", "SURFACE_UNKNOWN", "FOCUS_UNKNOWN"}
ALLOWED_RELEASE = {"NOT_TERMINAL", "VERIFIED_EMPTY", "UNVERIFIED", "FAILED"}
_FIELDS = {"schema", "state_id", "owner_id", "owner_revision", "observation_id", "surface_id", "coordinate_frame", "commanded_pointer", "observed_pointer", "held_keys", "held_buttons", "input_ack", "release", "uncertainty", "events"}


def validate(row: Any) -> tuple[bool, str]:
    """Return an acceptance/reason pair; never mutates input or grants authority."""
    if not isinstance(row, dict) or row.get("schema") != SCHEMA:
        return False, "schema"
    for key in ("state_id", "owner_id", "observation_id", "surface_id", "coordinate_frame"):
        if not isinstance(row.get(key), str) or not row[key]:
            return False, key
    if type(row.get("owner_revision")) is not int or row["owner_revision"] < 0:
        return False, "owner_revision"
    if set(row) - _FIELDS:
        return False, "unknown_or_authority_field"
    if not isinstance(row.get("commanded_pointer"), dict):
        return False, "commanded_pointer"
    if row.get("observed_pointer") is not None and not isinstance(row["observed_pointer"], dict):
        return False, "observed_pointer"
    if not isinstance(row.get("held_keys"), list) or not isinstance(row.get("held_buttons"), list):
        return False, "held"
    ack = row.get("input_ack")
    if not isinstance(ack, dict) or not isinstance(ack.get("id"), str) or ack.get("status") not in {"ACKED", "PENDING", "UNKNOWN"}:
        return False, "input_ack"
    release = row.get("release")
    if not isinstance(release, dict) or release.get("status") not in ALLOWED_RELEASE or type(release.get("retained")) is not bool:
        return False, "release"
    if row.get("uncertainty") not in ALLOWED_UNCERTAINTY:
        return False, "uncertainty"
    events = row.get("events")
    if not isinstance(events, list):
        return False, "events"
    if release["status"] in {"VERIFIED_EMPTY", "UNVERIFIED", "FAILED"} and not any(isinstance(event, dict) and event.get("type") == "RELEASE_TRANSITION" for event in events):
        return False, "release_event_not_retained"
    if row.get("uncertainty") == "NONE" and (row.get("observed_pointer") is None or ack["status"] != "ACKED"):
        return False, "implicit_confirmation"
    return True, "ok"