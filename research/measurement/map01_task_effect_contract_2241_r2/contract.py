from __future__ import annotations
from typing import Any

ROLES = {"PHYSICAL_ACTUATION", "STATE_FEEDBACK", "TASK_EFFECT"}

def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value)

def classify(events: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    task: list[dict[str, Any]] = []
    seen: set[Any] = set()

    for event in events:
        role = event.get("role")
        if role not in ROLES:
            errors.append("unknown_role")
            continue
        if role == "PHYSICAL_ACTUATION":
            if not all(_nonempty_string(event.get(k)) for k in ("plan_id", "actuation_id")):
                errors.append("physical_lineage")
            if not isinstance(event.get("t_ns"), int):
                errors.append("physical_clock")
            if not _nonempty_string(event.get("clock_domain")):
                errors.append("physical_clock_domain")
        elif role == "TASK_EFFECT":
            valid_timestamp = isinstance(event.get("t_ns"), int)
            if event.get("scored") is not True or not _nonempty_string(event.get("effect_id")):
                errors.append("task_effect_score")
            if not all(_nonempty_string(event.get(k)) for k in ("plan_id", "actuation_id")):
                errors.append("task_effect_lineage")
            if not valid_timestamp or not _nonempty_string(event.get("scorer_source")):
                errors.append("task_effect_provenance")
            if not _nonempty_string(event.get("clock_domain")):
                errors.append("task_effect_clock_domain")
            if event.get("effect_id") in seen:
                errors.append("duplicate_effect")
            seen.add(event.get("effect_id"))
            if valid_timestamp:
                task.append(event)

    physical = [
        event for event in events
        if event.get("role") == "PHYSICAL_ACTUATION"
        and isinstance(event.get("t_ns"), int)
        and _nonempty_string(event.get("clock_domain"))
    ]
    bound: list[dict[str, Any]] = []
    for event in task:
        matches = [
            physical_event for physical_event in physical
            if (physical_event.get("plan_id"), physical_event.get("actuation_id"))
            == (event.get("plan_id"), event.get("actuation_id"))
        ]
        if not matches:
            errors.append("task_effect_unbound")
            continue
        domains = {physical_event.get("clock_domain") for physical_event in matches}
        if len(domains) != 1 or event.get("clock_domain") not in domains:
            errors.append("clock_domain_mismatch")
            continue
        if event["t_ns"] < min(physical_event["t_ns"] for physical_event in matches):
            errors.append("effect_before_actuation")
            continue
        bound.append(event)

    decision = (
        "TASK_EFFECT_BOUND" if bound and not errors
        else "UNRESOLVED_NO_TASK_EFFECT" if not bound and not errors
        else "REJECT"
    )
    return {
        "physical_count": len(physical),
        "task_effect_count": len(bound),
        "task_effects": bound,
        "errors": sorted(set(errors)),
        "task_effect_authority": False,
        "decision": decision,
    }

def oracle(events: list[dict[str, Any]]) -> dict[str, Any]:
    physical: dict[tuple[Any, Any], tuple[int, str]] = {}
    for event in events:
        if (
            event.get("role") == "PHYSICAL_ACTUATION"
            and isinstance(event.get("t_ns"), int)
            and _nonempty_string(event.get("clock_domain"))
        ):
            physical[(event.get("plan_id"), event.get("actuation_id"))] = (
                event["t_ns"], event["clock_domain"]
            )
    effects = [event for event in events if event.get("role") == "TASK_EFFECT" and event.get("scored") is True]
    errors: list[str] = []
    accepted = 0
    for event in effects:
        key = (event.get("plan_id"), event.get("actuation_id"))
        timestamp = event.get("t_ns")
        if key not in physical or not isinstance(timestamp, int):
            errors.append("effect_invalid")
            continue
        physical_timestamp, physical_domain = physical[key]
        if not _nonempty_string(event.get("clock_domain")) or event["clock_domain"] != physical_domain:
            errors.append("clock_domain_mismatch")
            continue
        if timestamp < physical_timestamp:
            errors.append("effect_invalid")
            continue
        accepted += 1
    return {"accepted": accepted if not errors else 0, "errors": sorted(set(errors))}
