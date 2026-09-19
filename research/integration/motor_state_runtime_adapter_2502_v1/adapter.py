"""Pure native-result to MotorState v1 adapter.

This module never grants authority, renews a lease, dispatches input, or infers
application effect. Missing OS evidence is represented as uncertainty.
"""
from __future__ import annotations
from typing import Any

SCHEMA="agent-interface/motor-state-v1"
UNCERTAINTY={"NONE","OS_UNCONFIRMED","SURFACE_UNKNOWN","FOCUS_UNKNOWN"}

class MotorStateAdapterError(ValueError):
    pass

def motor_state_from_native_result(raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw,dict): raise MotorStateAdapterError("native result must be object")
    if raw.get("extends_lease") is True or raw.get("authority_promotion") is not None:
        raise MotorStateAdapterError("authority promotion is not representable")
    target=raw.get("target") if isinstance(raw.get("target"),dict) else {}
    obs=raw.get("observation") if isinstance(raw.get("observation"),dict) else None
    execution=raw.get("execution") if isinstance(raw.get("execution"),dict) else {}
    release=raw.get("release") if isinstance(raw.get("release"),dict) else {}
    if not raw.get("result_id"): raise MotorStateAdapterError("result_id required")
    release_status=("VERIFIED_EMPTY" if release.get("final_release_verified") is True
                     else "FAILED" if release.get("error") else "UNVERIFIED")
    uncertainty="NONE"
    if obs is None: uncertainty="OS_UNCONFIRMED"
    elif raw.get("focus_confirmed") is not True: uncertainty="FOCUS_UNKNOWN"
    surface=target.get("surface_id") or target.get("window_id")
    if not surface: uncertainty="SURFACE_UNKNOWN"; surface="surface-unknown"
    frame=target.get("frame","window_client")
    event={"type":"RELEASE_TRANSITION","status":release_status}
    return {
      "schema":SCHEMA,"state_id":str(raw["result_id"]),
      "owner_id":str(raw.get("owner_id","owner-unknown")),
      "owner_revision":int(raw.get("binding_revision",0)),
      "observation_id":str(obs.get("observation_id","obs-unknown") if obs else "obs-unknown"),
      "surface_id":str(surface),"coordinate_frame":str(frame),
      "commanded_pointer":raw.get("commanded_pointer",{}),
      "observed_pointer":obs.get("observed_pointer") if obs else None,
      "held_keys":list(raw.get("held_keys",[])),"held_buttons":list(raw.get("held_buttons",[])),
      "input_ack":{"id":str(raw.get("ack_id","ack-unknown")),
                   "status":"ACKED" if execution.get("transport_passed") is True else "UNKNOWN"},
      "release":{"status":release_status,"retained":True},
      "uncertainty":uncertainty,"events":[event],
    }
