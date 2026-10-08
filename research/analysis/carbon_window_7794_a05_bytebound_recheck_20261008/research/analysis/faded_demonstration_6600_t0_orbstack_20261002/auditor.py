#!/usr/bin/env python3
"""Independent oracle-only audit of #6600 T0 raw candidate output."""
import hashlib
import json
import pathlib
import sys


def main():
    fixture_path,oracle_path,raw_path,out_path=map(pathlib.Path,sys.argv[1:5])
    fixture=json.loads(fixture_path.read_text())
    truth=json.loads(oracle_path.read_text())["truth"]
    raw_bytes=raw_path.read_bytes()
    raw=json.loads(raw_bytes)
    rows={r.get("case_id"):r for r in raw.get("rows",[])}
    errors=[]
    ids={c["id"] for c in fixture["cases"]}
    if len(rows)!=9 or set(rows)!=ids or set(truth)!=ids: errors.append("CASE_SET")
    for c in fixture["cases"]:
        r=rows.get(c["id"],{})
        t=truth[c["id"]]
        fresh=c["source_generation"]==c["current_generation"]==c["receipt"]["source_generation"]
        target_ok=c["target_unambiguous"] and c["task_target"]!="UNKNOWN" and c["receipt"]["target"]==c["task_target"]
        expected_effect=c["receipt"]["effect_status"]=="verified" and target_ok and fresh
        expected_safe=expected_effect and c["receipt"]["released"] and c["reversible"]
        expected_offer=expected_safe and c["practice_opt_in"]
        expected={"case_id":c["id"],"effect_for_task":expected_effect,"safe_completion":expected_safe,"teaching_step_offered":expected_offer,"statement":"VERIFIED_OBSERVED_EFFECT" if expected_effect else "UNKNOWN_NOT_DEMONSTRATED","coordinate_reused":False,"fresh_target_rebind_required":not fresh,"skip_available":True,"stop_available":True,"action_authority_granted":False}
        if r!=expected: errors.append("RECONSTRUCTION:"+c["id"])
        if expected_effect!=t["effect_for_task"]: errors.append("FALSE_EFFECT_CLAIM:"+c["id"])
        if expected_safe!=t["safe_completion"]: errors.append("SAFETY_COMPLETION:"+c["id"])
        if expected_offer!=t["teaching_offer_allowed"]: errors.append("TEACHING_ELIGIBILITY:"+c["id"])
        if not r.get("skip_available") or not r.get("stop_available"): errors.append("NO_EXIT:"+c["id"])
        if r.get("action_authority_granted"): errors.append("AUTHORITY_LAUNDERING:"+c["id"])
    report={"status":"PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD","errors":errors,"rows":len(rows),"eligible_steps":sum(bool(r.get("teaching_step_offered")) for r in rows.values()),"verified_effect_claims":sum(bool(r.get("effect_for_task")) for r in rows.values()),"scope":"authored finite method fixture only; no participant, GUI, model, or input" ,"raw_sha256":hashlib.sha256(raw_bytes).hexdigest()}
    out_path.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"status":report["status"],"rows":len(rows),"errors":len(errors)}))
    return 0 if not errors else 2


if __name__=="__main__": raise SystemExit(main())
