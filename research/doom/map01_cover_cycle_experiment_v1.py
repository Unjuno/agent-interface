"""Select an exact repeated cycle without increasing a compiled cover's budget."""
from copy import deepcopy


def split_repeated_cover(steps, *, hold_count):
    if type(steps) is not list or type(hold_count) is not int or hold_count < 1:
        raise ValueError("an authored repeated cover is required")
    width = hold_count + 1
    if len(steps) < width * 2 or len(steps) % width:
        raise ValueError("complete repeated cycles are required")
    cycle = steps[:width]
    if (any(type(step) is not dict or step.get("op") != "hold" for step in cycle[:-1])
            or type(cycle[-1]) is not dict or cycle[-1].get("op") != "coast"
            or any(type(step.get("duration_ms")) is not int or step["duration_ms"] <= 0
                   for step in cycle)
            or any(steps[offset:offset + width] != cycle
                   for offset in range(width, len(steps), width))):
        raise ValueError("cover cycles must be exactly identical")
    return deepcopy(cycle), len(steps) // width
