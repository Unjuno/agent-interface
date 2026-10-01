"""Candidate classifier for the #1839 evidence-role contract (synthetic only)."""
from __future__ import annotations


def classify(row: dict) -> dict:
    """Classify physical, state, and task-effect evidence independently.

    This is a descriptive validator: it never grants input or task authority.
    The contract uses one explicitly attested monotonic clock axis.
    """
    plan = row.get("plan_id")
    act = row.get("actuation_id")
    session = row.get("session_id")
    physical = row.get("physical") or {}
    down, up = physical.get("down") or {}, physical.get("up") or {}
    physical_ok = bool(
        session and plan and act and row.get("clock_axis_attested") is True
        and physical.get("owner_id") and physical.get("empty_release_verified") is True
        and down.get("session_id") == session and up.get("session_id") == session
        and down.get("plan_id") == plan and up.get("plan_id") == plan
        and down.get("actuation_id") == act and up.get("actuation_id") == act
        and down.get("owner_id") == physical.get("owner_id") == up.get("owner_id")
        and down.get("key") == up.get("key") and isinstance(down.get("key"), str)
        and type(down.get("lower_ns")) is int and type(down.get("upper_ns")) is int
        and type(up.get("lower_ns")) is int and type(up.get("upper_ns")) is int
        and 0 <= down["lower_ns"] <= down["upper_ns"] <= up["lower_ns"] <= up["upper_ns"]
    )
    physical_out = "PHYSICAL_ACTUATION_SCOPED" if physical_ok else "UNRESOLVED"

    states = []
    for item in row.get("state_feedback", []):
        if (item.get("session_id") == session and type(item.get("observed_ns")) is int
                and item["observed_ns"] >= 0 and item.get("signal") in {"health", "ammo"}
                and type(item.get("before")) is int and type(item.get("after")) is int):
            states.append({"observed_ns": item["observed_ns"], "signal": item["signal"],
                           "before": item["before"], "after": item["after"],
                           "authority": False})

    effects = row.get("task_effects", [])
    qualifying = []
    seen = set()
    invalid_effect = False
    for effect in effects:
        eid = effect.get("effect_id")
        if (not physical_ok or not eid or eid in seen
                or effect.get("session_id") != session
                or effect.get("plan_id") != plan or effect.get("actuation_id") != act
                or effect.get("scored") is not True or effect.get("scorer_independent") is not True
                or effect.get("controller_visible") is not False
                or effect.get("scorer_source") != "independent_progress_clock_v2"
                or effect.get("kind") not in {"KILL_COUNT_INCREASE", "DEATH_COUNT_INCREASE", "MAP_EXIT", "PROGRESS"}
                or effect.get("polarity") not in {"useful", "harmful"}
                or type(effect.get("observed_ns")) is not int
                or effect["observed_ns"] < down["upper_ns"]):
            invalid_effect = True
            continue
        seen.add(eid)
        qualifying.append(effect)

    if len(qualifying) == 1 and not invalid_effect:
        task = "TASK_EFFECT_SCOPED"
        effect_id = qualifying[0]["effect_id"]
    elif len(qualifying) > 1:
        task, effect_id = "UNRESOLVED_DUPLICATE_EFFECT", None
    elif effects:
        task, effect_id = "UNRESOLVED_UNBOUND_OR_INVALID_EFFECT", None
    else:
        task, effect_id = "UNRESOLVED_NO_TASK_EFFECT", None

    return {"physical_actuation": physical_out, "state_feedback": states,
            "task_effect": task, "effect_id": effect_id,
            "grants_input_authority": False, "grants_task_authority": False}
