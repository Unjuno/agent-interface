"""Construction-only envelope helper for the #5156 joined-release JSONL row."""


def joined_release_envelope(owner_row, case, caller_receipt):
    """Preserve the owner event while emitting the auditor's joined_release schema."""
    if owner_row.get("event") != "owner_key_release_bracket":
        raise ValueError("expected owner_key_release_bracket")
    if owner_row.get("trigger_class") != "explicit_up":
        raise ValueError("joined release is only for explicit_up")
    required = (
        "release_call_started_ns",
        "release_call_returned_ns",
        "owner_id",
        "intent_token",
    )
    if any(key not in caller_receipt for key in required):
        raise ValueError("caller receipt is incomplete")

    result = dict(owner_row)
    result["owner_event"] = result.pop("event")
    result.update(
        case=case,
        caller_started_ns=caller_receipt["release_call_started_ns"],
        caller_returned_ns=caller_receipt["release_call_returned_ns"],
        caller_owner_id=caller_receipt["owner_id"],
        caller_intent_token=caller_receipt["intent_token"],
        event="joined_release",
    )
    return result
