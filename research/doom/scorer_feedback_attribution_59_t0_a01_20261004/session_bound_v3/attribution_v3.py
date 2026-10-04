"""Bind scorer-envelope association to one session before applying A03."""
from __future__ import annotations

import sys
from pathlib import Path

DOOM = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(DOOM / "scorer_feedback_attribution_59_t0_a03_20261004"))
from scorer_feedback_attribution_v2 import attribute_positive_events as _attribute_a03


def _session_id(row: dict, source: str) -> str:
    if not isinstance(row, dict):
        raise ValueError(f"{source} row must be an object")
    value = row.get("session_id")
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{source} row requires a non-empty session_id")
    return value


def attribute_positive_events(
    samples: list[dict], events: list[dict], intervals: list[dict]
) -> list[dict]:
    """Reject missing/cross-session records, then preserve A03 semantics."""
    session_ids = []
    for label, rows in (("sample", samples), ("event", events), ("interval", intervals)):
        if not isinstance(rows, list):
            raise ValueError(f"{label}s must be a list")
        session_ids.extend(_session_id(row, label) for row in rows)
    if session_ids and any(value != session_ids[0] for value in session_ids[1:]):
        raise ValueError("session_id mismatch across scorer and actuation records")
    return _attribute_a03(samples, events, intervals)
