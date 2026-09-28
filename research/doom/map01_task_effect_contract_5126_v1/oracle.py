"""Structurally separate reference implementation for the strict lineage gate."""


def _id(value):
    return isinstance(value, str) and len(value) > 0 and value.strip() == value


def oracle(record):
    session = record.get("session_id")
    plan = record.get("plan_id")
    act = record.get("actuation_id")
    p = record.get("physical") or {}
    down = p.get("down") or {}
    up = p.get("up") or {}
    owner = p.get("owner_id")
    edge_ids = [down.get("source_event_id"), up.get("source_event_id")]
    times = [down.get("lower_ns"), down.get("upper_ns"), up.get("lower_ns"), up.get("upper_ns")]
    lineage_ok = (
        all(_id(x) for x in (session, plan, act, owner))
        and record.get("clock_axis_attested") is True and p.get("empty_release_verified") is True
        and all(_id(edge.get(k)) for edge in (down, up)
                for k in ("session_id", "plan_id", "actuation_id", "owner_id", "source_event_id", "key"))
        and edge_ids[0] != edge_ids[1]
        and all(edge.get("session_id") == session and edge.get("plan_id") == plan
                and edge.get("actuation_id") == act and edge.get("owner_id") == owner
                for edge in (down, up))
        and down.get("key") == up.get("key") and all(type(t) is int for t in times)
        and 0 <= times[0] <= times[1] <= times[2] <= times[3]
    )
    feedback = [{"observed_ns": f["observed_ns"], "signal": f["signal"], "before": f["before"],
                 "after": f["after"], "authority": False}
                for f in record.get("state_feedback", [])
                if f.get("session_id") == session and type(f.get("observed_ns")) is int and f["observed_ns"] >= 0
                and f.get("signal") in ("health", "ammo") and type(f.get("before")) is int
                and type(f.get("after")) is int]
    accepted, used_effect_ids, used_sources, invalid, duplicate = [], set(), set(), False, False
    for event in record.get("task_effects", []):
        eid, sid = event.get("effect_id"), event.get("source_event_id")
        duplicate = duplicate or (_id(eid) and eid in used_effect_ids) or (_id(sid) and sid in used_sources)
        valid = (
            lineage_ok and _id(eid) and _id(sid) and eid not in used_effect_ids and sid not in used_sources
            and event.get("session_id") == session and event.get("plan_id") == plan
            and event.get("actuation_id") == act and event.get("scored") is True
            and event.get("scorer_independent") is True and event.get("controller_visible") is False
            and event.get("scorer_source") == "independent_progress_clock_v2"
            and event.get("kind") in ("KILL_COUNT_INCREASE", "DEATH_COUNT_INCREASE", "MAP_EXIT", "PROGRESS")
            and event.get("polarity") in ("useful", "harmful") and type(event.get("observed_ns")) is int
            and event.get("observed_ns", -1) >= down.get("upper_ns", 0)
        )
        if valid:
            accepted.append(event)
            used_effect_ids.add(eid)
            used_sources.add(sid)
        else:
            invalid = True
    if len(accepted) == 1 and not invalid:
        task, effect_id = "TASK_EFFECT_SCOPED", accepted[0]["effect_id"]
    elif duplicate or len(accepted) > 1:
        task, effect_id = "UNRESOLVED_DUPLICATE_EFFECT", None
    elif record.get("task_effects"):
        task, effect_id = "UNRESOLVED_UNBOUND_OR_INVALID_EFFECT", None
    else:
        task, effect_id = "UNRESOLVED_NO_TASK_EFFECT", None
    return {"physical_actuation": "PHYSICAL_ACTUATION_SCOPED" if lineage_ok else "UNRESOLVED",
            "state_feedback": feedback, "task_effect": task, "effect_id": effect_id,
            "grants_input_authority": False, "grants_task_authority": False}
