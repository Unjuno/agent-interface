"""Evidence-derived successor scorer for merged #2563."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping

@dataclass(frozen=True)
class AuditResult:
    outcome: str
    ready: bool
    reason: str

_EXPECTED={"USEFUL_EFFECT":"USEFUL","UNAVAILABLE_BEFORE_INPUT":"UNAVAILABLE","GUARDED_REFUSAL":"REFUSED","ACCEPTED_NO_EFFECT":"NO_EFFECT","PARTIAL_COLLATERAL":"PARTIAL","STALE_REPAIR":"REPAIRED"}

def audit_receipt(receipt: Mapping[str, Any]) -> AuditResult:
    if not isinstance(receipt, Mapping): return AuditResult("UNKNOWN",False,"shape")
    for key in ("case","authority_grants","cleanup","effect_receipt","input_ledger","session_id","window_id","observation_revision","binding_revision"):
        if key not in receipt: return AuditResult("UNKNOWN",False,"missing_"+key)
    if receipt["authority_grants"] != 0: return AuditResult("UNKNOWN",False,"authority")
    cleanup=receipt["cleanup"]
    if not isinstance(cleanup, Mapping) or cleanup.get("status") != "clean":
        return AuditResult("CLEANUP_FAILURE",False,"cleanup")
    case=receipt["case"]
    if case == "AMBIGUOUS_DELIVERY": return AuditResult("UNKNOWN",False,"ambiguous_no_replay")
    if case not in _EXPECTED or not receipt["window_id"]: return AuditResult("UNKNOWN",False,"case_or_target")
    if receipt["observation_revision"] != receipt["binding_revision"]:
        return AuditResult("UNKNOWN",False,"stale_binding")
    effect=receipt["effect_receipt"]; ledger=receipt["input_ledger"]
    if not isinstance(effect, Mapping) or not isinstance(ledger, list): return AuditResult("UNKNOWN",False,"evidence_shape")
    if case == "STALE_REPAIR":
        repair=receipt.get("repair")
        if not isinstance(repair, Mapping) or repair.get("bounded") is not True or repair.get("prior_observation_revision") == receipt["observation_revision"]:
            return AuditResult("UNKNOWN",False,"repair_lineage")
    observed=effect.get("outcome")
    if case == "USEFUL_EFFECT" and observed != "USEFUL": return AuditResult("UNKNOWN",False,"effect_mismatch")
    if case == "ACCEPTED_NO_EFFECT" and observed != "NO_EFFECT": return AuditResult("UNKNOWN",False,"effect_mismatch")
    if case == "PARTIAL_COLLATERAL" and observed != "PARTIAL": return AuditResult("UNKNOWN",False,"effect_mismatch")
    if case == "UNAVAILABLE_BEFORE_INPUT" and ledger: return AuditResult("UNKNOWN",False,"ledger_mismatch")
    return AuditResult(_EXPECTED[case],True,"evidence_derived")
