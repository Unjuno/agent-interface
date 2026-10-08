"""Build source-bound synthetic displays without reading sealed truth."""
from __future__ import annotations

import copy
import hashlib

POLICIES = ("A_CONTINUOUS", "B_EVIDENCE", "C_PERIODIC", "D_HARD_ALERT")


def build(stimuli: dict) -> dict:
    events = stimuli["events"]
    by_id = {event["id"]: event for event in events}
    if len(by_id) != len(events):
        raise ValueError("duplicate opportunity id")
    rows = []
    fixed = set(stimuli["fixed_checkpoint_positions"])
    predicates = stimuli["review_predicates"]
    for event in events:
        if event["block"] not in stimuli["blocks"]:
            raise ValueError("unknown block")
        if not 1 <= event["position"] <= stimuli["positions_per_block"]:
            raise ValueError("invalid position")
        gate = event.get("machine_gate", {"state": "CLEAR", "release_allowed": True})
        for policy in POLICIES:
            hard_alert = gate["state"] == "STOP_LATCHED"
            if policy == "A_CONTINUOUS":
                visible = True
                kind = "quiet_progress"
            elif policy == "B_EVIDENCE":
                visible = event["id"] in predicates or hard_alert
                kind = "evidence_triggered" if event["id"] in predicates else ("mandatory_hard_alert" if hard_alert else "quiet")
            elif policy == "C_PERIODIC":
                visible = event["position"] in fixed or hard_alert
                kind = "fixed_periodic" if event["position"] in fixed else ("mandatory_hard_alert" if hard_alert else "quiet")
            else:
                visible = hard_alert
                kind = "mandatory_hard_alert" if hard_alert else "quiet"
            if not event["evidence"] and not hard_alert:
                # No captured record is not a human-visible cue. Keep the
                # assigned opportunity row, but omit it from the display.
                visible = False
                kind = "no_captured_signal"
            # The same source-bound factual schema is exposed in B and C review.
            payload = {
                "source_ref": event["source_ref"] if visible else None,
                "evidence": copy.deepcopy(event["evidence"]) if visible else None,
            }
            if policy == "A_CONTINUOUS" and visible:
                payload["progress_kind"] = "routine_recorded_progress"
            token = hashlib.sha256(f"{stimuli['allocation']}:{event['id']}".encode()).hexdigest()[:16]
            rows.append({
                "opportunity_id": event["id"],
                "opportunity_token": token,
                "block": event["block"],
                "position": event["position"],
                "timestamp_ms": event["time_ms"],
                "policy": policy,
                "display_kind": kind,
                "review_visible": visible,
                "review_predicate": predicates.get(event["id"]) if policy == "B_EVIDENCE" and visible and not hard_alert else None,
                "payload": payload,
                "machine_gate": dict(gate),
                "hard_alert_visible": hard_alert,
                "human_response": None,
            })
    return {
        "schema": "quiet-supervision-material-v1",
        "allocation": stimuli["allocation"],
        "blocks": list(stimuli["blocks"]),
        "opportunities_per_policy": len(events),
        "rows": rows,
    }
