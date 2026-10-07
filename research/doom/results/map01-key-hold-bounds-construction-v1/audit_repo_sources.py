"""Fail-closed tombstone; the historical audit overwrote its retained JSON."""
raise SystemExit(
    "STOP: the historical repository-source audit is immutable. "
    "Use check_current_main_sources.py for a read-only current-main comparison."
)
