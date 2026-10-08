from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def contains_coord_keys(v):
    if isinstance(v,dict):
        for k,x in v.items():
            if k in {"x","y","point","field_point","submit_point","coordinates"}: return True
            if contains_coord_keys(x): return True
    if isinstance(v,list): return any(contains_coord_keys(x) for x in v)
    return False

def audit_data(fx, rows, rr):
    errors=[]
    if len(rows)!=12: errors.append("row_count")
    ga=rr.get("guarded_artifact",{})
    if contains_coord_keys(ga): errors.append("candidate_coordinate_leak")
    if fx["compile_example"]["token"] in repr(ga): errors.append("candidate_fixed_token")
    if ga.get("parameters") != ["token","field_handle","submit_handle"]: errors.append("candidate_parameters")
    by={(r["state_id"],r["artifact"]):r for r in rows}
    if len(by)!=12: errors.append("duplicate_rows")
    expected_states={s["state_id"]:s for s in fx["states"]}
    for sid,st in expected_states.items():
        c=by.get((sid,"GUARDED_TYPED_MACRO")); b=by.get((sid,"LITERAL_REPLAY"))
        if not c or not b: errors.append(f"missing_{sid}"); continue
        if c["decision"]!=st["evaluator"]["expected_candidate"]: errors.append(f"candidate_decision_{sid}")
        if sid=="task4_pre_repair":
            if c["pointer_events"]!=0: errors.append("stale_candidate_pointer")
            if b["decision"]!="ACTION" or not b["historical_coordinates_emitted"]: errors.append("baseline_pre_discriminator")
        elif st["evaluator"]["expected_candidate"]=="ACTION":
            if not c["matches_current_target"]: errors.append(f"candidate_target_{sid}")
        if sid in {"task4_post_repair","task5_b","task6_b"}:
            if b["decision"]!="ACTION" or b["matches_current_target"] or not b["historical_coordinates_emitted"]: errors.append(f"baseline_b_discriminator_{sid}")
        if sid in {"task2_a","task3_a"} and not b["matches_current_target"]: errors.append(f"baseline_a_control_{sid}")
        if c.get("historical_coordinates_emitted"): errors.append(f"candidate_historical_{sid}")
    # Same context must hold across A/B; otherwise literal baseline discriminator is not isolated.
    ctxs={json.dumps(s["context"],sort_keys=True) for s in fx["states"]}
    if len(ctxs)!=1: errors.append("context_not_held_fixed")
    decision="PASS_CHROMIUM_GUARDED_MACRO_COMPILATION_SCOPED" if not errors else "FAIL_AUDIT"
    return {"decision":decision,"errors":errors,"rows":len(rows)}

def main():
    fx=json.loads((ROOT/"fixture.json").read_text()); rows=json.loads((ROOT/"results/formal_rows.json").read_text()); rr=json.loads((ROOT/"results/RUNNER_RESULT.json").read_text())
    out=audit_data(fx,rows,rr); (ROOT/"results/AUDIT.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); print(json.dumps(out,sort_keys=True))
if __name__=="__main__": main()
