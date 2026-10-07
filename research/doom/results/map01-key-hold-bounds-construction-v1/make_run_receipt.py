"""Fail-closed tombstone; the historical helper overwrote RUN.json."""
raise SystemExit(
    "STOP: the historical run receipt is immutable. "
    "Do not regenerate RUN.json in this evidence package."
)
