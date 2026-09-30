"""Raw-only audit with literal expected outcomes independent of candidate/oracle."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
TRUSTED_FREEZE_SHA256="8be490ec36eed7ceccf4c3884bd0129ab337f0c873616f35e9dfe14edf920347"
EXPECTED={
    "warm_cpu_feasible":("c1","COMPATIBLE",[],12),
    "unsupported_primitive":("c2","REJECTED",["unsupported_primitive","wrong_evidence_role"],12),
    "wrong_input_role":("c3","REJECTED",["wrong_evidence_role"],12),
    "wrong_output_role":("c4","REJECTED",["wrong_output_role"],12),
    "stale_version":("c5","REJECTED",["stale_version"],12),
    "unknown_verifier":("c6","UNAVAILABLE",["verifier_unknown"],None),
    "resource_unavailable":("c7","UNAVAILABLE",["resource_unavailable","latency_unqualified"],120),
    "cold_budget_violation":("c8","REJECTED",["budget_exceeded"],80),
    "hard_incompatibility_precedes_unavailable":("c9","REJECTED",["stale_version","side_effect_prohibited","resource_unavailable","latency_unqualified"],900),
    "deadline_infeasible":("c10","REJECTED",["deadline_infeasible"],12),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_rows(cases,raw):
    expected_case_ids=set(EXPECTED)
    rows=cases.get("cases",[])
    case_ids=[row.get("case_id") for row in rows]
    checks=[row.get("assignment",{}).get("check_id") for row in rows]
    observed=raw.get("decisions",[])
    observed_ids=[row.get("check_id") for row in observed]
    identity_ok=(set(case_ids)==expected_case_ids and len(case_ids)==len(expected_case_ids) and
                 len(checks)==len(set(checks)) and len(observed_ids)==len(checks) and
                 len(observed_ids)==len(set(observed_ids)) and set(observed_ids)==set(checks))
    errors=[]
    if not identity_ok:
        errors.append("case_or_check_id_bijection")
    by_id={row.get("check_id"):row for row in observed}
    for case in rows:
        key=case.get("case_id")
        if key not in EXPECTED:
            continue
        check_id,status,reasons,cost=EXPECTED[key]
        actual=by_id.get(check_id,{})
        if (case.get("assignment",{}).get("check_id")!=check_id or case.get("expected")!=status or
            case.get("reasons")!=reasons or actual.get("status")!=status or
            actual.get("reasons")!=reasons or actual.get("estimated_cost_ms")!=cost):
            errors.append("decision_mismatch:"+key)
        if (actual.get("dispatch_count")!=0 or actual.get("authority")!="none" or
            actual.get("cost_basis")!="declared_estimate_not_measurement"):
            errors.append("authority_dispatch_cost:"+key)
    ok=identity_ok and not errors
    return {"disposition":"PASS_HOST_CONSTRUCTION_ONLY" if ok else "FAIL_ROW_IDENTITY" if not identity_ok else "FAIL_DECISIONS",
            "case_count":len(rows),"matched":ok,"errors":errors,
            "dispatches":sum(row.get("dispatch_count",-1) for row in observed)}


def main():
    freeze_path=HERE/"FREEZE.json"
    cases_path=HERE/"cases.json"
    registry_path=HERE/"registry.json"
    raw_path=HERE/"results"/"host-construction-01"/"RAW.json"
    freeze=json.loads(freeze_path.read_text())
    cases=json.loads(cases_path.read_text())
    raw=json.loads(raw_path.read_text())
    frozen_sources=all(sha(HERE/name)==digest for name,digest in freeze["source_sha256"].items())
    parent=HERE.parent/"verification_ir_5268_v1"/"candidate.py"
    input_bound=(sha(freeze_path)==TRUSTED_FREEZE_SHA256 and
                 raw.get("schema")=="verifier_registry_5273_raw.v2" and
                 raw.get("allocation")=="verifier-registry-5273-t0-v2-20260930-01" and
                 raw.get("base_commit")=="c12e6079f82d1604a9f9a08445a314e4d59d8846" and
                 raw.get("freeze_sha256")==sha(freeze_path) and
                 raw.get("registry_sha256")==sha(registry_path) and
                 raw.get("cases_sha256")==sha(cases_path) and
                 raw.get("parent_ir_candidate_sha256")==sha(parent)==freeze.get("parent_ir_candidate_sha256"))
    result=audit_rows(cases,raw)
    result.update({"source_binding":frozen_sources,"input_binding":input_bound,
                   "raw_sha256":sha(raw_path),"freeze_sha256":sha(freeze_path),
                   "auditor_sha256":sha(HERE/"audit.py")})
    if not frozen_sources or not input_bound:
        result["disposition"]="FAIL_BINDING"
    out=raw_path.parent/"AUDIT.json"
    out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"disposition":result["disposition"],"cases":result["case_count"],
                      "errors":len(result["errors"]),"source_binding":frozen_sources,
                      "input_binding":input_bound,"audit_sha256":sha(out)},sort_keys=True))


if __name__=="__main__":
    main()
