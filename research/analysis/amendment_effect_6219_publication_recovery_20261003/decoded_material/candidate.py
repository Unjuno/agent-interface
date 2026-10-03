"""Finite no-model amendment ledger candidate; no GUI or action authority."""
from __future__ import annotations

ALLOCATION = "AMENDMENT-EFFECT-LEDGER-6219-T0-CPU-20261002-01"
MAIN_SHA = "460f09c465a2ff0347917bc2a2805f78bcb5cdab"

def resolve(case):
    amendment = case["amendment"]
    if amendment.get("authenticated") is None:
        return {"disposition":"HOLD_AMBIGUOUS_AMENDMENT","generation":case["current_generation"],"retained_effects":case["effects"],"open_clauses":case["before"],"rejected_proposals":[]}
    if amendment.get("authenticated") is not True:
        return {"disposition":"REJECT_UNAUTHENTICATED","generation":case["current_generation"],"retained_effects":case["effects"],"open_clauses":case["before"],"rejected_proposals":[]}
    generation = amendment["generation"]
    rejected = [p["id"] for p in case["proposals"] if p["generation"] < generation]
    effects = list(case["effects"])
    if any(e["state"] == "UNKNOWN" for e in effects):
        return {"disposition":"HOLD_UNKNOWN_DELIVERY","generation":generation,"retained_effects":effects,"open_clauses":amendment["clauses"],"rejected_proposals":rejected}
    goals = list(amendment["clauses"])
    conflicts = [e for e in effects if e["state"] == "COMMITTED_VERIFIED" and e["clause"] not in goals and not e["reversible"]]
    if conflicts:
        return {"disposition":"IMPOSSIBLE_TO_FULLY_SATISFY","generation":generation,"retained_effects":effects,"open_clauses":goals,"rejected_proposals":rejected}
    compensation = [e["clause"] for e in effects if e["state"] == "COMMITTED_VERIFIED" and e["clause"] not in goals and e["reversible"]]
    if compensation and not amendment.get("compensation_allowed", False):
        return {"disposition":"HOLD_COMPENSATION_NOT_AUTHORIZED","generation":generation,"retained_effects":effects,"open_clauses":goals,"rejected_proposals":rejected}
    if compensation:
        return {"disposition":"COMPENSATION_REQUIRED","generation":generation,"retained_effects":effects,"open_clauses":goals,"rejected_proposals":rejected,"compensation_clauses":compensation}
    if not goals:
        return {"disposition":"SATISFIED_NO_EFFECT" if not effects else "SATISFIED_EFFECTS_RETAINED","generation":generation,"retained_effects":effects,"open_clauses":[],"rejected_proposals":rejected}
    satisfied = {e["clause"] for e in effects if e["state"] == "COMMITTED_VERIFIED"}
    return {"disposition":"CONTINUE_NEW_GENERATION","generation":generation,"retained_effects":effects,"open_clauses":[g for g in goals if g not in satisfied],"rejected_proposals":rejected}

def baseline(case, policy):
    a=case["amendment"]
    if policy=="old_plan":
        return {"disposition":"CONTINUE_OLD_PLAN","generation":case["current_generation"],"retained_effects":case["effects"],"open_clauses":case["before"],"rejected_proposals":[]}
    if policy=="prompt_reset":
        return {"disposition":"PROMPT_RESET_ONLY","generation":a["generation"],"retained_effects":[],"open_clauses":a["clauses"],"rejected_proposals":[]}
    if policy=="blanket_undo":
        return {"disposition":"BLANKET_UNDO_ALL" if case["effects"] else "BLANKET_RESTART","generation":a["generation"],"retained_effects":[],"open_clauses":a["clauses"],"rejected_proposals":[]}
    raise ValueError("unknown baseline")

def run(fixture):
    rows=[]
    for case in fixture["cases"]:
        for policy in fixture["policies"]:
            result=resolve(case) if policy=="obligation_ledger" else baseline(case,policy)
            rows.append({"case_id":case["id"],"policy":policy,"result":result})
    return {"schema":"amendment-effect-candidate-raw-v1","allocation":ALLOCATION,"main_sha":MAIN_SHA,"rows":rows}
