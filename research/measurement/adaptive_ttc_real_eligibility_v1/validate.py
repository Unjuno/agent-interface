#!/usr/bin/env python3
import copy, json, sys
from pathlib import Path

REQUIRED_BLOBS = {
    "cross_domain_rule_vm_result": "20ed6bc4c682e5d2e1cf60fb44f4fcdf5a1bd21d",
    "map01_v31_representation": "9b131cc22860ca210959202790688a0759bc8b24",
    "operation_target_realstate_reservation": "eaf2e5c01288e2531a1767ffd22731ee6d9bb646",
}
REQ = [
    "real_caller_visible_contract",
    "representation_sufficient_for_frozen_residual",
    "genuine_needs_policy_residual",
    "enough_leakage_free_rows",
    "independent_semantic_effect_oracle",
    "first_rung_no_live_input_authority",
]

def evaluate(d):
    errors=[]
    s=d["sources"]
    for k,v in REQUIRED_BLOBS.items():
        if s.get(k,{}).get("git_blob") != v: errors.append("source_blob:"+k)
    if s["cross_domain_rule_vm_result"].get("decision") != "PASS_CROSS_DOMAIN_RULE_VM_SCOPED": errors.append("rule_vm_decision")
    if not s["cross_domain_rule_vm_result"].get("chromium_exact") or s["cross_domain_rule_vm_result"].get("openttd_retained_exact") != 5: errors.append("rule_vm_exactness")
    if s["map01_v31_representation"].get("eligible_rows") != 5 or s["map01_v31_representation"].get("enriched_collisions") != 0: errors.append("v31_fixture")
    integ=d["integrity"]
    if integ.get("uses_unpublished_active_result"): errors.append("unpublished_active_result_consumed")
    if integ.get("uses_future_or_oracle_as_feature"): errors.append("feature_leakage")
    if integ.get("claims_deterministic_exact_rows_as_residual"): errors.append("deterministic_closure_relabelled_as_residual")
    if integ.get("claims_five_rows_are_sufficient_despite_source_boundary"):
        errors.append("row_sufficiency_overclaim")
    a=d["activation"]
    if set(a) != set(REQ): errors.append("activation_schema")
    if a.get("enough_leakage_free_rows") and s["map01_v31_representation"].get("eligible_rows") == 5 and s["map01_v31_representation"].get("report_boundary_requires_larger_corpus"):
        errors.append("activation_rows_contradict_source")
    if a.get("independent_semantic_effect_oracle") and not s["map01_v31_representation"].get("independent_semantic_effect_oracle"):
        errors.append("oracle_claim_contradicts_source")
    if a.get("genuine_needs_policy_residual") and integ.get("claims_deterministic_exact_rows_as_residual"):
        errors.append("residual_claim_uses_closed_rule_rows")
    if errors:
        return {"decision":"FAIL_INTEGRITY","eligible":False,"errors":errors,"prerequisites":a}
    eligible=all(a[k] for k in REQ)
    return {
        "decision":"ELIGIBLE_FOR_ADAPTIVE_TTC_SHADOW" if eligible else "HOLD_NO_REAL_ADAPTIVE_RESIDUAL",
        "eligible":eligible,
        "errors":[],
        "failed_prerequisites":[k for k in REQ if not a[k]],
        "prerequisites":a,
    }

def main():
    p=Path(sys.argv[1])
    d=json.loads(p.read_text())
    out=evaluate(d)
    print(json.dumps(out,sort_keys=True))
    if len(sys.argv)>2: Path(sys.argv[2]).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")

if __name__=="__main__": main()
