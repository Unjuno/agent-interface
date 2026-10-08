"""Independent v2 reference model with cross-plane source identity check."""


def oracle(record):
    sid, pid, aid = (record.get(k) for k in ("session_id", "plan_id", "actuation_id"))
    physical = record.get("physical") or {}
    owner = physical.get("owner_id")
    edges = [physical.get("down") or {}, physical.get("up") or {}]
    physical_refs = [edge.get("source_event_id") for edge in edges]

    def valid_id(item):
        return isinstance(item, str) and item != "" and item.strip() == item

    edge_times = [[edge.get("lower_ns"), edge.get("upper_ns")] for edge in edges]
    edge_ok = (
        all(valid_id(item) for item in (sid, pid, aid, owner, *physical_refs))
        and physical_refs[0] != physical_refs[1]
        and record.get("clock_axis_attested") is True and physical.get("empty_release_verified") is True
        and all(valid_id(edge.get(key)) for edge in edges
                for key in ("session_id", "plan_id", "actuation_id", "owner_id", "key"))
        and all(edge.get("session_id") == sid and edge.get("plan_id") == pid
                and edge.get("actuation_id") == aid and edge.get("owner_id") == owner for edge in edges)
        and edges[0].get("key") == edges[1].get("key")
        and all(type(value) is int for pair in edge_times for value in pair)
        and 0 <= edge_times[0][0] <= edge_times[0][1] <= edge_times[1][0] <= edge_times[1][1]
    )
    state = []
    for obs in record.get("state_feedback", []):
        valid_obs = (obs.get("session_id") == sid and type(obs.get("observed_ns")) is int
                     and obs["observed_ns"] >= 0 and obs.get("signal") in {"health", "ammo"}
                     and type(obs.get("before")) is int and type(obs.get("after")) is int)
        if valid_obs:
            state.append({"observed_ns": obs["observed_ns"], "signal": obs["signal"],
                          "before": obs["before"], "after": obs["after"], "authority": False})

    source_universe = set(physical_refs)
    effect_ids, good, bad_source, bad_effect, rejected = set(), [], False, False, False
    for scored in record.get("task_effects", []):
        ref = scored.get("source_event_id")
        key = scored.get("effect_id")
        source_conflict = valid_id(ref) and ref in source_universe
        effect_conflict = valid_id(key) and key in effect_ids
        bad_source = bad_source or source_conflict
        bad_effect = bad_effect or effect_conflict
        ok = (
            edge_ok and valid_id(ref) and valid_id(key) and not source_conflict and not effect_conflict
            and scored.get("session_id") == sid and scored.get("plan_id") == pid
            and scored.get("actuation_id") == aid and scored.get("scored") is True
            and scored.get("scorer_independent") is True and scored.get("controller_visible") is False
            and scored.get("scorer_source") == "independent_progress_clock_v2"
            and scored.get("kind") in {"KILL_COUNT_INCREASE", "DEATH_COUNT_INCREASE", "MAP_EXIT", "PROGRESS"}
            and scored.get("polarity") in {"useful", "harmful"}
            and type(scored.get("observed_ns")) is int and scored.get("observed_ns", -1) >= edge_times[0][1]
        )
        if ok:
            good.append(scored)
            source_universe.add(ref)
            effect_ids.add(key)
        else:
            rejected = True

    if bad_source:
        effect_status, chosen = "UNRESOLVED_DUPLICATE_SOURCE_EVENT", None
    elif bad_effect or len(good) > 1:
        effect_status, chosen = "UNRESOLVED_DUPLICATE_EFFECT", None
    elif len(good) == 1 and not rejected:
        effect_status, chosen = "TASK_EFFECT_SCOPED", good[0]["effect_id"]
    elif record.get("task_effects"):
        effect_status, chosen = "UNRESOLVED_UNBOUND_OR_INVALID_EFFECT", None
    else:
        effect_status, chosen = "UNRESOLVED_NO_TASK_EFFECT", None
    return {"physical_actuation": "PHYSICAL_ACTUATION_SCOPED" if edge_ok else "UNRESOLVED",
            "state_feedback": state, "task_effect": effect_status, "effect_id": chosen,
            "grants_input_authority": False, "grants_task_authority": False}
