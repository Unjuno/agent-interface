"""Fail-closed GTK/X11 second-domain receipt adapter."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping

CASES = ("USEFUL_EFFECT","UNAVAILABLE_BEFORE_INPUT","GUARDED_REFUSAL","ACCEPTED_NO_EFFECT","PARTIAL_COLLATERAL","STALE_REPAIR","AMBIGUOUS_DELIVERY","TERMINAL_CLEANUP_FAILURE")

@dataclass(frozen=True)
class AuditResult:
    case: str
    outcome: str
    ready: bool
    authority_grants: int
    reason: str

def audit_receipt(receipt: Mapping[str, Any]) -> AuditResult:
    case = receipt.get("case")
    if case not in CASES:
        return AuditResult(str(case), "UNKNOWN", False, 0, "case")
    if receipt.get("authority_grants", 0) != 0:
        return AuditResult(case, "UNKNOWN", False, 0, "authority")
    required = ("session_id","window_id","observation_revision","binding_revision","input_ledger","effect_receipt","cleanup")
    if any(key not in receipt for key in required):
        return AuditResult(case, "UNKNOWN", False, 0, "lineage")
    if receipt["window_id"] in (None, "") or receipt["observation_revision"] != receipt["binding_revision"]:
        return AuditResult(case, "UNKNOWN", False, 0, "stale_binding")
    if not isinstance(receipt["input_ledger"], list) or not isinstance(receipt["effect_receipt"], Mapping):
        return AuditResult(case, "UNKNOWN", False, 0, "receipt_shape")
    if case == "AMBIGUOUS_DELIVERY":
        return AuditResult(case, "UNKNOWN", False, 0, "ambiguous_no_replay")
    if case == "TERMINAL_CLEANUP_FAILURE":
        return AuditResult(case, "CLEANUP_FAILURE", False, 0, "cleanup")
    outcomes = {
        "UNAVAILABLE_BEFORE_INPUT":"UNAVAILABLE",
        "GUARDED_REFUSAL":"REFUSED",
        "ACCEPTED_NO_EFFECT":"NO_EFFECT",
        "PARTIAL_COLLATERAL":"PARTIAL",
        "STALE_REPAIR":"REPAIRED",
        "USEFUL_EFFECT":"USEFUL",
    }
    return AuditResult(case, outcomes[case], True, 0, "classified")
