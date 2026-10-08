from __future__ import annotations

VALID_ROLES = {"PHYSICAL_ACTUATION", "STATE_FEEDBACK", "TASK_EFFECT", "UNRESOLVED"}

def _nonblank(v):
    return isinstance(v, str) and bool(v.strip())

def classify(record: dict) -> dict:
    if not isinstance(record, dict):
        raise ValueError("record")
    kind = record.get("kind")
    authority = bool(record.get("input_authority", False) or record.get("semantic_authority", False))
    if authority:
        raise ValueError("authority_escalation")

    if kind == "physical_actuation":
        for k in ("plan_id", "actuation_id", "owner_id", "intent_token", "key"):
            if not _nonblank(record.get(k)):
                raise ValueError("bad_lineage")
        dl, dh = record.get("down_lo_ns"), record.get("down_hi_ns")
        ul, uh = record.get("up_lo_ns"), record.get("up_hi_ns")
        if not all(type(x) is int and x >= 0 for x in (dl, dh, ul, uh)) or not (dl <= dh <= ul <= uh):
            raise ValueError("bad_interval")
        return {"role":"PHYSICAL_ACTUATION", "plan_id":record["plan_id"], "actuation_id":record["actuation_id"],
                "physical_interval_ns":[dl, uh], "input_authority":False, "semantic_authority":False}

    if kind == "state_feedback":
        if not _nonblank(record.get("plan_id")) or record.get("signal") not in {"health","ammo"}:
            raise ValueError("bad_state_feedback")
        if type(record.get("t_ns")) is not int or record["t_ns"] < 0 or type(record.get("value")) is not int:
            raise ValueError("bad_state_feedback")
        return {"role":"STATE_FEEDBACK", "plan_id":record["plan_id"], "signal":record["signal"], "t_ns":record["t_ns"],
                "input_authority":False, "semantic_authority":False}

    if kind == "task_effect":
        for k in ("effect_id", "plan_id", "actuation_id", "scorer_source"):
            if not _nonblank(record.get(k)):
                raise ValueError("bad_effect_lineage")
        if record.get("scored") is not True:
            raise ValueError("unscored_effect")
        if record.get("effect_type") not in {"kill", "death", "map_exit", "progress"}:
            raise ValueError("bad_effect_type")
        if type(record.get("t_ns")) is not int or record["t_ns"] < 0:
            raise ValueError("bad_effect_time")
        if type(record.get("down_hi_ns")) is not int or record["down_hi_ns"] < 0:
            raise ValueError("bad_effect_time")
        if record["t_ns"] < record["down_hi_ns"]:
            return {"role":"UNRESOLVED", "reason":"EFFECT_BEFORE_CONFIRMED_DOWN", "plan_id":record["plan_id"],
                    "input_authority":False, "semantic_authority":False}
        if record.get("clock_relation") not in {"same_process_monotonic", "measured_axis"}:
            return {"role":"UNRESOLVED", "reason":"CLOCK_RELATION_UNPROVEN", "plan_id":record["plan_id"],
                    "input_authority":False, "semantic_authority":False}
        return {"role":"TASK_EFFECT", "effect_id":record["effect_id"], "plan_id":record["plan_id"],
                "actuation_id":record["actuation_id"], "effect_type":record["effect_type"], "t_ns":record["t_ns"],
                "scorer_source":record["scorer_source"], "input_authority":False, "semantic_authority":False}

    if kind in {"viewport_change", "program_terminal", "run_total", "hud_delta_unscored"}:
        pid = record.get("plan_id") if _nonblank(record.get("plan_id")) else None
        return {"role":"UNRESOLVED", "reason":"WEAK_EVIDENCE_NOT_TASK_EFFECT", "plan_id":pid,
                "input_authority":False, "semantic_authority":False}

    if kind == "no_task_effect":
        if not _nonblank(record.get("plan_id")):
            raise ValueError("bad_unresolved")
        return {"role":"UNRESOLVED", "reason":"NO_TASK_EFFECT", "plan_id":record["plan_id"],
                "input_authority":False, "semantic_authority":False}

    raise ValueError("unknown_kind")
