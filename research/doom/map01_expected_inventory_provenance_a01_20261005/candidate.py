"""Completeness wrapper for the retained per-key ledger construction case."""
from ledger import summarize


EXPECTED_KEYS = ("SPACE", "W")


def summarize_complete(rows, expected_keys=EXPECTED_KEYS):
    base = summarize(rows)
    if base["status"] != "BOUNDED":
        return base
    if (not isinstance(expected_keys, (tuple, list))
            or any(not isinstance(key, str) or not key for key in expected_keys)
            or len(set(expected_keys)) != len(expected_keys)):
        return {"status": "UNKNOWN", "intervals": [],
                "reasons": ["invalid_expected_key_inventory"]}
    observed = {row["key"] for row in base["intervals"]}
    if observed != set(expected_keys):
        return {"status": "UNKNOWN", "intervals": [],
                "reasons": ["expected_key_inventory_mismatch"]}
    return base
