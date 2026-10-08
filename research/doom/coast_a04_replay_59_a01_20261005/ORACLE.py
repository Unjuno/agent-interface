"""Independent raw-row oracle for the frozen fixed 5-down, 2-of-3 rule."""
from collections import deque


def oracle(baseline, observations):
    threshold = baseline - 5
    window = deque(maxlen=3)
    for row in observations:
        value = row["health"]
        window.append(value <= threshold)
        if sum(window) >= 2:
            return {"sequence": row["sequence"], "emit_ns": row["emit_ns"], "health": value}
    return None

