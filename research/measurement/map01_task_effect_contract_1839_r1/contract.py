from __future__ import annotations
from typing import Any

ROLES={"PHYSICAL_ACTUATION","STATE_FEEDBACK","TASK_EFFECT"}

def classify(events:list[dict[str,Any]])->dict[str,Any]:
    errors=[]; task=[]
    seen=set()
    for e in events:
        role=e.get("role")
        if role not in ROLES: errors.append("unknown_role"); continue
        lineage=(e.get("plan_id"),e.get("actuation_id"))
        if role=="PHYSICAL_ACTUATION":
            if not all(isinstance(e.get(k),str) and e[k] for k in ("plan_id","actuation_id")): errors.append("physical_lineage")
            if not isinstance(e.get("t_ns"),int): errors.append("physical_clock")
        elif role=="TASK_EFFECT":
            if e.get("scored") is not True or not isinstance(e.get("effect_id"),str) or not e["effect_id"]: errors.append("task_effect_score")
            if not all(isinstance(e.get(k),str) and e[k] for k in ("plan_id","actuation_id")): errors.append("task_effect_lineage")
            if not isinstance(e.get("t_ns"),int) or not isinstance(e.get("scorer_source"),str) or not e.get("scorer_source"): errors.append("task_effect_provenance")
            if e.get("effect_id") in seen: errors.append("duplicate_effect")
            seen.add(e.get("effect_id")); task.append(e)
    physical=[e for e in events if e.get("role")=="PHYSICAL_ACTUATION" and isinstance(e.get("t_ns"),int)]
    bound=[]
    for e in task:
        matches=[p for p in physical if (p.get("plan_id"),p.get("actuation_id"))==(e.get("plan_id"),e.get("actuation_id"))]
        if not matches: errors.append("task_effect_unbound"); continue
        if e["t_ns"] < min(p["t_ns"] for p in matches): errors.append("effect_before_actuation"); continue
        bound.append(e)
    return {"physical_count":len(physical),"task_effect_count":len(bound),"task_effects":bound,
            "errors":sorted(set(errors)),"task_effect_authority":False,
            "decision":"TASK_EFFECT_BOUND" if bound and not errors else ("UNRESOLVED_NO_TASK_EFFECT" if not bound and not errors else "REJECT")}

def oracle(events:list[dict[str,Any]])->dict[str,Any]:
    # Independent role/lineage reconstruction; never imports candidate helpers.
    valid_physical={(e.get("plan_id"),e.get("actuation_id")):e.get("t_ns") for e in events if e.get("role")=="PHYSICAL_ACTUATION" and isinstance(e.get("t_ns"),int)}
    effects=[e for e in events if e.get("role")=="TASK_EFFECT" and e.get("scored") is True]
    errors=[]
    for e in effects:
        key=(e.get("plan_id"),e.get("actuation_id"))
        if key not in valid_physical: errors.append("task_effect_unbound")
        elif not isinstance(e.get("effect_id"),str) or not e["effect_id"] or not isinstance(e.get("t_ns"),int) or e["t_ns"]<valid_physical[key]: errors.append("effect_invalid")
    return {"accepted":len(effects)-len(errors) if not errors else 0,"errors":sorted(set(errors))}
