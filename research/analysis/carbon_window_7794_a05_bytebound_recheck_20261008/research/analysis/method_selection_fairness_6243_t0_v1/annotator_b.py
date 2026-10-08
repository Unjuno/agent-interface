"""Second rule set: derive the same codebook fields using independent checks."""

def annotate(row):
    expected = {"row_id", "blind_code", "goal", "method", "operators", "events", "duration_ms", "outcome", "acquisition_ms"}
    if row.keys() != expected:
        raise ValueError("row schema differs from blinded codebook")
    event_set = set(row["events"])
    if not event_set <= {"start", "error", "switch", "complete"}:
        raise ValueError("unknown event token")
    if row["outcome"] not in ("correct", "failed"):
        raise ValueError("unknown outcome")
    return {
        "row_id": str(row["row_id"]),
        "goal": str(row["goal"]),
        "method": str(row["method"]),
        "operators": tuple(str(op) for op in row["operators"]),
        "switches": int("switch" in event_set) + row["events"].count("switch") - int("switch" in event_set),
        "errors": row["events"].count("error"),
        "terminal": row["outcome"],
        "duration_ms": int(row["duration_ms"]),
        "acquisition_ms": int(row["acquisition_ms"]),
    }
