import json

EXPECTED = {
    "unique_positive":"BOUND_TASK_EFFECT",
    "missing_source":"HOLD_SOURCE_IDENTITY_INSUFFICIENT",
    "wrong_session":"HOLD_SOURCE_IDENTITY_INSUFFICIENT",
    "wrong_plan":"HOLD_SOURCE_IDENTITY_INSUFFICIENT",
    "wrong_actuation":"HOLD_SOURCE_IDENTITY_INSUFFICIENT",
    "wrong_source_event":"HOLD_SOURCE_IDENTITY_INSUFFICIENT",
    "clock_mismatch":"HOLD_CLOCK_DOMAIN_UNCOMPARABLE",
    "score_before_down":"HOLD_CLOCK_DOMAIN_UNCOMPARABLE",
    "duplicate_score":"FAIL_AMBIGUOUS_EVENT_BINDING",
    "no_input_positive":"FAIL_AUTHORITY_OR_ATTRIBUTION_LAUNDERING",
    "unsupported_event":"HOLD_UNSUPPORTED_EVENT_KIND",
    "unsupported_effect":"HOLD_UNSUPPORTED_EFFECT_KIND",
    "missing_up":"HOLD_PHYSICAL_EDGE_INCOMPLETE",
    "nonneutral_terminal":"HOLD_TERMINAL_NOT_NEUTRAL",
}
def independent_disposition(r):
    if r.get("duplicate_scorer_events",0)>1: return "FAIL_AMBIGUOUS_EVENT_BINDING"
    if r.get("mode")=="NO_INPUT" and r.get("scorer_event_id") is not None: return "FAIL_AUTHORITY_OR_ATTRIBUTION_LAUNDERING"
    if r.get("scorer_event_id") is not None and r.get("event_kind")!="TASK_EFFECT": return "HOLD_UNSUPPORTED_EVENT_KIND"
    if r.get("scorer_event_id") is not None and r.get("scorer_effect_kind") not in ("KILL_COUNT_INCREASE","MAP_EXIT"): return "HOLD_UNSUPPORTED_EFFECT_KIND"
    if not r.get("physical_down") or not r.get("physical_up"): return "HOLD_PHYSICAL_EDGE_INCOMPLETE"
    if not r.get("terminal_neutral"): return "HOLD_TERMINAL_NOT_NEUTRAL"
    required=("session_id","plan_id","actuation_id","source_event_id","scorer_event_id","scorer_session_id","scorer_plan_id","scorer_actuation_id","scorer_source_event_id","clock_domain","scorer_clock_domain","down_ns","terminal_ns","scorer_monotonic_ns")
    if any(r.get(k) in (None,"") for k in required): return "HOLD_SOURCE_IDENTITY_INSUFFICIENT"
    pairs=(("session_id","scorer_session_id"),("plan_id","scorer_plan_id"),("actuation_id","scorer_actuation_id"),("source_event_id","scorer_source_event_id"))
    if any(r[a]!=r[b] for a,b in pairs): return "HOLD_SOURCE_IDENTITY_INSUFFICIENT"
    if r["clock_domain"]!=r["scorer_clock_domain"] or not r["down_ns"]<r["scorer_monotonic_ns"]<r["terminal_ns"]: return "HOLD_CLOCK_DOMAIN_UNCOMPARABLE"
    if r.get("scorer_authority") is not False: return "FAIL_AUTHORITY_OR_ATTRIBUTION_LAUNDERING"
    return "BOUND_TASK_EFFECT"
def audit(raw):
    errors=[]
    if raw.get("schema")!="task-effect-receipt-boundary-t0-raw-v1": errors.append("schema")
    rows=raw.get("rows",[])
    ids=[x.get("case_id") for x in rows]
    if len(rows)!=len(EXPECTED): errors.append("denominator")
    if len(ids)!=len(set(ids)) or set(ids)!=set(EXPECTED): errors.append("case_inventory")
    for item in rows:
        cid=item.get("case_id")
        if cid not in EXPECTED: continue
        independent=independent_disposition(item.get("input",{}))
        if EXPECTED[cid]!=independent: errors.append("frozen_case_semantics:"+cid)
        if item.get("expected")!=independent or item.get("observed")!=independent: errors.append("verdict:"+cid)
    return {"schema":"task-effect-receipt-boundary-independent-audit-v1","errors":errors,"passed":not errors,"rows":len(rows)}
def corruption_controls(raw):
    mutations=[]
    x=json.loads(json.dumps(raw)); x["rows"].pop(); mutations.append(("drop_case",x))
    x=json.loads(json.dumps(raw)); x["rows"][0]["observed"]="HOLD"; mutations.append(("change_verdict",x))
    x=json.loads(json.dumps(raw)); x["rows"][0]["input"]["scorer_plan_id"]="wrong"; mutations.append(("wrong_plan",x))
    x=json.loads(json.dumps(raw)); x["rows"][0]["input"]["scorer_authority"]=True; mutations.append(("authority",x))
    x=json.loads(json.dumps(raw)); x["rows"][0]["input"]["scorer_monotonic_ns"]=99; mutations.append(("time",x))
    x=json.loads(json.dumps(raw)); x["rows"][0]["input"]["scorer_effect_kind"]="HUD_CHANGE"; mutations.append(("effect_kind",x))
    x=json.loads(json.dumps(raw)); x["rows"][0]["input"]["physical_up"]=False; mutations.append(("physical_edge",x))
    return [{"name":name,"rejected":not audit(changed)["passed"]} for name,changed in mutations]
if __name__=="__main__":
    import sys
    raw=json.load(open(sys.argv[1],encoding="utf-8"))
    print(json.dumps({"audit":audit(raw),"corruption_controls":corruption_controls(raw)},sort_keys=True))
