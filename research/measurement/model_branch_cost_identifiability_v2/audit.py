#!/usr/bin/env python3
import hashlib, json, re
from pathlib import Path

HERE=Path(__file__).parent

def git_blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def audit(result_a=None,result_b=None,root=HERE):
    root=Path(root)
    sm=json.loads((root/"SOURCE_MAP.json").read_text())
    errors=[]
    source_rows=[]
    for name,meta in sm["sources"].items():
        data=(root/name).read_bytes()
        actual=git_blob(data)
        ok=actual==meta["expected_git_blob"]
        source_rows.append({"name":name,"expected":meta["expected_git_blob"],"actual":actual,"match":ok})
        if not ok:
            errors.append("source_blob:"+name)
    ledger=json.loads((root/"INPUT_LEDGER.json").read_text())
    cont=json.loads((root/"SOURCE_CONTINGENCY_AUDIT.json").read_text())
    p1=(root/"SOURCE_PROBE1.md").read_text()
    p2=(root/"SOURCE_PROBE2.md").read_text()
    for arm in ("grouped","ungrouped"):
        l=ledger["whole_run"][arm]
        c=cont[arm]
        for k in ("iterations","wall_seconds","model_seconds","contingencies_authored"):
            if l[k]!=c[k]:
                errors.append(f"whole_run:{arm}:{k}")
        for lk,ck in (("input_tokens","input_tokens"),("cached_input_tokens","cached_input_tokens"),("output_tokens","output_tokens"),("reasoning_output_tokens","reasoning_output_tokens")):
            if l[lk]!=c["usage"][ck]:
                errors.append(f"usage:{arm}:{lk}")
    if cont.get("status")!="passed" or not cont.get("protocol",{}).get("same_model_effort_task_environment_iterations_session_span"):
        errors.append("contingency_protocol")
    expected_probe1=("input_tokens=17477","cached_input_tokens=0","output_tokens=49","reasoning_output_tokens=0")
    if not all(x in p1 for x in expected_probe1):
        errors.append("probe1_usage")
    expected_probe2=("12567 input","1792 cached input","43 output tokens")
    if not all(x in p2 for x in expected_probe2):
        errors.append("probe2_usage")
    a=result_a if result_a is not None else json.loads((root/"RESULT_A.json").read_text())
    b=result_b if result_b is not None else json.loads((root/"RESULT_B.json").read_text())
    for label,r in (("A",a),("B",b)):
        if r.get("rows")!=24 or r.get("candidate_pairs")!=144:
            errors.append("counts:"+label)
        if r.get("causal_per_branch_estimate") is not None:
            errors.append("causal_laundering:"+label)
        if not r.get("all_pairs_fail_at_least_one_required_gate"):
            errors.append("unmatched_gate_claim:"+label)
    if a.get("admissible_pairs")!=b.get("admissible_pairs"):
        errors.append("analyzer_pair_disagreement")
    if a.get("same_image_pairs")!=b.get("same_image_pairs"):
        errors.append("analyzer_image_disagreement")
    if a.get("admissible_pair_count")!=b.get("admissible_pair_count"):
        errors.append("analyzer_count_disagreement")
    if not errors and a["admissible_pair_count"]==0:
        decision="PASS_RETAINED_MODEL_BRANCH_COST_NOT_IDENTIFIABLE_V2_SCOPED"
    elif not errors:
        decision="PASS_IDENTIFIABLE_V2_SCOPED"
    elif any(x.startswith("source_blob:") or x.startswith("whole_run:") or x.startswith("usage:") or x.startswith("probe") or x=="contingency_protocol" for x in errors):
        decision="HOLD_SOURCE_OR_PROVENANCE_GAP"
    else:
        decision="FAIL_ANALYZER_DISAGREEMENT"
    return {
        "task":sm["task"],
        "formal_invocations":1,
        "reruns":0,
        "decision":decision,
        "audit_pass":not errors,
        "errors":errors,
        "source_readback":source_rows,
        "rows":a.get("rows"),
        "candidate_pairs":a.get("candidate_pairs"),
        "same_image_pairs":a.get("same_image_pairs"),
        "admissible_pair_count":a.get("admissible_pair_count"),
        "admissible_pairs":a.get("admissible_pairs"),
        "provider_usage_endpoint_confirmed":not any(x.startswith("probe") for x in errors),
        "model_calls":0,
        "gui_actions":0,
        "task_input_actions":0,
        "causal_per_branch_estimate":None
    }

if __name__=="__main__":
    out=audit()
    (HERE/"AUDIT.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,indent=2,sort_keys=True))
    raise SystemExit(0 if out["audit_pass"] else 1)
