from collections import Counter
def iv(r):
    s=r.get("completion_status"); v=r.get("completion_ms")
    if s=="complete" and isinstance(v,int): return v,v
    b=r.get("completion_bounds_ms")
    if s=="censored_unknown" and isinstance(b,list) and len(b)==2 and all(isinstance(x,int) for x in b) and b[0]<=b[1]: return b[0],b[1]
    return None
def ac(c):
    rows=[]; lo=[]; hi=[]; op=0
    for p in c["pairs"]:
        d,g=iv(p["direct"]),iv(p["guarded"])
        if d is None or g is None: x=y=None; op+=1; rs="HOLD_OPEN_CENSOR_BOUND"
        else: x=g[0]-d[1]; y=g[1]-d[0]; lo.append(x); hi.append(y); rs="BOUNDED"
        rows.append({"task_id":p["task_id"],"phase":p["phase"],"direct_status":p["direct"]["completion_status"],"guarded_status":p["guarded"]["completion_status"],"delta_lower_ms":x,"delta_upper_ms":y,"row_status":rs})
    if op: s="HOLD_OPEN_CENSOR_BOUND"; ls=us=ml=mu=None
    else:
        ls,us=sum(lo),sum(hi); ml,mu=ls/len(c["pairs"]),us/len(c["pairs"])
        s="HOLD_ROBUSTNESS_FOR_THAT_CLAIM" if ml<0<mu else "DIRECTIONALLY_FASTER_ACROSS_BOUNDS" if mu<0 else "DIRECTIONALLY_SLOWER_ACROSS_BOUNDS" if ml>0 else "NO_DIRECTIONAL_SEPARATION"
    return {"estimand":"task_completion_latency","pair_rows":rows,"status":s,"n_pairs_total":len(c["pairs"]),"n_pairs_bounded":len(lo),"n_open_censor_pairs":op,"lower_sum_ms":ls,"upper_sum_ms":us,"mean_lower_ms":ml,"mean_upper_ms":mu}
def am(c,field,estimand):
    vals=[]; rows=[]; miss=0
    for p in c["pairs"]:
        x,y=p["direct"].get(field),p["guarded"].get(field); z=y-x if isinstance(x,int) and isinstance(y,int) else None
        if z is None: miss+=1
        else: vals.append(z)
        rows.append({"task_id":p["task_id"],"delta":z})
    return {"estimand":estimand,"n_pairs_total":len(c["pairs"]),"n_pairs_observed":len(vals),"n_pairs_missing":miss,"pair_rows":rows,"status":"HOLD_MISSING_DATA" if miss else "METHOD_ONLY","delta_sum":None if miss else sum(vals),"mean_delta":None if miss else sum(vals)/len(vals)}
def af(c,field):
    vals=[]; rows=[]; miss=0
    for p in c["pairs"]:
        a,b=p["direct"],p["guarded"]
        valid=a.get("effect_status")=="PASS_VERIFIED" and b.get("effect_status")=="PASS_VERIFIED" and all(isinstance(r.get(field),int) and isinstance(r.get("first_verified_effect_ms"),int) for r in (a,b))
        z=(b["first_verified_effect_ms"]-b[field])-(a["first_verified_effect_ms"]-a[field]) if valid else None
        if z is None: miss+=1
        else: vals.append(z)
        rows.append({"task_id":p["task_id"],"delta_ms":z})
    return {"estimand":"capture_to_verified_effect" if field=="image_capture_ms" else "delivery_to_verified_effect","start_field":field,"end_field":"first_verified_effect_ms","n_pairs_total":len(c["pairs"]),"n_pairs_observed":len(vals),"n_pairs_missing_or_unverified":miss,"pair_rows":rows,"status":"HOLD_MISSING_DATA" if miss else "METHOD_ONLY","delta_sum_ms":None if miss else sum(vals),"mean_delta_ms":None if miss else sum(vals)/len(vals)}
def aq(c):
    rr=[p[a] for p in c["pairs"] for a in ("direct","guarded")]; n=sum(r.get("collateral_errors",0) for r in rr); good=all(r.get("effect_status")=="PASS_VERIFIED" for r in rr)
    return {"collateral_error_count":n,"all_effects_independently_verified":good,"safety_gate":"FAIL_COLLATERAL_ERROR" if n else "HOLD_EFFECT_NOT_VERIFIED" if not good else "PASS_FIXTURE_ONLY","eligible_for_future_primary_route_analysis":not n and good and all(r.get("completion_status")=="complete" for r in rr)}
def expected(c):
    return {"cohort_id":c["id"],"phase_pair_counts":dict(sorted(Counter(p["phase"] for p in c["pairs"]).items())),"primary_completion":ac(c),"quality":aq(c),"different_estimands":{"model_active_wait":am(c,"model_active_ms","model_active_wait"),"human_residual_work":am(c,"human_residual_ms","human_residual_work"),"safe_termination":am(c,"safe_termination_ms","time_to_typed_safe_termination"),"token_usage":am(c,"tokens","provider_token_usage"),"capture_to_effect":af(c,"image_capture_ms"),"delivery_to_effect":af(c,"image_delivery_ms")}}
def audit(raw,f):
    err=[]
    if raw.get("schema")!="ai-route-multiverse-raw-v1": err.append("schema")
    if raw.get("allocation")!=f.get("allocation"): err.append("allocation")
    if raw.get("registry")!=f.get("registry"): err.append("registry")
    ex=[expected(c) for c in f["cohorts"]]
    if raw.get("analyses")!=ex: err.append("independent_replay_mismatch")
    got=raw.get("analyses",[])
    return {"status":"PASS_METHOD_SCOPED" if not err else "FAIL_RAW_AUDIT","errors":err,"cohorts_expected":len(ex),"cohorts_matched":sum(1 for x,y in zip(got,ex) if x==y),"scope":"raw-only synthetic accounting"}
