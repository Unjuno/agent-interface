"""Independent supplemental validation for preference inputs."""
import math


def finite_number(value):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, TypeError):
        return False


def weight_input_errors(case, criteria):
    if case.get("mode") != "weights":
        return []
    inputs = case.get("input")
    if not isinstance(inputs, dict):
        return ["PREFERENCE_INPUT_NOT_OBJECT"]
    weights = inputs.get("weights")
    if not isinstance(weights, dict) or set(weights) != set(criteria):
        return ["WEIGHT_VECTOR_SHAPE"]
    values = list(weights.values())
    if any(not finite_number(value) or value < 0 for value in values):
        return ["WEIGHT_VALUE_NOT_FINITE_NONNEGATIVE"]
    total = sum(values)
    if not finite_number(total) or abs(total - 1.0) > 1e-9:
        return ["WEIGHT_VECTOR_NOT_NORMALIZED"]
    return []
