"""Fail-closed pure mapping from a native result to MotorState."""
from __future__ import annotations
from typing import Any, Mapping
from .adapter import SCHEMA, validate


class NativeResultError(ValueError):
    pass


def motor_state_from_native_result(raw: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise NativeResultError("native result must be an object")
    if raw.get("extends_lease") is True or raw.get("authority_promotion") is not None:
        raise NativeResultError("authority promotion is not representable")
    result_id = raw.get("result_id")
    if not isinstance(result_id, str) or not result_id:
        raise NativeResultError("result_id required")
    target = raw.get("target")
    if not isinstance(target, Mapping):
        raise NativeResultError("target context required")
    surface = target.get("surface_id") or target.get("window_id")
    frame = target.get("frame")
    if not isinstance(surface, str) or not surface or not isinstance(frame, str) or not frame:
        raise NativeResultError("explicit surface and frame required")
    obs = raw.get("observation")
    execution = raw.get("execution")
    release = raw.get("release")
    if not isinstance(execution, Mapping):
        execution = {}
    if not isinstance(release, Mapping):
        release = {}
    observed = obs.get("observed_pointer") if isinstance(obs, Mapping) else None
    transport_ok = execution.get("transport_passed") is True
    focus_ok = raw.get("focus_confirmed") is True
    ack_id = raw.get("ack_id")
    ack_ok = isinstance(ack_id, str) and bool(ack_id)
    pointer_ok = (isinstance(observed, Mapping) and isinstance(observed.get("x"), (int, float)) and isinstance(observed.get("y"), (int, float)))
    certainty_ok = isinstance(obs, Mapping) and pointer_ok and transport_ok and focus_ok and ack_ok
    uncertainty = "NONE" if certainty_ok else "FOCUS_UNKNOWN" if isinstance(obs, Mapping) else "OS_UNCONFIRMED"
    release_status = "FAILED" if release.get("error") else "VERIFIED_EMPTY" if release.get("final_release_verified") is True else "UNVERIFIED"
    row = {
        "schema": SCHEMA, "state_id": result_id, "owner_id": str(raw.get("owner_id", "owner-unknown")),
        "owner_revision": raw.get("binding_revision", 0),
        "observation_id": str(obs.get("observation_id", "obs-unknown")) if isinstance(obs, Mapping) else "obs-unknown",
        "surface_id": surface, "coordinate_frame": frame,
        "commanded_pointer": raw.get("commanded_pointer", {}), "observed_pointer": observed,
        "held_keys": list(raw.get("held_keys", [])), "held_buttons": list(raw.get("held_buttons", [])),
        "input_ack": {"id": ack_id if ack_ok else "ack-unknown", "status": "ACKED" if transport_ok and ack_ok else "UNKNOWN"},
        "release": {"status": release_status, "retained": True}, "uncertainty": uncertainty,
        "events": [{"type": "RELEASE_TRANSITION", "status": release_status}],
    }
    ok, reason = validate(row)
    if not ok:
        raise NativeResultError("invalid motor state: " + reason)
    return row
