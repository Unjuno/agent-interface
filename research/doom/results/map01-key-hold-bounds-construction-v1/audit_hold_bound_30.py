"""Fail-closed tombstone; the historical auditor overwrote AUDIT.json."""
raise SystemExit(
    "STOP: this historical auditor rewrites AUDIT.json. "
    "Use verify_preserved_hold_bound_30.py for read-only integrity checks."
)
