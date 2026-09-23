"""Pure fail-open O4 VERIFY gate."""
from __future__ import annotations
from typing import Any, Mapping

DECISIONS = ("TRUE","FALSE","UNKNOWN")

def evaluate(receipt: Mapping[str, Any], observation_id: str, intent_epoch: int) -> dict[str, Any]:
    base = {"escalate": True, "authority_grants": 0}
    if receipt.get("authority_grants", 0) != 0:
        return dict(base, decision="UNKNOWN", reason="authority")
    if receipt.get("observation_id") != observation_id:
        return dict(base, decision="UNKNOWN", reason="observation_mismatch")
    if receipt.get("intent_epoch") != intent_epoch:
        return dict(base, decision="UNKNOWN", reason="intent_mismatch")
    decision = receipt.get("decision")
    if decision not in DECISIONS:
        return dict(base, decision="UNKNOWN", reason="decision")
    if decision == "UNKNOWN":
        return dict(base, decision=decision, reason="unknown")
    return {"escalate": False, "authority_grants": 0, "decision": decision, "reason":"current_bound"}
