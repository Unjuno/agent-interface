"""Strict candidate for synthetic Issue #5126 task-effect lineage."""


def canonical(value):
    return type(value) is str and bool(value) and value == value.strip()


def classify(row):
    session, plan, act = (row.get(k) for k in ("session_id", "plan_id", "actuation_id"))
    physical = row.get("physical") or {}
    down, up = physical.get("down") or {}, physical.get("up") or {}
    owner = physical.get("owner_id")
    physical_ok = (
        all(canonical(v) for v in (session, plan, act, owner))
        and row.get("clock_axis_attested") is True
        and physical.get("empty_release_verified") is True
        and all(canonical(edge.get(k)) for edge in (down, up)
                for k in ("session_id", "plan_id", "actuation_id", "owner_id", "source_event_id", "key"))
        and down.get("source_event_id") != up.get("source_event_id")
        and all(edge.get("session_id") == session and edge.get("plan_id") == plan
                and edge.get("actuation_id") == act and edge.get("owner_id") == owner
                for edge in (down, up))
        and down.get("key") == up.get("key")
        and all(type(edge.get(k)) is int for edge in (down, up) for k in ("lower_ns", "upper_ns"))
        and 0 <= down.get("lower_ns", -1) <= down.get("upper_ns", -1)
        <= up.get("lower_ns", -1) <= up.get("upper_ns", -1)
    )
    states = []
    for item in row.get("state_feedback", []):
        if (item.get("session_id") == session and type(item.get("observed_ns")) is int
                and item["observed_ns"] >= 0 and item.get("signal") in {"health", "ammo"}
                and type(item.get("before")) is int and type(item.get("after")) is int):
            states.append({"observed_ns": item["observed_ns"], "signal": item["signal"],
                           "before": item["before"], "after": item["after"], "authority": False})
    effects, accepted, seen_source, seen_effect = row.get("task_effects", []), [], set(), set()
    invalid, duplicate = False, False
    for effect in effects:
        source_id, effect_id = effect.get("source_event_id"), effect.get("effect_id")
        duplicate = duplicate or (canonical(source_id) and source_id in seen_source) or (canonical(effect_id) and effect_id in seen_effect)
        valid = (
            physical_ok and canonical(source_id) and canonical(effect_id)
            and source_id not in seen_source and effect_id not in seen_effect
            and all(effect.get(k) == v for k, v in (("session_id", session), ("plan_id", plan), ("actuation_id", act)))
            and effect.get("scored") is True and effect.get("scorer_independent") is True
            and effect.get("controller_visible") is False
            and effect.get("scorer_source") == "independent_progress_clock_v2"
            and effect.get("kind") in {"KILL_COUNT_INCREASE", "DEATH_COUNT_INCREASE", "MAP_EXIT", "PROGRESS"}
            and effect.get("polarity") in {"useful", "harmful"}
            and type(effect.get("observed_ns")) is int
            and effect.get("observed_ns", -1) >= down.get("upper_ns", 0)
        )
        if valid:
            accepted.append(effect)
            seen_source.add(source_id)
            seen_effect.add(effect_id)
        else:
            invalid = True
    if len(accepted) == 1 and not invalid:
        task, eid = "TASK_EFFECT_SCOPED", accepted[0]["effect_id"]
    elif duplicate or len(accepted) > 1:
        task, eid = "UNRESOLVED_DUPLICATE_EFFECT", None
    elif effects:
        task, eid = "UNRESOLVED_UNBOUND_OR_INVALID_EFFECT", None
    else:
        task, eid = "UNRESOLVED_NO_TASK_EFFECT", None
    return {"physical_actuation": "PHYSICAL_ACTUATION_SCOPED" if physical_ok else "UNRESOLVED",
            "state_feedback": states, "task_effect": task, "effect_id": eid,
            "grants_input_authority": False, "grants_task_authority": False}
