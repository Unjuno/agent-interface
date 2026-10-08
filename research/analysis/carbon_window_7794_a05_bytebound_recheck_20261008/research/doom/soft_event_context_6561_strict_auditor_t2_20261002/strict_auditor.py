"""Strict raw-only checks for the frozen SOFT_CHANGED receipt boundary."""
from __future__ import annotations

EXPECTED_CASES = ["NONE", "ONE_SOFT", "MULTI_SOFT", "HARD", "UNKNOWN", "EXPIRED"]
REQUIRED_SOFT_FIELDS = {
    "status": "SOFT_CHANGED",
    "keep_existing_policy": True,
    "requires_new_decision": False,
    "grants_input_authority": False,
    "may_only_preserve_or_reduce_existing_authority": True,
    "semantic_change_identified": True,
    "task_success_verified": False,
}


def audit_packet(packet: dict, expected_binding: dict) -> list[str]:
    """Return stable raw-evidence errors; never trusts a packet's own binding anchor."""
    errors: list[str] = []
    if type(packet) is not dict or set(packet) != {"cases"}:
        return ["packet_shape"]
    cases = packet.get("cases")
    if type(cases) is not list or [row.get("case_id") for row in cases if type(row) is dict] != EXPECTED_CASES:
        return ["case_set_or_order"]
    for case in cases:
        case_id = case["case_id"]
        if case.get("binding") != expected_binding:
            errors.append(f"{case_id}:external_binding_mismatch")
        seq = case.get("current_sequence")
        if type(seq) is not int or seq < 0:
            errors.append(f"{case_id}:current_sequence_invalid")
            continue
        events = case.get("raw_events")
        if type(events) is not list:
            errors.append(f"{case_id}:raw_events_invalid")
            continue
        prior_seq = -1
        for index, event in enumerate(events):
            label = f"{case_id}:event_{index}"
            if type(event) is not dict:
                errors.append(f"{label}:event_shape")
                continue
            event_seq = event.get("sequence")
            if type(event_seq) is not int or not prior_seq < event_seq < seq:
                errors.append(f"{label}:sequence_invalid")
            elif type(event_seq) is int:
                prior_seq = event_seq
            signal = event.get("signal")
            if type(signal) is not dict or signal.get("binding") != expected_binding:
                errors.append(f"{label}:external_binding_mismatch")
            outcome = event.get("outcome")
            if type(outcome) is not dict:
                errors.append(f"{label}:outcome_shape")
                continue
            status = outcome.get("status")
            if status == "SOFT_CHANGED":
                for key, expected in REQUIRED_SOFT_FIELDS.items():
                    actual = outcome.get(key, object())
                    if type(actual) is not bool and type(expected) is bool:
                        errors.append(f"{label}:{key}_type")
                    elif actual != expected:
                        errors.append(f"{label}:{key}_value")
                context = case.get("context")
                if type(context) is not dict:
                    errors.append(f"{label}:context_shape")
                else:
                    for key in ("grants_input_authority", "task_success_verified"):
                        if type(context.get(key)) is not bool or context.get(key) is not False:
                            errors.append(f"{label}:context_{key}")
    return errors

