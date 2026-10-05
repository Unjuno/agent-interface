"""Finite synthetic repair-history enumerator; not an interface reliability model."""

FAULT_THRESHOLD = 4
HORIZON = 2
INITIAL_STATES = (0, 1, 2, 3)
OPERATORS = ("perfect", "minimal", "partial")


def enumerate_histories():
    rows = []
    for initial in INITIAL_STATES:
        for operator in OPERATORS:
            state = initial
            # A fixed unit exposure precedes intervention. Fault is independently
            # defined as threshold crossing; recovery does not erase that event.
            before = state + 1
            fault_before = before >= FAULT_THRESHOLD
            post = {"perfect": 0, "minimal": before, "partial": max(0, before - 2)}[operator]
            recurrence_at = None
            for tick in range(1, HORIZON + 1):
                state = post + tick
                if state >= FAULT_THRESHOLD:
                    recurrence_at = tick
                    break
            censored = recurrence_at is None
            rows.append({
                "initial_state": initial,
                "operator": operator,
                "exposure_before": 1,
                "fault_before": fault_before,
                "pre_repair_state": before,
                "post_repair_state": post,
                "exposure_after": recurrence_at if recurrence_at is not None else HORIZON,
                "recurrence_tick": recurrence_at,
                "censored": censored,
                "censor_horizon": HORIZON if censored else None,
            })
    return rows


def summarize(rows):
    if len(rows) != len(INITIAL_STATES) * len(OPERATORS):
        raise ValueError("incomplete equal-exposure enumeration")
    if {r["operator"] for r in rows} != set(OPERATORS):
        raise ValueError("operator coverage mismatch")
    by_operator = {}
    for op in OPERATORS:
        selected = [r for r in rows if r["operator"] == op]
        if len(selected) != len(INITIAL_STATES) or {r["initial_state"] for r in selected} != set(INITIAL_STATES):
            raise ValueError("unequal state/exposure coverage")
        by_operator[op] = {
            "episodes": len(selected),
            "recurrence_count": sum(r["recurrence_tick"] is not None for r in selected),
            "censored_count": sum(r["censored"] is True for r in selected),
            "fault_before_count": sum(r["fault_before"] is True for r in selected),
            "recurrence_ticks": [r["recurrence_tick"] for r in selected],
        }
    return by_operator
