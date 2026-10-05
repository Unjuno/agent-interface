"""Conservative temporal alignment of independent outcome samples and key-up receipts.

These helpers compare timestamps only. They do not establish physical key state,
application consumption, or causal attribution between a released key and an outcome.
"""
from __future__ import annotations

from typing import Any


def useful_onset_bounds(previous: dict[str, Any], current: dict[str, Any],
                        *, field: str) -> tuple[int, int]:
    """Bound a sampled positive transition by the two sample execution windows.

    The previous sample must be negative and the current one positive. A sampled
    state is known to have been read somewhere inside its [started, finished]
    window, so these bounds intentionally include the whole endpoint windows.
    """
    for row in (previous, current):
        if type(row) is not dict:
            raise TypeError("sample rows must be dictionaries")
        if type(row.get("sample_started_ns")) is not int:
            raise ValueError("sample_started_ns must be an integer")
        if type(row.get("sample_finished_ns")) is not int:
            raise ValueError("sample_finished_ns must be an integer")
        if row["sample_started_ns"] > row["sample_finished_ns"]:
            raise ValueError("sample window is reversed")
        payload = row.get("payload")
        if type(payload) is not dict or field not in payload:
            raise ValueError(f"payload must contain {field}")
    if previous["sample_finished_ns"] > current["sample_started_ns"]:
        raise ValueError("sample windows overlap or are out of order")
    before = previous["payload"][field]
    after = current["payload"][field]
    if type(before) is not int or type(after) is not int or before < 0 or after < 0:
        raise ValueError("transition counters must be non-negative integers")
    if after <= before:
        raise ValueError("current sample does not show a positive transition")
    return previous["sample_started_ns"], current["sample_finished_ns"]


def owner_keyup_bracket(row: dict[str, Any]) -> tuple[int, int]:
    """Return the owner XTest/XSync bracket, preserving its limited meaning."""
    if type(row) is not dict or row.get("event") != "input_release_transition":
        raise ValueError("expected an input_release_transition row")
    if row.get("owner_thread_keyup_verified") is not True:
        raise ValueError("owner key-up receipt is not verified")
    receipt = row.get("owner_thread_keyup_receipt")
    if type(receipt) is not dict or receipt.get("server_sync_completed") is not True:
        raise ValueError("missing owner-thread XSync receipt")
    if receipt.get("physical_verification_authoritative") is not False:
        raise ValueError("physical verification scope must be explicitly false")
    start = receipt.get("owner_keyrelease_started_ns")
    end = receipt.get("owner_sync_returned_ns")
    if type(start) is not int or type(end) is not int or start > end:
        raise ValueError("invalid owner key-up bracket")
    return start, end


def temporal_relation(onset: tuple[int, int], release: tuple[int, int]) -> str:
    """Classify interval ordering without claiming causal linkage."""
    onset_start, onset_end = onset
    release_start, release_end = release
    if any(type(v) is not int for v in (*onset, *release)):
        raise ValueError("interval endpoints must be integers")
    if onset_start > onset_end or release_start > release_end:
        raise ValueError("interval is reversed")
    if onset_end < release_start:
        return "useful_outcome_observed_before_keyup_request"
    if onset_start > release_end:
        return "useful_outcome_observed_after_keyup_sync"
    return "temporally_overlapping_or_unresolved"
