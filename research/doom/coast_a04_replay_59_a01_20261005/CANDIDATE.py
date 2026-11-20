"""Small candidate component implementing PR #7527's fixed 5-down 2-of-3 rule."""
from collections import deque


def candidate(baseline, observations):
    low_rows = deque(maxlen=3)
    for row in observations:
        low_rows.append({
            "sequence": row["sequence"],
            "emit_ns": row["emit_ns"],
            "value": row["health"] <= baseline - 5,
        })
        if len(low_rows) >= 2 and sum(item["value"] for item in low_rows) >= 2:
            return {"sequence": row["sequence"], "emit_ns": row["emit_ns"], "health": row["health"]}
    return None

