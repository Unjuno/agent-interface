from statistics import median


DECISION_KEYS = {"decision", "target", "container", "state", "reason"}
DECISION_TYPES = {"TARGET", "STATE", "NO_ACTION", "YIELD"}
YIELD_REASONS = {"AMBIGUOUS", "UNSUPPORTED", "INSUFFICIENT_EVIDENCE"}
STATE_TYPES = {"STATUS_SAVED", "STATUS_PAUSED"}


def validate_result(value):
    if not isinstance(value, dict):
        raise ValueError("result must be a JSON object")
    if set(value) != DECISION_KEYS:
        raise ValueError("unexpected keys; authority fields are forbidden")
    if not isinstance(value["decision"], str) or value["decision"] not in DECISION_TYPES:
        raise ValueError("unknown decision")

    decision = value["decision"]
    target, container, state, reason = (
        value["target"], value["container"], value["state"], value["reason"]
    )
    if decision == "TARGET":
        if not isinstance(target, str) or not target.strip():
            raise ValueError("target must be non-empty for TARGET")
        if not isinstance(container, str) or not container.strip():
            raise ValueError("container must be non-empty for TARGET")
        if not isinstance(state, str) or state not in {"ENABLED", "DISABLED"} or reason is not None:
            raise ValueError("invalid TARGET state or reason")
    elif decision == "STATE":
        if target is not None or container is not None:
            raise ValueError("STATE cannot include target/container")
        if not isinstance(state, str) or state not in STATE_TYPES or reason is not None:
            raise ValueError("invalid STATE label or reason")
    elif decision == "NO_ACTION":
        if target is not None or container is not None or state is not None:
            raise ValueError("NO_ACTION cannot include a target or state")
        if not isinstance(reason, str) or reason != "TARGET_ABSENT":
            raise ValueError("NO_ACTION requires TARGET_ABSENT")
    else:
        if target is not None or container is not None or state is not None:
            raise ValueError("YIELD cannot include a target or state")
        if not isinstance(reason, str) or reason not in YIELD_REASONS:
            raise ValueError("YIELD requires an allowed reason")
    return {key: value[key] for key in ("decision", "target", "container", "state", "reason")}


def score_rows(rows, oracle):
    if not isinstance(rows, list) or not isinstance(oracle, dict):
        raise ValueError("rows and oracle must be list/object")
    ids = [row.get("case_id") for row in rows if isinstance(row, dict)]
    if len(ids) != len(rows) or len(ids) != len(set(ids)):
        raise ValueError("duplicate or malformed case rows")
    if set(ids) != set(oracle):
        raise ValueError("case denominator does not match oracle")
    exact = 0
    wrong_target = 0
    for row in rows:
        result = validate_result(row.get("result"))
        expected = oracle[row["case_id"]]
        if result == expected:
            exact += 1
        if expected["decision"] == "TARGET" and result["decision"] == "TARGET":
            if (result["target"], result["container"]) != (expected["target"], expected["container"]):
                wrong_target += 1
    return {"exact": exact, "total": len(rows), "wrong_target": wrong_target}


def median_ns(values):
    if not values:
        raise ValueError("latency sample is empty")
    if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in values):
        raise ValueError("latency values must be positive integer nanoseconds")
    return int(median(values))
