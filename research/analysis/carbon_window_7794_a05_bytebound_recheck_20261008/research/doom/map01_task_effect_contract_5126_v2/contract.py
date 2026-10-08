"""V2 synthetic contract candidate; source-event IDs share one namespace."""


def _id(value):
    return type(value) is str and bool(value) and value == value.strip()


def classify(row):
    session, plan, act = (row.get(k) for k in ("session_id", "plan_id", "actuation_id"))
    p = row.get("physical") or {}
    down, up = p.get("down") or {}, p.get("up") or {}
    owner = p.get("owner_id")
    physical_ids = [down.get("source_event_id"), up.get("source_event_id")]
    times = [down.get("lower_ns"), down.get("upper_ns"), up.get("lower_ns"), up.get("upper_ns")]
    physical_ok = (
        all(_id(v) for v in (session, plan, act, owner)) and row.get("clock_axis_attested") is True
        and p.get("empty_release_verified") is True
        and all(_id(edge.get(k)) for edge in (down, up)
                for k in ("session_id", "plan_id", "actuation_id", "owner_id", "source_event_id", "key"))
        and len(set(physical_ids)) == 2
        and all(edge.get("session_id") == session and edge.get("plan_id") == plan
                and edge.get("actuation_id") == act and edge.get("owner_id") == owner for edge in (down, up))
        and down.get("key") == up.get("key") and all(type(t) is int for t in times)
        and 0 <= times[0] <= times[1] <= times[2] <= times[3]
    )
    states = []
    for f in row.get("state_feedback", []):
        if (f.get("session_id") == session and type(f.get("observed_ns")) is int and f["observed_ns"] >= 0
                and f.get("signal") in ("health", "ammo") and type(f.get("before")) is int
                and type(f.get("after")) is int):
            states.append({"observed_ns": f["observed_ns"], "signal": f["signal"], "before": f["before"],
                           "after": f["after"], "authority": False})
    events = row.get("task_effects", [])
    seen_source, seen_effect, accepted = set(physical_ids), set(), []
    duplicate_source = duplicate_effect = invalid = False
    for event in events:
        source_id, effect_id = event.get("source_event_id"), event.get("effect_id")
        duplicate_source |= _id(source_id) and source_id in seen_source
        duplicate_effect |= _id(effect_id) and effect_id in seen_effect
        valid = (
            physical_ok and _id(source_id) and _id(effect_id) and source_id not in seen_source
            and effect_id not in seen_effect
            and all(event.get(k) == value for k, value in (("session_id", session), ("plan_id", plan), ("actuation_id", act)))
            and event.get("scored") is True and event.get("scorer_independent") is True
            and event.get("controller_visible") is False
            and event.get("scorer_source") == "independent_progress_clock_v2"
            and event.get("kind") in ("KILL_COUNT_INCREASE", "DEATH_COUNT_INCREASE", "MAP_EXIT", "PROGRESS")
            and event.get("polarity") in ("useful", "harmful") and type(event.get("observed_ns")) is int
            and event["observed_ns"] >= down.get("upper_ns", 0)
        )
        if valid:
            accepted.append(event)
            seen_source.add(source_id)
            seen_effect.add(effect_id)
        else:
            invalid = True
    if duplicate_source:
        status, effect_id = "UNRESOLVED_DUPLICATE_SOURCE_EVENT", None
    elif duplicate_effect or len(accepted) > 1:
        status, effect_id = "UNRESOLVED_DUPLICATE_EFFECT", None
    elif len(accepted) == 1 and not invalid:
        status, effect_id = "TASK_EFFECT_SCOPED", accepted[0]["effect_id"]
    elif events:
        status, effect_id = "UNRESOLVED_UNBOUND_OR_INVALID_EFFECT", None
    else:
        status, effect_id = "UNRESOLVED_NO_TASK_EFFECT", None
    return {"physical_actuation": "PHYSICAL_ACTUATION_SCOPED" if physical_ok else "UNRESOLVED",
            "state_feedback": states, "task_effect": status, "effect_id": effect_id,
            "grants_input_authority": False, "grants_task_authority": False}
