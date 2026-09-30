"""Independent reference oracle: no imports from policy.py."""

def expected(row):
    intent = row.get("intent")
    if intent not in ("TRACK", "STABILIZE", "WATCH_ONLY", "OUT_OF_SCOPE"):
        return "YIELD"
    if row.get("evidence") not in ("CLEAR", "MISSING", "AMBIGUOUS", "STALE"):
        return "YIELD"
    if row["evidence"] != "CLEAR" or row.get("generation_fresh") is not True:
        return "YIELD"
    if row.get("forbidden_effect") is True:
        return "YIELD"
    if row.get("completed") is True:
        return "NO_ACTION"
    if intent == "TRACK":
        if row.get("progressing") is True:
            return "CONTINUE"
        return "CORRECT"
    if intent == "STABILIZE":
        if row.get("progressing") is True:
            return "CONTINUE"
        return "CORRECT"
    if intent == "WATCH_ONLY":
        return "WATCH"
    return "YIELD"
