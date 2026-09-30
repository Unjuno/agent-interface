"""Fail-closed classifier for synthetic T0 source/effect-join contract rows."""

REQUIRED = (
    "session_id", "plan_id", "actuation_id", "source_event_id",
    "scorer_event_id", "scorer_effect_kind", "scorer_session_id", "scorer_plan_id",
    "scorer_actuation_id", "scorer_source_event_id",
    "clock_domain", "scorer_clock_domain", "down_ns", "terminal_ns",
    "scorer_monotonic_ns",
)


def classify(row):
    if row.get("duplicate_scorer_events", 0) > 1:
        return "FAIL_AMBIGUOUS_EVENT_BINDING"
    if row.get("mode") == "NO_INPUT" and row.get("scorer_event_id") is not None:
        return "FAIL_AUTHORITY_OR_ATTRIBUTION_LAUNDERING"
    if row.get("scorer_event_id") is not None and row.get("event_kind") != "TASK_EFFECT":
        return "HOLD_UNSUPPORTED_EVENT_KIND"
    if row.get("scorer_event_id") is not None and row.get("scorer_effect_kind") not in ("KILL_COUNT_INCREASE", "MAP_EXIT"):
        return "HOLD_UNSUPPORTED_EFFECT_KIND"
    if not row.get("physical_down") or not row.get("physical_up"):
        return "HOLD_PHYSICAL_EDGE_INCOMPLETE"
    if not row.get("terminal_neutral"):
        return "HOLD_TERMINAL_NOT_NEUTRAL"
    if any(row.get(key) in (None, "") for key in REQUIRED):
        return "HOLD_SOURCE_IDENTITY_INSUFFICIENT"
    for left, right in (
        ("session_id", "scorer_session_id"),
        ("plan_id", "scorer_plan_id"),
        ("actuation_id", "scorer_actuation_id"),
        ("source_event_id", "scorer_source_event_id"),
    ):
        if row[left] != row[right]:
            return "HOLD_SOURCE_IDENTITY_INSUFFICIENT"
    if row["clock_domain"] != row["scorer_clock_domain"]:
        return "HOLD_CLOCK_DOMAIN_UNCOMPARABLE"
    if not row["down_ns"] < row["scorer_monotonic_ns"] < row["terminal_ns"]:
        return "HOLD_CLOCK_DOMAIN_UNCOMPARABLE"
    if row.get("scorer_authority") is not False:
        return "FAIL_AUTHORITY_OR_ATTRIBUTION_LAUNDERING"
    return "BOUND_TASK_EFFECT"
