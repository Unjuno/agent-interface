"""Independent blinded coder B; derives terminal state and costs separately."""

def annotate(trace, timeout_charge):
    allowed = {"row_id", "pair_id", "blind_code", "goal", "allowed_methods", "segments", "final_outcome"}
    if trace.keys() != allowed:
        raise ValueError("blinded trace has unknown or arm-revealing columns")
    coded_segments = []
    for segment in trace["segments"]:
        if set(segment) != {"method", "operators", "events", "duration_ms", "outcome"}:
            raise ValueError("unknown segment columns")
        method = str(segment["method"])
        if method not in tuple(trace["allowed_methods"]):
            raise ValueError("method outside row-level permission set")
        tokens = tuple(segment["events"])
        coded_segments.append({
            "method": method,
            "operators": [str(op) for op in tuple(segment["operators"])],
            "duration_ms": int(segment["duration_ms"]),
            "outcome": str(segment["outcome"]),
            "errors": len([token for token in tokens if token == "error"]),
            "switches": len([token for token in tokens if token == "switch"]),
            "terminal": next((terminal for terminal in ("complete", "timeout") if terminal in tokens), "nonterminal"),
        })
    final = str(trace["final_outcome"])
    return {
        "row_id": str(trace["row_id"]),
        "pair_id": str(trace["pair_id"]),
        "goal": str(trace["goal"]),
        "segments": coded_segments,
        "final_outcome": final,
        "elapsed_ms": sum(segment["duration_ms"] for segment in coded_segments),
        "penalty_ms": int(timeout_charge) if final == "unfinished" else 0,
        "errors": sum(segment["errors"] for segment in coded_segments),
        "switches": sum(segment["switches"] for segment in coded_segments),
    }
