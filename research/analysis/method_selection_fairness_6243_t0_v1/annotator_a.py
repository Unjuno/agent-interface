"""First independent rule set: parse the blinded event vocabulary directly."""

def annotate(row):
    allowed = {"row_id", "blind_code", "goal", "method", "operators", "events", "duration_ms", "outcome", "acquisition_ms"}
    if set(row) != allowed:
        raise ValueError("unexpected or arm-revealing fields")
    return {
        "row_id": row["row_id"],
        "goal": row["goal"],
        "method": row["method"],
        "operators": tuple(row["operators"]),
        "switches": sum(event == "switch" for event in row["events"]),
        "errors": sum(event == "error" for event in row["events"]),
        "terminal": "correct" if "complete" in row["events"] else "failed",
        "duration_ms": int(row["duration_ms"]),
        "acquisition_ms": int(row["acquisition_ms"]),
    }
