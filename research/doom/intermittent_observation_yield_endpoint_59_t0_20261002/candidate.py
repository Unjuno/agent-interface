"""Finite conservative capture-interval admission predicate for Issue #6562."""

def decide(source_sequence: int, source_health: int, event: dict) -> str:
    if event["clock_domain"] != "runtime-monotonic":
        return "YIELD_CLOCK_DOMAIN"
    interval = event["capture_interval_ns"]
    if interval is None:
        return "YIELD_OBSERVATION_MISSING"
    if len(interval) != 2 or any(type(value) is not int for value in interval) or interval[0] > interval[1]:
        return "YIELD_CAPTURE_INTERVAL_MALFORMED"
    if interval[0] > event["available_at_ns"]:
        return "YIELD_CAPTURE_NOT_AVAILABLE"
    if interval[0] <= event["available_at_ns"] <= interval[1]:
        return "YIELD_CAPTURE_ORDER_UNKNOWN"
    sequence = event["observation_sequence"]
    if type(sequence) is not int or sequence <= source_sequence:
        return "YIELD_NON_FRESH"
    health = event["health"]
    if health.get("status") == "missing":
        return "YIELD_OBSERVATION_MISSING"
    if health.get("status") == "unavailable":
        return "YIELD_HEALTH_UNAVAILABLE"
    if health.get("status") != "observed":
        return "YIELD_HEALTH_MALFORMED"
    value = health.get("value")
    if type(value) is not int or value < 0:
        return "YIELD_HEALTH_MALFORMED"
    if value < source_health:
        return "YIELD_HEALTH_LOSS"
    return "CONTINUE"
