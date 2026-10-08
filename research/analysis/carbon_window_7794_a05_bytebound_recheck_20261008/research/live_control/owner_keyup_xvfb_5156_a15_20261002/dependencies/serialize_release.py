def join_explicit_release(owner_row, caller_context):
    if not isinstance(owner_row, dict) or owner_row.get("event") != "owner_key_release_bracket":
        raise ValueError("expected owner_key_release_bracket")
    if not isinstance(caller_context, dict) or "event" in caller_context:
        raise ValueError("caller context must be a mapping without event")
    joined = dict(owner_row)
    joined.update(caller_context)
    joined["owner_event"] = joined["event"]
    joined["event"] = "joined_release"
    return joined
