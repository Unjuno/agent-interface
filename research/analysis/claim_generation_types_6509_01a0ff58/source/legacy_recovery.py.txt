"""Research-only prefix reconstruction; never grants input authority."""
import json
from pathlib import Path

MANDATORY = ("identity", "freshness", "effect")

def recover(path, *, generation=1, scope="synthetic-claim"):
    def unknown(reason):
        return {"disposition": "PARTIAL_UNKNOWN", "reason": reason,
                "completed": [], "missing": list(MANDATORY)}
    data = Path(path).read_bytes()
    if len(data) > 65536:
        return unknown("OVERSIZE")
    # Only newline-terminated records contribute. A torn tail is not a receipt.
    records = data.split(b"\n")[:-1]
    parsed = []
    try:
        for position, encoded in enumerate(records):
            item = json.loads(encoded)
            if type(item) is not dict or set(item) != {"sequence", "check", "value", "generation", "scope"}:
                return unknown("SCHEMA")
            if type(item["sequence"]) is not int or item["sequence"] != position + 1:
                return unknown("SEQUENCE")
            if position >= len(MANDATORY) or item["check"] != MANDATORY[position]:
                return unknown("ORDER_OR_DUPLICATE")
            if type(item["value"]) is not bool or type(item["generation"]) is not int:
                return unknown("SCALAR_TYPE")
            if item["generation"] != generation or item["scope"] != scope:
                return unknown("GENERATION_OR_SCOPE")
            parsed.append(item)
    except (ValueError, UnicodeError):
        return unknown("CORRUPT_COMPLETE_RECORD")
    completed = [item["check"] for item in parsed]
    missing = list(MANDATORY[len(parsed):])
    if any(item["check"] in ("identity", "effect") and item["value"] is False for item in parsed):
        disposition, reason = "COUNTEREXAMPLE", "SOURCE_CURRENT_NEGATIVE"
    elif not missing and all(item["value"] for item in parsed):
        disposition, reason = "COMPLETE_VERDICT", "MANDATORY_COMPLETE"
    else:
        disposition, reason = "PARTIAL_UNKNOWN", "MISSING_OR_UNPROVEN_MANDATORY"
    return dict(disposition=disposition, reason=reason, completed=completed, missing=missing)
