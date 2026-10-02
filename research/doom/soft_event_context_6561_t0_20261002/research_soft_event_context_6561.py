"""Host-only construction prototype for Issue #6561; grants no authority."""
from __future__ import annotations

import copy

SOURCE = {
    "main": "648be0cb805a4cf44b9d8f6e1ad2a793b83bbf9a",
    "controller_blob": "201e580e58ee7e5455a25da55bdd4e0bfb9f8a92",
    "monitor_blob": "c0955f976e3a0af6ce926f22cee4a5ddf70ef543",
    "v30_audit_blob": "980acfca962e3cc4ff8c32968692374ea0b60191",
}


def candidate_context(history_state, soft_event_count, latest_soft_event,
                      current_sequence, current_binding):
    """Project a previously observed monitor event into bounded advisory data."""
    if history_state == "none":
        if soft_event_count != 0 or latest_soft_event is not None:
            raise ValueError("NONE requires empty monitor history")
        return {"state": "NONE"}
    if history_state != "observed":
        return {"state": "UNKNOWN", "reason": str(history_state)[:64]}
    if type(soft_event_count) is not int or soft_event_count < 1:
        return {"state": "UNKNOWN", "reason": "invalid_event_count"}
    if type(latest_soft_event) is not dict:
        return {"state": "UNKNOWN", "reason": "missing_latest_event"}

    signal = latest_soft_event.get("signal")
    outcome = latest_soft_event.get("outcome")
    if type(signal) is not dict or type(outcome) is not dict:
        return {"state": "UNKNOWN", "reason": "malformed_event"}
    seq = latest_soft_event.get("sequence")
    binding = signal.get("binding")
    if type(seq) is not int or seq >= current_sequence:
        return {"state": "UNKNOWN", "reason": "nonprior_event"}
    if binding != current_binding:
        return {"state": "UNKNOWN", "reason": "binding_changed"}
    if (signal.get("status") != "observed" or
            signal.get("signal_id") != "health" or
            outcome.get("status") != "SOFT_CHANGED" or
            outcome.get("signal_id") != "health" or
            outcome.get("current_value") != signal.get("value") or
            type(outcome.get("source_value")) is not int or
            type(signal.get("value")) is not int or
            type(outcome.get("source_age_ms")) not in (int, float) or
            outcome.get("source_age_ms") < 0 or
            type(outcome.get("guard_id")) is not str):
        return {"state": "UNKNOWN", "reason": "invalid_soft_receipt"}
    return {
        "state": "OBSERVED", "sequence": seq, "signal_id": "health",
        "source_value": outcome["source_value"],
        "current_value": signal["value"],
        "source_age_ms": outcome["source_age_ms"],
        "guard_id": outcome["guard_id"], "outcome": "SOFT_CHANGED",
        "soft_event_count": soft_event_count,
        "grants_input_authority": False,
        "task_success_verified": False,
    }


def auditor_derive(history_state, count, event, current_sequence, binding):
    """Independent raw-only derivation; intentionally no candidate import."""
    if history_state != "observed":
        return {"state": "NONE"} if history_state == "none" and count == 0 and event is None else {
            "state": "UNKNOWN", "reason": str(history_state)[:64]}
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        return {"state": "UNKNOWN", "reason": "invalid_event_count"}
    if not isinstance(event, dict):
        return {"state": "UNKNOWN", "reason": "missing_latest_event"}
    raw_seq = event.get("sequence")
    if isinstance(raw_seq, int) and not isinstance(raw_seq, bool) and raw_seq >= current_sequence:
        return {"state": "UNKNOWN", "reason": "nonprior_event"}
    try:
        evseq = event["sequence"]
        sig = event["signal"]
        result = event["outcome"]
        age = result["source_age_ms"]
        valid = (
            isinstance(evseq, int) and not isinstance(evseq, bool) and evseq < current_sequence
            and sig["binding"] == binding
            and sig["status"] == "observed" and sig["signal_id"] == "health"
            and result["status"] == "SOFT_CHANGED" and result["signal_id"] == "health"
            and result["current_value"] == sig["value"]
            and isinstance(result["source_value"], int)
            and isinstance(sig["value"], int)
            and isinstance(age, (int, float)) and not isinstance(age, bool) and age >= 0
            and isinstance(result["guard_id"], str)
        )
    except (KeyError, TypeError):
        valid = False
    if not valid:
        reason = "binding_changed" if isinstance(event.get("signal"), dict) and event["signal"].get("binding") != binding else "invalid_soft_receipt"
        return {"state": "UNKNOWN", "reason": reason}
    return {
        "state": "OBSERVED", "sequence": evseq, "signal_id": "health",
        "source_value": result["source_value"], "current_value": sig["value"],
        "source_age_ms": age, "guard_id": result["guard_id"],
        "outcome": "SOFT_CHANGED", "soft_event_count": count,
        "grants_input_authority": False, "task_success_verified": False,
    }


