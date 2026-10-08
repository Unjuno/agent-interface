"""Independent declarative same-clock ordering rule; imports no runtime."""

RETURN_CLOCKS = (10, 100, 200)
EXECUTION_RETURNS = (20, 110)


def expected(case):
    for index, captured in enumerate(case["captures"]):
        if type(captured) is not int or captured < 0:
            return {"kind": "exception", "exception_type": "ValueError",
                    "executions": index, "verifications": max(0, index - 1)}
        if (captured > RETURN_CLOCKS[index] or
                (index and captured < EXECUTION_RETURNS[index - 1])):
            return {"kind": "receipt", "outcome": "SAFE_YIELD",
                    "reason": "stale_observation", "completed": index,
                    "observations": index, "executions": index,
                    "verifications": max(0, index - 1),
                    "pending_action": (None, "enter", "save")[index]}
    return {"kind": "receipt", "outcome": "TASK_SUCCEEDED",
            "reason": "method_complete", "completed": 2, "observations": 3,
            "executions": 2, "verifications": 2, "pending_action": None}


def same_json(left, right):
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return left.keys() == right.keys() and all(
            same_json(left[k], right[k]) for k in left)
    if type(left) is list:
        return len(left) == len(right) and all(
            same_json(a, b) for a, b in zip(left, right))
    return left == right


def legacy_expected(case):
    """Legacy validates capture type/sign but does not compare clock order."""
    for index, captured in enumerate(case["captures"]):
        if type(captured) is not int or captured < 0:
            return {"kind": "exception", "exception_type": "ValueError",
                    "executions": index, "verifications": max(0, index - 1)}
    return {"kind": "receipt", "outcome": "TASK_SUCCEEDED",
            "reason": "method_complete", "completed": 2, "observations": 3,
            "executions": 2, "verifications": 2, "pending_action": None}


def summarize(row):
    calls = row["calls"]
    result = row["result"]
    summary = {"kind": result["kind"], "executions": len(calls["execute"]),
               "verifications": len(calls["verify_effect"])}
    if result["kind"] == "exception":
        summary["exception_type"] = result["exception_type"]
    else:
        receipt = result["receipt"]
        summary.update(outcome=receipt["outcome"], reason=receipt["reason"],
                       completed=receipt["completed_transitions"],
                       observations=len(receipt["observations"]),
                       pending_action=(receipt["pending_effect"]["action"]
                                       if receipt["pending_effect"] else None))
    return summary
