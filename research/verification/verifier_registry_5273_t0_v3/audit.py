"""Independent raw-only verifier: no candidate or test-oracle imports."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
TRUSTED_FREEZE_SHA256="2ca6eaff9bc44c64303c798c463f11fec4e591b2a18033d260035e2994c8abe4"
RAW_FIELDS={"schema","allocation","base_commit","freeze_sha256","registry_sha256","fixtures_sha256","parent_ir_candidate_sha256","plans"}
PLAN_FIELDS={"case_id","plan_id","schema","status","reasons","decisions","dispatch_count","authority"}
DECISION_FIELDS={"check_id","status","reasons","dispatch_count","authority","cost_basis","estimated_cost_ms"}
CHECK_FIELDS={"check_id","primitive","subject_ref","criticality","required_evidence_role","verifier_class","dependencies","deadline","budget_class","fallback"}
TOP_FIELDS={"schema","unknown_check_required","checks"}
PRIMITIVES={"TARGET.IDENTITY_CURRENT","TARGET.TARGET_MATCH","TARGET.AMBIGUITY","SEMANTIC.INTENT_MATCH","SEMANTIC.SCOPE_MATCH","AUTHORITY.PERMISSION_CURRENT","AUTHORITY.DECISION_DEADLINE","EFFECT.REVERSIBILITY","EFFECT.POSTCONDITION","META.UNKNOWN_REQUIRED","META.COVERAGE"}
ROLES={"CURRENT_OBSERVATION","CURRENT_INTENT","CURRENT_PERMISSION","CURRENT_CLOCK","CURRENT_ACTION_CONTRACT","VERIFIED_EFFECT","UNKNOWN_REQUIREMENT","COVERAGE_REPORT"}
CRITICALITIES={"MANDATORY","CONDITIONAL_MANDATORY","OPTIONAL"}
EXPECTED={
    "c1":("COMPATIBLE",[],12),
    "c2":("REJECTED",["unsupported_primitive","wrong_evidence_role"],12),
    "c3":("REJECTED",["wrong_evidence_role"],12),
    "c4":("REJECTED",["wrong_output_role"],12),
    "c5":("REJECTED",["stale_version"],12),
    "c6":("UNAVAILABLE",["verifier_unknown"],None),
    "c7":("UNAVAILABLE",["resource_unavailable","latency_unqualified"],120),
    "c8":("REJECTED",["budget_exceeded"],80),
    "c9":("REJECTED",["stale_version","side_effect_prohibited","resource_unavailable","latency_unqualified"],900),
    "c10":("REJECTED",["deadline_infeasible"],12),
    "c11":("UNAVAILABLE",["resource_unavailable","latency_unqualified"],120),
    "c12":("COMPATIBLE",[],12),
}
CASE_IDS={"warm_cpu_feasible","unsupported_primitive","wrong_input_role","wrong_output_role","stale_version","unknown_verifier","resource_unavailable","cold_budget_violation","hard_incompatibility_precedes_unavailable","deadline_infeasible","full_plan_has_unavailable_member"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def raw_field_set_valid(raw):
    return isinstance(raw,dict) and set(raw)==RAW_FIELDS and isinstance(raw.get("plans"),list)


def independent_ir_valid(ir):
    if not isinstance(ir,dict) or set(ir)!=TOP_FIELDS or ir["schema"]!="verification_ir.v0.1" or type(ir["unknown_check_required"]) is not bool or not isinstance(ir["checks"],list):
        return False
    ids=set()
    for row in ir["checks"]:
        if not isinstance(row,dict) or set(row)!=CHECK_FIELDS:
            return False
        if row["primitive"] not in PRIMITIVES or row["required_evidence_role"] not in ROLES or row["criticality"] not in CRITICALITIES:
            return False
        if not all(isinstance(row[key],str) and row[key] for key in ("check_id","subject_ref","verifier_class","budget_class","fallback")):
            return False
        if not isinstance(row["dependencies"],list) or not all(isinstance(dep,str) for dep in row["dependencies"]):
            return False
        if row["deadline"] is not None and (type(row["deadline"]) is not int or row["deadline"]<0):
            return False
        if row["check_id"] in ids:
            return False
        ids.add(row["check_id"])
    for row in ir["checks"]:
        if row["check_id"] in row["dependencies"] or not set(row["dependencies"]).issubset(ids):
            return False
    return any(row["primitive"]=="META.UNKNOWN_REQUIRED" for row in ir["checks"])==ir["unknown_check_required"]


def audit_rows(cases,raw_plans):
    errors=[]
    case_ids=[row.get("case_id") for row in cases]
    raw_case_ids=[row.get("case_id") for row in raw_plans if isinstance(row,dict)]
    if (set(case_ids)!=CASE_IDS or len(case_ids)!=len(CASE_IDS) or
        len(raw_plans)!=len(cases) or len(raw_case_ids)!=len(raw_plans) or
        len(raw_case_ids)!=len(set(raw_case_ids)) or set(raw_case_ids)!=set(case_ids)):
        errors.append("case_id_bijection")
    by_case={row.get("case_id"):row for row in raw_plans if isinstance(row,dict)}
    for case in cases:
        cid=case.get("case_id")
        if not independent_ir_valid(case.get("ir")):
            errors.append("invalid_fixture_ir:"+str(cid))
            continue
        checks=case["ir"]["checks"]
        ids=[row["check_id"] for row in checks]
        assignments=case.get("assignments",[])
        assignment_ids=[row.get("check_id") for row in assignments if isinstance(row,dict)]
        if len(assignment_ids)!=len(assignments) or len(assignment_ids)!=len(set(assignment_ids)) or set(assignment_ids)!=set(ids):
            errors.append("fixture_assignment_bijection:"+str(cid))
        plan=by_case.get(cid)
        if not isinstance(plan,dict) or set(plan)!=PLAN_FIELDS:
            errors.append("raw_plan_schema:"+str(cid))
            continue
        if plan["plan_id"]!=cid or plan["schema"]!="verifier_plan_preflight.v0.3":
            errors.append("raw_plan_identity:"+str(cid))
        decisions=plan.get("decisions")
        if not isinstance(decisions,list) or any(not isinstance(row,dict) or set(row)!=DECISION_FIELDS for row in decisions):
            errors.append("raw_decision_schema:"+str(cid))
            continue
        observed_ids=[row["check_id"] for row in decisions]
        if len(observed_ids)!=len(ids) or len(observed_ids)!=len(set(observed_ids)) or set(observed_ids)!=set(ids):
            errors.append("check_id_bijection:"+str(cid))
            continue
        rows_by_id={row["check_id"]:row for row in decisions}
        for check_id in ids:
            if check_id not in EXPECTED:
                errors.append("unexpected_check_id:"+check_id)
                continue
            status,reasons,cost=EXPECTED[check_id]
            actual=rows_by_id[check_id]
            if (actual["status"]!=status or actual["reasons"]!=reasons or actual["estimated_cost_ms"]!=cost or
                actual["dispatch_count"]!=0 or actual["authority"]!="none" or
                actual["cost_basis"]!="declared_estimate_not_measurement"):
                errors.append("decision_mismatch:"+check_id)
        row_status={key:EXPECTED[key][0] for key in ids if key in EXPECTED}
        overall="REJECTED" if "REJECTED" in row_status.values() else "UNAVAILABLE" if "UNAVAILABLE" in row_status.values() else "COMPATIBLE"
        expected_reasons=[{"check_id":key,"reason":reason} for key in ids for reason in EXPECTED.get(key,(None,[],None))[1]]
        if (plan["status"]!=overall or plan["reasons"]!=expected_reasons or
            plan["dispatch_count"]!=0 or plan["authority"]!="none"):
            errors.append("aggregate_mismatch:"+str(cid))
    return {"ok":not errors,"errors":errors,"case_count":len(cases),"plan_count":len(raw_plans)}


def main():
    freeze_path=HERE/"FREEZE.json"
    freeze=json.loads(freeze_path.read_text())
    from fixtures import CASES
    raw_path=HERE/"results"/"host-construction-01"/"RAW.json"
    raw=json.loads(raw_path.read_text())
    sources_ok=all(sha(HERE/name)==digest for name,digest in freeze["source_sha256"].items())
    parent_path=HERE.parent/"verification_ir_5268_v1"/"candidate.py"
    identity_ok=(sha(freeze_path)==TRUSTED_FREEZE_SHA256 and
        raw_field_set_valid(raw) and raw.get("schema")=="verifier_registry_5273_raw.v3" and
        raw.get("allocation")=="verifier-registry-5273-t0-v3-20260930-01" and
        raw.get("base_commit")=="4e2c0cf6241e3068bbc1afde8c97206c6b731a1b" and
        raw.get("freeze_sha256")==sha(freeze_path) and
        raw.get("registry_sha256")==sha(HERE/"registry.json") and
        raw.get("fixtures_sha256")==sha(HERE/"fixtures.py") and
        raw.get("parent_ir_candidate_sha256")==sha(parent_path)==freeze.get("parent_ir_candidate_sha256"))
    checked=audit_rows(CASES,raw.get("plans",[]))
    disposition="PASS_HOST_CONSTRUCTION_ONLY" if sources_ok and identity_ok and checked["ok"] else "FAIL_BINDING_OR_AUDIT"
    result={"schema":"verifier_registry_5273_raw_audit.v3","disposition":disposition,
        "source_binding":sources_ok,"input_binding":identity_ok,**checked,
        "raw_sha256":sha(raw_path),"freeze_sha256":sha(freeze_path),"auditor_sha256":sha(HERE/"audit.py")}
    out=raw_path.parent/"AUDIT.json"
    out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"disposition":disposition,"case_count":result["case_count"],"plan_count":result["plan_count"],"errors":len(result["errors"]),"raw_sha256":result["raw_sha256"],"audit_sha256":sha(out)},sort_keys=True))


if __name__=="__main__": main()
