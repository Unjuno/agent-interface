"""Independent supplemental validation for preference inputs."""
import math


def weight_input_errors(case, criteria):
    if case.get("mode") != "weights":
        return []
    weights = case.get("input", {}).get("weights")
    if not isinstance(weights, dict) or set(weights) != set(criteria):
        return ["WEIGHT_VECTOR_SHAPE"]
    values = list(weights.values())
    if any(not isinstance(value, (int, float)) or isinstance(value, bool)
           or not math.isfinite(value) or value < 0 for value in values):
        return ["WEIGHT_VALUE_NOT_FINITE_NONNEGATIVE"]
    total = sum(values)
    if not math.isfinite(total) or abs(total - 1.0) > 1e-9:
        return ["WEIGHT_VECTOR_NOT_NORMALIZED"]
    return []
