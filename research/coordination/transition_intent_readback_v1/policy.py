def exact_recovery(observed_bytes, expected_after_bytes):
    if observed_bytes is None:
        return "UNKNOWN_READBACK"
    if observed_bytes == expected_after_bytes:
        return "ALREADY_COMMITTED_SELF"
    return "UNKNOWN_CONTENT_MISMATCH"


def intent_recovery(state, requested_transition):
    receipt = state.get("last_applied_transition")
    if receipt is None:
        return "UNKNOWN_NO_APPLIED_TRANSITION"
    if receipt.get("intent_id") != requested_transition.get("intent_id"):
        return "UNKNOWN_OTHER_INTENT"
    if receipt == requested_transition:
        return "ALREADY_COMMITTED_SELF"
    return "CONFLICT_INTENT_CONTENT"
