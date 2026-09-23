"""Pure, fail-closed bridge from native dispatch receipts to MotorState."""
from __future__ import annotations
from copy import deepcopy
from typing import Any
from .adapter import validate
_REQUIRED_CONTEXT = ("state_id","owner_id","owner_revision","observation_id","surface_id","coordinate_frame","commanded_pointer")
def from_dispatch_result(raw: Any, *, context: dict[str, Any]) -> dict[str, Any]:
    """Return validation evidence; never infer identity, focus, effect, or authority."""
    if not isinstance(raw, dict):
        return {"accepted": False, "reason": "native_result"}
    if not isinstance(context, dict) or any(key not in context or (isinstance(context[key], str) and not context[key]) for key in _REQUIRED_CONTEXT):
        return {"accepted": False, "reason": "missing_context", "uncertainty": "OS_UNCONFIRMED"}
    row = {
        "schema": "agent-interface/motor-state-v1",
        "state_id": context["state_id"], "owner_id": context["owner_id"], "owner_revision": context["owner_revision"],
        "observation_id": context["observation_id"], "surface_id": context["surface_id"], "coordinate_frame": context["coordinate_frame"],
        "commanded_pointer": deepcopy(context["commanded_pointer"]), "observed_pointer": None,
        "held_keys": [], "held_buttons": [], "input_ack": {"id": str(raw.get("result_id","dispatch-unknown")), "status": "UNKNOWN"},
        "release": {"status": "FAILED", "retained": True}, "uncertainty": "OS_UNCONFIRMED",
        "events": [{"type": "RELEASE_TRANSITION", "status": "FAILED"}],
    }
    if raw.get("admission") == "accepted":
        row["input_ack"]["status"] = "ACKED"
    execution = raw.get("execution")
    releases = execution.get("releases", []) if isinstance(execution, dict) else []
    if isinstance(releases, list) and releases and all(isinstance(item, dict) and item.get("verified") is True for item in releases):
        row["release"] = {"status": "VERIFIED_EMPTY", "retained": True}
        row["events"] = [{"type": "RELEASE_TRANSITION", "status": "VERIFIED_EMPTY"}]
    accepted, reason = validate(row)
    return {"accepted": accepted, "reason": reason, "state": row}
