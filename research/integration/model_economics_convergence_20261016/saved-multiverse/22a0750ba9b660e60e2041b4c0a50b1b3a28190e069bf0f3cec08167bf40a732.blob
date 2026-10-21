from collections import Counter
def interval(r):
    if r.get("completion_status")=="complete" and isinstance(r.get("completion_ms"),int):
        return r["completion_ms"],r["completion_ms"]
    if r.get("completion_status")=="censored_unknown":
        b=r.get("completion_bounds_ms")
        if isinstance(b,list) and len(b)==2 and isinstance(b[0],int) and isinstance(b[1],int) and b[0]<=b[1]: return b[0],b[1]
    return None
def completion(c):
    rows=[]; lows=[]; highs=[]; opened=0
    for p in c["pairs"]:
        a,b=interval(p["direct"]),interval(p["guarded"])
        if a is None or b is None:
            lo=hi=None; opened+=1; status="HOLD_OPEN_CENSOR_BOUND"
        else:
            lo=b[0]-a[1]; hi=b[1]-a[0]; lows.append(lo); highs.append(hi); status="BOUNDED"
        rows.append({"task_id":p["task_id"],"phase":p["phase"],"direct_status":p["direct"]["completion_status"],"guarded_status":p["guarded"]["completion_status"],"delta_lower_ms":lo,"delta_upper_ms":hi,"row_status":status})
    if opened:
        s="HOLD_OPEN_CENSOR_BOUND"; ls=us=ml=mu=None
    else:
        ls,us=sum(lows),sum(highs); ml,mu=ls/len(c["pairs"]),us/len(c["pairs"])
        s=("HOLD_ROBUSTNESS_FOR_THAT_CLAIM" if ml<0<mu else "DIRECTIONALLY_FASTER_ACROSS_BOUNDS" if mu<0 else "DIRECTIONALLY_SLOWER_ACROSS_BOUNDS" if ml>0 else "NO_DIRECTIONAL_SEPARATION")
    return {"estimand":"task_completion_latency","pair_rows":rows,"status":s,"n_pairs_total":len(c["pairs"]),"n_pairs_bounded":len(lows),"n_open_censor_pairs":opened,"lower_sum_ms":ls,"upper_sum_ms":us,"mean_lower_ms":ml,"mean_upper_ms":mu}
def metric(c,field,estimand):
    vals=[]; rows=[]; missing=0
    for p in c["pairs"]:
        a,b=p["direct"].get(field),p["guarded"].get(field)
        d=b-a if isinstance(a,int) and isinstance(b,int) else None
        if d is None: missing+=1
        else: vals.append(d)
        rows.append({"task_id":p["task_id"],"delta":d})
    return {"estimand":estimand,"n_pairs_total":len(c["pairs"]),"n_pairs_observed":len(vals),"n_pairs_missing":missing,"pair_rows":rows,"status":"HOLD_MISSING_DATA" if missing else "METHOD_ONLY","delta_sum":None if missing else sum(vals),"mean_delta":None if missing else sum(vals)/len(vals)}
def feedback(c,field):
    vals=[]; rows=[]; missing=0
    for p in c["pairs"]:
        a,b=p["direct"],p["guarded"]
        ok=a.get("effect_status")==b.get("effect_status")=="PASS_VERIFIED" and all(isinstance(r.get(field),int) and isinstance(r.get("first_verified_effect_ms"),int) for r in (a,b))
        d=((b["first_verified_effect_ms"]-b[field])-(a["first_verified_effect_ms"]-a[field])) if ok else None
        if d is None: missing+=1
        else: vals.append(d)
        rows.append({"task_id":p["task_id"],"delta_ms":d})
    return {"estimand":"capture_to_verified_effect" if field=="image_capture_ms" else "delivery_to_verified_effect","start_field":field,"end_field":"first_verified_effect_ms","n_pairs_total":len(c["pairs"]),"n_pairs_observed":len(vals),"n_pairs_missing_or_unverified":missing,"pair_rows":rows,"status":"HOLD_MISSING_DATA" if missing else "METHOD_ONLY","delta_sum_ms":None if missing else sum(vals),"mean_delta_ms":None if missing else sum(vals)/len(vals)}
def quality(c):
    rr=[p[k] for p in c["pairs"] for k in ("direct","guarded")]
    n=sum(r.get("collateral_errors",0) for r in rr); effects=all(r.get("effect_status")=="PASS_VERIFIED" for r in rr)
    gate="FAIL_COLLATERAL_ERROR" if n else "HOLD_EFFECT_NOT_VERIFIED" if not effects else "PASS_FIXTURE_ONLY"
    eligible=not n and effects and all(r.get("completion_status")=="complete" for r in rr)
    return {"collateral_error_count":n,"all_effects_independently_verified":effects,"safety_gate":gate,"eligible_for_future_primary_route_analysis":eligible}
def run(f):
    out=[]
    for c in f["cohorts"]:
        sec={"model_active_wait":metric(c,"model_active_ms","model_active_wait"),"human_residual_work":metric(c,"human_residual_ms","human_residual_work"),"safe_termination":metric(c,"safe_termination_ms","time_to_typed_safe_termination"),"token_usage":metric(c,"tokens","provider_token_usage"),"capture_to_effect":feedback(c,"image_capture_ms"),"delivery_to_effect":feedback(c,"image_delivery_ms")}
        out.append({"cohort_id":c["id"],"phase_pair_counts":dict(sorted(Counter(p["phase"] for p in c["pairs"]).items())),"primary_completion":completion(c),"quality":quality(c),"different_estimands":sec})
    return {"schema":"ai-route-multiverse-raw-v1","allocation":f["allocation"],"registry":f["registry"],"analyses":out,"scope":"finite synthetic accounting method only; no route/product result"}