def auditor_verify_context(history_state, raw_events, current_sequence, binding, emitted):
    """Verify emitted context against the complete retained monitor event list."""
    if history_state == "none":
        expected = {"state": "NONE"} if raw_events == [] else {
            "state": "UNKNOWN", "reason": "none_with_events"}
    elif history_state != "observed":
        expected = {"state": "UNKNOWN", "reason": str(history_state)[:64]}
    elif not isinstance(raw_events, list) or not raw_events:
        expected = {"state": "UNKNOWN", "reason": "missing_raw_history"}
    else:
        accepted = [event for event in raw_events
                    if isinstance(event, dict)
                    and isinstance(event.get("outcome"), dict)
                    and event["outcome"].get("status") == "SOFT_CHANGED"]
        if len(accepted) != len(raw_events):
            expected = {"state": "UNKNOWN", "reason": "nonsoft_event_in_history"}
        else:
            latest = max(raw_events, key=lambda event: event.get("sequence", -1))
            expected = auditor_derive("observed", len(raw_events), latest,
                                      current_sequence, binding)
    if emitted != expected:
        raise ValueError("emitted context differs from independently derived raw history")
    return True


def render_prompt_context(context):
    """Stable serialization; separate from image/model transport."""
    import json
    return "Latest observed soft evidence (advisory only): " + json.dumps(
        context, sort_keys=True, separators=(",", ":")) + "\n"


def fixture():
    binding = {"session": "fixture-1"}
    def event(seq, source, current, age, guard):
        return {
            "sequence": seq,
            "signal": {"status": "observed", "signal_id": "health",
                       "value": current, "binding": copy.deepcopy(binding),
                       "capture_ns": 1_000_000 + seq},
            "outcome": {"status": "SOFT_CHANGED", "signal_id": "health",
                        "source_value": source, "current_value": current,
                        "source_age_ms": age, "guard_id": guard,
                        "keep_existing_policy": True,
                        "requires_new_decision": False,
                        "grants_input_authority": False,
                        "task_success_verified": False},
        }
    return binding, [
        ("NONE", "none", 0, None, 10, {"state": "NONE"}, []),
        ("ONE_SOFT", "observed", 1, event(73, 84, 78, 100, "map01-4"), 90,
         {"state":"OBSERVED","sequence":73,"signal_id":"health","source_value":84,"current_value":78,"source_age_ms":100,"guard_id":"map01-4","outcome":"SOFT_CHANGED","soft_event_count":1,"grants_input_authority":False,"task_success_verified":False},
         [event(73, 84, 78, 100, "map01-4")]),
        ("MULTI_SOFT", "observed", 3, event(137, 78, 73, 200, "map01-5"), 150,
         {"state":"OBSERVED","sequence":137,"signal_id":"health","source_value":78,"current_value":73,"source_age_ms":200,"guard_id":"map01-5","outcome":"SOFT_CHANGED","soft_event_count":3,"grants_input_authority":False,"task_success_verified":False},
         [event(73,84,78,100,"map01-4"), event(101,78,75,150,"map01-4b"), event(137,78,73,200,"map01-5")]),
        ("HARD", "invalidated", 1, None, 90, {"state":"UNKNOWN","reason":"invalidated"}, []),
        ("UNKNOWN", "unknown", 1, None, 90, {"state":"UNKNOWN","reason":"unknown"}, []),
        ("EXPIRED", "expired", 1, None, 90, {"state":"UNKNOWN","reason":"expired"}, []),
    ], binding

