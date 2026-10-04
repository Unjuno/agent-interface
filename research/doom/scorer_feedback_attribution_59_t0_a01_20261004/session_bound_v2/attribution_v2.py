"""Add session provenance checks before v1's temporal attribution join."""
from __future__ import annotations

from scorer_feedback_attribution_v1 import attribute_positive_events as _attribute_v1


def _checked_session_id(row: dict, source: str) -> str:
    if not isinstance(row, dict):
        raise ValueError(f"{source} row must be an object")
    session_id = row.get("session_id")
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError(f"{source} row requires a non-empty session_id")
    return session_id


def attribute_positive_events(samples: list[dict], events: list[dict], intervals: list[dict]) -> list[dict]:
    """Reject cross-session or provenance-free joins, then apply v1's rules."""
    session_ids = []
    for source, rows in (("sample", samples), ("event", events), ("interval", intervals)):
        if not isinstance(rows, list):
            raise ValueError(f"{source}s must be a list")
        session_ids.extend(_checked_session_id(row, source) for row in rows)

    if session_ids and any(session_id != session_ids[0] for session_id in session_ids[1:]):
        raise ValueError("session_id mismatch across scorer and actuation records")

    return _attribute_v1(samples, events, intervals)
