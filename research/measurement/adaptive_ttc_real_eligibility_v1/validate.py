#!/usr/bin/env python3
import json, sys
from pathlib import Path

REQUIRED_BLOBS = {
    "cross_domain_rule_vm_result": "20ed6bc4c682e5d2e1cf60fb44f4fcdf5a1bd21d",
    "map01_v31_representation": "9b131cc22860ca210959202790688a0759bc8b24",
    "operation_target_private_x11_result": "0b98bdfd7f00d063f252b5e9db27f9868eb4c9a8",
}
REQUIRED_AUDIT_BLOB = "9f22e0291e38b450bdbac105d5ec42b3e4941b65"
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
    vm=s["cross_domain_rule_vm_result"]
    if vm.get("decision") != "PASS_CROSS_DOMAIN_RULE_VM_SCOPED": errors.append("rule_vm_decision")
    if not vm.get("chromium_exact") or vm.get("chromium_rows") != 8192 or vm.get("openttd_retained_exact") != 5 or not vm.get("controls_fail_closed"): errors.append("rule_vm_exactness")
    if vm.get("learned_residual_rows") != 0: errors.append("rule_vm_residual_count")
    v31=s["map01_v31_representation"]
    if v31.get("eligible_rows") != 5 or v31.get("enriched_collisions") != 0 or not v31.get("report_boundary_requires_larger_corpus"): errors.append("v31_boundary")
    x=s["operation_target_private_x11_result"]
    if x.get("audit_git_blob") != REQUIRED_AUDIT_BLOB: errors.append("private_x11_audit_blob")
    expected=("PASS_PRIVATE_X11_OPERATION_TARGET_CONTRACT_SCOPED",1,96,96,48,48,0,0,0,0,0,0,True,0)
    actual=(x.get("decision"),x.get("formal_invocations"),x.get("rows"),x.get("acceptable_membership"),x.get("positive_coverage"),x.get("semantic_negatives"),x.get("false_executable_negatives"),x.get("stale_executable"),x.get("missing_arguments"),x.get("public_oracle_leakage"),x.get("model_calls"),x.get("task_input_actions"),x.get("independent_decision_oracle"),x.get("learned_residual_rows"))
    if actual != expected: errors.append("private_x11_result")
    integ=d["integrity"]
    if integ.get("uses_future_or_oracle_as_feature"): errors.append("feature_leakage")
    if integ.get("claims_cross_domain_deterministic_rows_as_residual"): errors.append("cross_domain_closure_relabelled_as_residual")
    if integ.get("claims_private_x11_deterministic_rows_as_residual"): errors.append("private_x11_closure_relabelled_as_residual")
    if integ.get("claims_five_rows_are_sufficient_despite_source_boundary"): errors.append("row_sufficiency_overclaim")
    a=d["activation"]
    if set(a) != set(REQ): errors.append("activation_schema")
    # Five retained MAP01 rows cannot satisfy the source's explicit larger-corpus requirement.
    if a.get("enough_leakage_free_rows") and v31.get("eligible_rows")==5 and v31.get("report_boundary_requires_larger_corpus"):
        errors.append("activation_rows_contradict_source")
    # Both real-state rule families are closed by deterministic logic. They cannot be relabelled as NEEDS_POLICY residuals.
    if a.get("genuine_needs_policy_residual") and (vm.get("learned_residual_rows")==0 and x.get("learned_residual_rows")==0):
        errors.append("residual_claim_contradicts_deterministic_closure")
    # The completed #1223 result does establish an independent decision-level semantic acceptable-set oracle.
    if not a.get("independent_semantic_effect_oracle") and x.get("independent_decision_oracle"):
        errors.append("oracle_prerequisite_understated")
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
    d=json.loads(Path(sys.argv[1]).read_text())
    out=evaluate(d)
    print(json.dumps(out,sort_keys=True))
    if len(sys.argv)>2: Path(sys.argv[2]).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")

if __name__=="__main__": main()
