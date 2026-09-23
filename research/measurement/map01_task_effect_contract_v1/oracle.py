from __future__ import annotations

def nb(x): return isinstance(x,str) and x.strip() != ""

def classify_oracle(r):
    if not isinstance(r,dict): raise ValueError("record")
    if r.get("input_authority") is True or r.get("semantic_authority") is True: raise ValueError("authority_escalation")
    k=r.get("kind")
    if k=="physical_actuation":
        if any(not nb(r.get(x)) for x in ["plan_id","actuation_id","owner_id","intent_token","key"]): raise ValueError("bad_lineage")
        xs=[r.get(x) for x in ["down_lo_ns","down_hi_ns","up_lo_ns","up_hi_ns"]]
        if any(type(x) is not int or x<0 for x in xs) or not (xs[0]<=xs[1]<=xs[2]<=xs[3]): raise ValueError("bad_interval")
        return {"role":"PHYSICAL_ACTUATION","plan_id":r["plan_id"],"actuation_id":r["actuation_id"],"physical_interval_ns":[xs[0],xs[3]],"input_authority":False,"semantic_authority":False}
    if k=="state_feedback":
        if not nb(r.get("plan_id")) or r.get("signal") not in ["health","ammo"] or type(r.get("t_ns")) is not int or r["t_ns"]<0 or type(r.get("value")) is not int: raise ValueError("bad_state_feedback")
        return {"role":"STATE_FEEDBACK","plan_id":r["plan_id"],"signal":r["signal"],"t_ns":r["t_ns"],"input_authority":False,"semantic_authority":False}
    if k=="task_effect":
        if any(not nb(r.get(x)) for x in ["effect_id","plan_id","actuation_id","scorer_source"]): raise ValueError("bad_effect_lineage")
        if r.get("scored") is not True: raise ValueError("unscored_effect")
        if r.get("effect_type") not in ["kill","death","map_exit","progress"]: raise ValueError("bad_effect_type")
        if type(r.get("t_ns")) is not int or r["t_ns"]<0 or type(r.get("down_hi_ns")) is not int or r["down_hi_ns"]<0: raise ValueError("bad_effect_time")
        if r["t_ns"] < r["down_hi_ns"]: return {"role":"UNRESOLVED","reason":"EFFECT_BEFORE_CONFIRMED_DOWN","plan_id":r["plan_id"],"input_authority":False,"semantic_authority":False}
        if r.get("clock_relation") not in ["same_process_monotonic","measured_axis"]: return {"role":"UNRESOLVED","reason":"CLOCK_RELATION_UNPROVEN","plan_id":r["plan_id"],"input_authority":False,"semantic_authority":False}
        return {"role":"TASK_EFFECT","effect_id":r["effect_id"],"plan_id":r["plan_id"],"actuation_id":r["actuation_id"],"effect_type":r["effect_type"],"t_ns":r["t_ns"],"scorer_source":r["scorer_source"],"input_authority":False,"semantic_authority":False}
    if k in ["viewport_change","program_terminal","run_total","hud_delta_unscored"]:
        return {"role":"UNRESOLVED","reason":"WEAK_EVIDENCE_NOT_TASK_EFFECT","plan_id":r.get("plan_id") if nb(r.get("plan_id")) else None,"input_authority":False,"semantic_authority":False}
    if k=="no_task_effect":
        if not nb(r.get("plan_id")): raise ValueError("bad_unresolved")
        return {"role":"UNRESOLVED","reason":"NO_TASK_EFFECT","plan_id":r["plan_id"],"input_authority":False,"semantic_authority":False}
    raise ValueError("unknown_kind")
