from __future__ import annotations
import argparse, copy, hashlib, json, pathlib, sys

TYPES = ("file_digest", "window_geometry", "typed_state")
SCENARIOS = ("valid", "no_effect", "stale", "wrong_target", "partial", "ambiguous", "missing_receipt", "malformed", "pixel_only", "cleanup_failure")
POLICIES = ("RICH_AGENT_FIRST", "DETERMINISTIC_FIRST", "DETERMINISTIC_ONLY_FOR_KNOWN")
KNOWN = {"valid", "no_effect", "stale", "wrong_target", "partial", "pixel_only"}
EXPECTED_BINDING = {
    "workflow_run": 35466506122,
    "workflow_head": "6960809cdf9ccc2c2cda24ad84cab94c3cd2b4b6",
    "artifact_id": 10590764445,
    "artifact_zip_sha256": "863177586ae3d686c05b2c150967a9c426ef8d460b86ae5b8fc9a0243954b728",
    "artifact_raw_sha256": "ce1e0372f1f5c8387c0630436e5d1208f4e810c42711e544e3c4073f790534e0",
    "artifact_audit_sha256": "cb0d8ff3aa419bc15c423bd0331763be30f39eb80ad2423c913a9f981b242446",
    "experiment_blob": "0cd6b755cf54d8c01b254b2f8ee52610a29410f2",
    "retained_audit_blob": "a234184fbb583911cea3a66d0eb01e4fe4ce894f",
    "dockerfile_blob": "263520dc3ce3f10fbc4905b8893dad1946e5a9cf",
    "workflow_blob": "32418aa8b5af29851d2a9f7ac0652bf5df07885b",
}

def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def expected_evidence(kind: str, scenario: str) -> dict:
    expected = {"file_digest":"sha256:new", "window_geometry":"1024x768", "typed_state":"saved"}[kind]
    changed = {
        "no_effect": {"file_digest":"sha256:old", "window_geometry":"800x600", "typed_state":"dirty"}[kind],
        "partial": {"file_digest":"sha256:partial", "window_geometry":"1024x600", "typed_state":"saving"}[kind],
        "pixel_only": {"file_digest":"sha256:pixel", "window_geometry":"1024x768", "typed_state":"saved"}[kind],
    }
    observed = changed.get(scenario, expected)
    return {
        "kind": kind,
        "scenario": scenario,
        "target": "target-" + kind,
        "expected": expected,
        "observed": observed,
        "receipt": scenario not in {"missing_receipt", "ambiguous"},
        "sequence": 3 if scenario in {"stale", "malformed"} else 7,
        "target_observed": scenario != "wrong_target",
        "pixel_changed": scenario == "pixel_only",
    }

def expected_verifier(e: dict) -> dict:
    if e["scenario"] == "cleanup_failure":
        return {"verdict":"ESCALATE_RICH_AGENT", "reason":"cleanup_failure"}
    if not e["receipt"]:
        return {"verdict":"ESCALATE_RICH_AGENT", "reason":"missing_or_ambiguous_receipt"}
    if e["sequence"] != 7:
        return {"verdict":"ESCALATE_RICH_AGENT", "reason":"stale_observation"}
    if not e["target_observed"]:
        return {"verdict":"ESCALATE_RICH_AGENT", "reason":"wrong_target"}
    if e["observed"] == e["expected"] and not e["pixel_changed"]:
        return {"verdict":"PASS_POSTCONDITION", "reason":"exact_typed_effect"}
    return {"verdict":"FAIL_POSTCONDITION", "reason":"effect_mismatch"}

def expected_rich(policy: str, scenario: str, verdict: str) -> int:
    if policy == "RICH_AGENT_FIRST": return 1
    if policy == "DETERMINISTIC_FIRST": return int(verdict == "ESCALATE_RICH_AGENT")
    return int(scenario not in KNOWN)

