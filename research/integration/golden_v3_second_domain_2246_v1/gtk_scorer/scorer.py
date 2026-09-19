"""Independent GTK receipt scorer.

Consumes frozen receipts only. It deliberately does not import or call the
adapter and never grants authority or replays ambiguous delivery.
"""
from __future__ import annotations
from typing import Any, Mapping

CASES = ("USEFUL_EFFECT","UNAVAILABLE_BEFORE_INPUT","GUARDED_REFUSAL","ACCEPTED_NO_EFFECT","PARTIAL_COLLATERAL","STALE_REPAIR","AMBIGUOUS_DELIVERY","TERMINAL_CLEANUP_FAILURE")

def score(receipt: Mapping[str, Any]) -> dict[str, Any]:
    case = receipt.get("case")
    base = {"case": case, "authority_grants": 0, "ready": False}
    if case not in CASES:
        return dict(base, outcome="UNKNOWN", reason="case")
    if receipt.get("authority_grants", 0) != 0:
        return dict(base, outcome="UNKNOWN", reason="authority")
    required = ("session_id","window_id","observation_revision","binding_revision","input_ledger","effect_receipt","cleanup")
    if any(k not in receipt for k in required):
        return dict(base, outcome="UNKNOWN", reason="lineage")
    if not receipt["window_id"] or receipt["observation_revision"] != receipt["binding_revision"]:
        return dict(base, outcome="UNKNOWN", reason="stale_binding")
    if not isinstance(receipt["input_ledger"], list) or not isinstance(receipt["effect_receipt"], Mapping):
        return dict(base, outcome="UNKNOWN", reason="shape")
    if case == "AMBIGUOUS_DELIVERY":
        return dict(base, outcome="UNKNOWN", reason="ambiguous_no_replay")
    if case == "TERMINAL_CLEANUP_FAILURE":
        return dict(base, outcome="CLEANUP_FAILURE", reason="cleanup")
    outcomes = {"USEFUL_EFFECT":"USEFUL","UNAVAILABLE_BEFORE_INPUT":"UNAVAILABLE","GUARDED_REFUSAL":"REFUSED","ACCEPTED_NO_EFFECT":"NO_EFFECT","PARTIAL_COLLATERAL":"PARTIAL","STALE_REPAIR":"REPAIRED"}
    return dict(base, outcome=outcomes[case], ready=True, reason="independent_classification")
