"""Independent, deliberately separate reference classifier for #1839 tests."""


def oracle(record):
    session, plan, act = (record.get(k) for k in ("session_id", "plan_id", "actuation_id"))
    p = record.get("physical", {})
    d, u = p.get("down", {}), p.get("up", {})
    lineage = (session is not None and plan is not None and act is not None
               and record.get("clock_axis_attested") is True
               and p.get("owner_id") is not None and p.get("empty_release_verified") is True
               and all(x.get("session_id") == session and x.get("plan_id") == plan
                       and x.get("actuation_id") == act and x.get("owner_id") == p.get("owner_id")
                       for x in (d, u))
               and isinstance(d.get("key"), str) and d.get("key") == u.get("key")
               and all(type(x.get(k)) is int for x in (d, u) for k in ("lower_ns", "upper_ns"))
               and 0 <= d.get("lower_ns", -1) <= d.get("upper_ns", -1)
               <= u.get("lower_ns", -1) <= u.get("upper_ns", -1))
    phys = "PHYSICAL_ACTUATION_SCOPED" if lineage else "UNRESOLVED"
    feedback = []
    for f in record.get("state_feedback", []):
        if (f.get("session_id") == session and type(f.get("observed_ns")) is int
                and f["observed_ns"] >= 0 and f.get("signal") in ("health", "ammo")
                and type(f.get("before")) is int and type(f.get("after")) is int):
            feedback.append({"observed_ns": f["observed_ns"], "signal": f["signal"],
                             "before": f["before"], "after": f["after"], "authority": False})
    accepted = []
    invalid = False
    ids = set()
    for e in record.get("task_effects", []):
        eid = e.get("effect_id")
        valid = (lineage and isinstance(eid, str) and eid not in ids
                 and e.get("session_id") == session and e.get("plan_id") == plan
                 and e.get("actuation_id") == act and e.get("scored") is True
                 and e.get("scorer_independent") is True and e.get("controller_visible") is False
                 and e.get("scorer_source") == "independent_progress_clock_v2"
                 and e.get("kind") in ("KILL_COUNT_INCREASE", "DEATH_COUNT_INCREASE", "MAP_EXIT", "PROGRESS")
                 and e.get("polarity") in ("useful", "harmful")
                 and type(e.get("observed_ns")) is int
                 and e.get("observed_ns", -1) >= d.get("upper_ns", 0))
        if valid:
            ids.add(eid); accepted.append(eid)
        else:
            invalid = True
    if len(accepted) == 1 and not invalid:
        task, eid = "TASK_EFFECT_SCOPED", accepted[0]
    elif len(accepted) > 1:
        task, eid = "UNRESOLVED_DUPLICATE_EFFECT", None
    elif record.get("task_effects"):
        task, eid = "UNRESOLVED_UNBOUND_OR_INVALID_EFFECT", None
    else:
        task, eid = "UNRESOLVED_NO_TASK_EFFECT", None
    return {"physical_actuation": phys, "state_feedback": feedback, "task_effect": task,
            "effect_id": eid, "grants_input_authority": False, "grants_task_authority": False}
