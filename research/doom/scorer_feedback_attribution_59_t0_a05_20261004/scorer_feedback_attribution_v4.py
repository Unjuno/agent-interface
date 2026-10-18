"""A05 strict wrapper around the immutable A04 temporal-envelope helper."""
from __future__ import annotations

from scorer_feedback_attribution_v3 import attribute_positive_events as _a04_attribute

POSITIVE_USEFUL_EVENT_KINDS = frozenset({"KILL_COUNT_INCREASE", "MAP_EXIT"})
EVENT_SCHEMA = "independent-progress-event-v2"


def attribute_positive_events(samples, events, intervals):
    """Reject positive-useful event names outside the frozen v2 producer vocabulary."""
    for event in events:
        if not isinstance(event, dict) or event.get("schema") != EVENT_SCHEMA:
            continue  # Preserve A04's existing schema validation and error.
        if event.get("polarity") == "positive" and event.get("useful") is True:
            kind = event.get("kind")
            if not isinstance(kind, str) or kind not in POSITIVE_USEFUL_EVENT_KINDS:
                raise ValueError("positive useful event kind is outside v2 producer vocabulary")
    return _a04_attribute(samples, events, intervals)
