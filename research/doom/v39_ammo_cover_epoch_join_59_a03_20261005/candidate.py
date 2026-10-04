"""Construction-only paired-frame ammo/health guard probe."""
from doom_typed_observation_v1 import build_action_snapshot
from observable_signal_guard_v2 import ObservableSignalGuard

FLOORS = {"health": 90, "ammo": 1}


def _snapshot(event):
    if type(event.get("sequence")) is not int or type(event.get("capture_ns")) is not int:
        raise ValueError("frame identity must use exact integers")
    signals = event.get("signals")
    if not isinstance(signals, dict):
        raise ValueError("signals missing")
    for name in FLOORS:
        row = signals.get(name)
        if not isinstance(row, dict) or type(row.get("sequence")) is not int or type(row.get("capture_ns")) is not int:
            raise ValueError("signal frame identity must use exact integers")
        if row["sequence"] != event["sequence"] or row["capture_ns"] != event["capture_ns"]:
            raise ValueError("signal does not belong to event frame")
        if row.get("binding") != event.get("pointer_binding"):
            raise ValueError("signal binding does not belong to event frame")
    return build_action_snapshot(event, {
        "format": "action-validity-contract-v1",
        "source": {"signals": {"health": {}, "ammo": {}}},
    })


def assess_pair(source_event, current_event):
    try:
        _snapshot(source_event)
    except (KeyError, TypeError, ValueError):
        return {"decision": "replan", "reason": "source_typed_frame_invalid"}
    try:
        _snapshot(current_event)
    except (KeyError, TypeError, ValueError):
        return {"decision": "replan", "reason": "current_typed_frame_invalid"}

    results = {}
    for name, floor in FLOORS.items():
        source = source_event["signals"][name]
        guard = ObservableSignalGuard({
            "op": "observable_signal_guard", "guard_id": f"a03-{name}",
            "source_sequence": source["sequence"], "signal_id": name,
            "source_value": source["value"], "hard_minimum": floor,
            "max_source_age_ms": 30000,
            "on_soft_change": "preserve_existing_policy",
            "on_hard_change": "needs_decision", "on_unknown": "needs_decision",
        }, source, source["binding"])
        results[name] = guard.evaluate(current_event["signals"][name])
    replan = any(row["requires_new_decision"] for row in results.values())
    return {
        "decision": "replan" if replan else "preserve",
        "reason": "guard_requires_new_decision" if replan else "paired_frame_valid",
        "source_frame": {"sequence": source_event["sequence"], "capture_ns": source_event["capture_ns"]},
        "current_frame": {"sequence": current_event["sequence"], "capture_ns": current_event["capture_ns"]},
        "signals": results,
        "grants_input_authority": False,
    }
