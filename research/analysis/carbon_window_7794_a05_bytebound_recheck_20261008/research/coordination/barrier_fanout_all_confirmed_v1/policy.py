CONFIRMED = "BARRIER_CONFIRMED"
CONFLICT = "BARRIER_CONFLICT"
UNKNOWN = "BARRIER_UNKNOWN"


def classify(expected_bytes: bytes, observed_bytes):
    if observed_bytes is None:
        return UNKNOWN
    if observed_bytes == expected_bytes:
        return CONFIRMED
    return CONFLICT


def aggregate(receiver_results):
    results = list(receiver_results)
    if all(result == CONFIRMED for result in results):
        return {"disposition": "ALL_CONFIRMED", "advance": True}
    if any(result == CONFLICT for result in results):
        return {"disposition": "HOLD_CONFLICT", "advance": False}
    return {"disposition": "HOLD_UNKNOWN", "advance": False}
