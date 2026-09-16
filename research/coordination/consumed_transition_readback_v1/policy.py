def classify_recovery(expected_after_bytes: bytes, observed):
    if observed == "UNAVAILABLE":
        return "UNKNOWN_COMMIT"
    if not isinstance(observed, (bytes, bytearray)):
        return "CONFLICT_READBACK"
    if bytes(observed) == expected_after_bytes:
        return "ALREADY_COMMITTED_SELF"
    return "CONFLICT_READBACK"


def may_reissue(decision: str) -> bool:
    return decision == "NAIVE_REISSUE"


def may_advance_one_use(state: dict) -> str:
    if state.get("confirmation_consumed"):
        return "HOLD_CONFIRMATION_CONSUMED"
    return "AUTHORIZE_TRANSITION"
