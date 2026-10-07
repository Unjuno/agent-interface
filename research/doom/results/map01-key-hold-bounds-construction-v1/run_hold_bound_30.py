"""Fail-closed tombstone for the consumed one-shot historical runner."""
raise SystemExit(
    "STOP: this frozen one-shot would overwrite RAW-30.json. "
    "Use verify_preserved_hold_bound_30.py; do not rerun the historical candidate."
)