def audit(rows: list, binding: dict, artifact_audit: dict) -> dict:
    errors=[]
    if binding != EXPECTED_BINDING:
        errors.append("binding_mismatch")
    expected_ids={(k,s,p) for k in TYPES for s in SCENARIOS for p in POLICIES}
    seen=[]
    counts={p:0 for p in POLICIES}
    if len(rows)!=90: errors.append(f"row_count:{len(rows)}")
    for idx,row in enumerate(rows):
        try:
            ident=(row["kind"],row["scenario"],row["policy"]); seen.append(ident)
            if ident not in expected_ids: errors.append(f"identity:{idx}:{ident}"); continue
            exp_e=expected_evidence(row["kind"],row["scenario"])
            if row.get("evidence") != exp_e: errors.append(f"evidence:{idx}:{ident}")
            exp_v=expected_verifier(exp_e)
            if row.get("verifier") != exp_v: errors.append(f"verifier:{idx}:{ident}")
            exp_r=expected_rich(row["policy"],row["scenario"],exp_v["verdict"])
            if type(row.get("rich_agent_calls")) is not int or row.get("rich_agent_calls") != exp_r:
                errors.append(f"rich_agent_calls:{idx}:{ident}")
            counts[row["policy"]] += exp_r
            if row["scenario"] != "valid" and row.get("verifier",{}).get("verdict") == "PASS_POSTCONDITION":
                errors.append(f"false_success:{idx}:{ident}")
        except Exception as e:
            errors.append(f"row_exception:{idx}:{type(e).__name__}:{e}")
    if set(seen)!=expected_ids or len(seen)!=len(set(seen)):
        errors.append("identity_denominator")
    if counts != {"RICH_AGENT_FIRST":30,"DETERMINISTIC_FIRST":18,"DETERMINISTIC_ONLY_FOR_KNOWN":12}:
        errors.append(f"rich_counts:{counts}")
    expected_hist={
        "errors":[],"rich_agent_calls":{"DETERMINISTIC_FIRST":18,"DETERMINISTIC_ONLY_FOR_KNOWN":12,"RICH_AGENT_FIRST":30},
        "rows":90,"schema":"agent-interface/known-postcondition-boundary-audit-v1",
        "scientific_decision":"PASS_DETERMINISTIC_POSTCONDITION_BOUNDARY_SCOPED","status":"PASS_AUDIT"
    }
    if artifact_audit != expected_hist: errors.append("historical_audit_payload")
    return {"status":"PASS_CURRENT_MAIN_ARTIFACT_RECONCILED_SCOPED" if not errors else "FAIL_RECONCILIATION",
            "errors":errors,"rows":len(rows),"unique_identities":len(set(seen)),"rich_agent_calls":counts}

def controls(rows,binding,audit_json):
    tests=[]
    def check(name,mut_rows=None,mut_binding=None,mut_audit=None):
        rr=rows if mut_rows is None else mut_rows
        bb=binding if mut_binding is None else mut_binding
        aa=audit_json if mut_audit is None else mut_audit
        res=audit(rr,bb,aa); tests.append({"name":name,"rejected":res["status"]!="PASS_CURRENT_MAIN_ARTIFACT_RECONCILED_SCOPED","errors":res["errors"][:5]})
    r=copy.deepcopy(rows); r.pop(); check("missing_row",r)
    r=copy.deepcopy(rows); r[-1]=copy.deepcopy(r[0]); check("duplicate_identity",r)
    r=copy.deepcopy(rows); x=next(x for x in r if x["scenario"]=="wrong_target"); x["verifier"]={"verdict":"PASS_POSTCONDITION","reason":"exact_typed_effect"}; check("forged_wrong_target_pass",r)
    r=copy.deepcopy(rows); x=next(x for x in r if x["scenario"]=="wrong_target"); x["evidence"]["target_observed"]=True; check("changed_target_observed",r)
    r=copy.deepcopy(rows); r[0]["rich_agent_calls"]=0; check("altered_rich_agent_calls",r)
    b=copy.deepcopy(binding); b["experiment_blob"]="0"*40; check("changed_source_binding",mut_binding=b)
    return tests

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--artifact-root",type=pathlib.Path,required=True); ap.add_argument("--binding",type=pathlib.Path,required=True); ap.add_argument("--out",type=pathlib.Path,required=True); a=ap.parse_args()
    rows=json.loads((a.artifact_root/"raw.json").read_text())
    hist=json.loads((a.artifact_root/"audit.json").read_text())
    binding=json.loads(a.binding.read_text())
    result=audit(rows,binding,hist)
    cs=controls(rows,binding,hist)
    result["corruption_controls"]=cs
    result["corruptions_rejected"]=sum(x["rejected"] for x in cs)
    result["artifact_raw_sha256"]=sha256(a.artifact_root/"raw.json")
    result["artifact_audit_sha256"]=sha256(a.artifact_root/"audit.json")
    if result["corruptions_rejected"] != len(cs): result["status"]="FAIL_RECONCILIATION"; result["errors"].append("corruption_control_accepted")
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result["status"]=="PASS_CURRENT_MAIN_ARTIFACT_RECONCILED_SCOPED" else 2)
if __name__=="__main__": main()
