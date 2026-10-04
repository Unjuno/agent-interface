"""Check occurrence-local admission/ack timestamps against XQueryKeymap samples."""


def check_occurrences(raw, expected_key="w"):
    """Return (ok, errors); does not infer device state or application effect."""
    errors = []
    occurrences = raw.get("occurrences")
    events = raw.get("events")
    if not isinstance(occurrences, list) or not isinstance(events, list):
        return False, ["occurrences/events must be lists"]

    seen = set()
    for occurrence in occurrences:
        token = occurrence.get("intent_token")
        if not isinstance(token, str) or token in seen:
            errors.append("missing or duplicate occurrence token")
            continue
        seen.add(token)
        pre = occurrence.get("pre_down", {})
        down = occurrence.get("post_down", {})
        up = occurrence.get("post_up", {})
        admissions = [event for event in events
                      if event.get("event") == "input_admission"
                      and event.get("intent_token") == token
                      and event.get("key") == expected_key]
        if len(admissions) != 1:
            errors.append(f"{token}: expected exactly one matching admission")
            continue
        admission = admissions[0]
        times = (pre.get("sample_finished_ns"), admission.get("admitted_ns"),
                 admission.get("input_ack_ns"), down.get("sample_started_ns"),
                 down.get("sample_finished_ns"), up.get("sample_started_ns"),
                 admission.get("valid_until_ns"))
        if any(type(value) is not int for value in times):
            errors.append(f"{token}: admission/sample timestamps must be integers")
            continue
        pre_end, admitted, ack, down_start, down_end, up_start, valid_until = times
        if not pre_end <= admitted <= ack <= down_start:
            errors.append(f"{token}: admission/ack not bound between pre-down and down")
        if not down_start <= down_end < up_start:
            errors.append(f"{token}: down/up sample interval is not ordered")
        if valid_until < down_end:
            errors.append(f"{token}: admission lease expired before down witness")

    return not errors, errors
