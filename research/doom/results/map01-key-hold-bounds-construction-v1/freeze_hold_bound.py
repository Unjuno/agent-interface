"""Fail-closed tombstone; the historical freezer overwrote PRE-RUN.json."""
raise SystemExit(
    "STOP: the historical freeze is immutable. "
    "Do not regenerate PRE-RUN.json in this evidence package."
)
