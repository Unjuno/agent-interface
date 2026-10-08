"""Independent blinded coder A for the frozen synthetic trace vocabulary."""

ROW_KEYS = {"row_id", "pair_id", "blind_code", "goal", "allowed_methods", "segments", "final_outcome"}
SEGMENT_KEYS = {"method", "operators", "events", "duration_ms", "outcome"}

def annotate(row, penalty_ms):
    if set(row) != ROW_KEYS:
        raise ValueError("row schema exposes unexpected fields (including arm labels)")
    segments = []
    for segment in row["segments"]:
        if set(segment) != SEGMENT_KEYS:
            raise ValueError("segment schema mismatch")
        if segment["method"] not in row["allowed_methods"]:
            raise ValueError("selected method is not permitted")
        events = segment["events"]
        segments.append({
            "method": str(segment["method"]),
            "operators": list(segment["operators"]),
            "duration_ms": int(segment["duration_ms"]),
            "outcome": str(segment["outcome"]),
            "errors": sum(1 for event in events if event == "error"),
            "switches": sum(1 for event in events if event == "switch"),
            "terminal": "complete" if "complete" in events else ("timeout" if "timeout" in events else "nonterminal"),
        })
    unfinished = row["final_outcome"] == "unfinished"
    return {
        "row_id": str(row["row_id"]),
        "pair_id": str(row["pair_id"]),
        "goal": str(row["goal"]),
        "segments": segments,
        "final_outcome": str(row["final_outcome"]),
        "elapsed_ms": sum(item["duration_ms"] for item in segments),
        "penalty_ms": int(penalty_ms if unfinished else 0),
        "errors": sum(item["errors"] for item in segments),
        "switches": sum(item["switches"] for item in segments),
    }
