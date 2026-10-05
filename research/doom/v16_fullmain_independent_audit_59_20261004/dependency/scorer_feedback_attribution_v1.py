"""Fail-closed temporal association of independent positive events to input intents.

This utility does not infer causation. It only reports an intent when verified
per-key input intervals cover the complete scorer detection interval and no
other intent could overlap that interval.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any


SAMPLE_SCHEMA = "independent-progress-sample-v2"
EVENT_SCHEMA = "independent-progress-event-v2"


def _nonnegative_int(value: Any, name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _validated_samples(samples: list[dict]) -> list[int]:
    times = []
    for row in samples:
        if not isinstance(row, dict) or row.get("schema") != SAMPLE_SCHEMA:
            raise ValueError("invalid scorer sample schema")
        times.append(_nonnegative_int(row.get("sample_ns"), "sample_ns"))
    if any(right <= left for left, right in zip(times, times[1:])):
        raise ValueError("scorer sample clock must be strictly increasing")
    return times


def _validated_intervals(intervals: list[dict]) -> list[dict]:
    output = []
    seen = set()
    for row in intervals:
        if not isinstance(row, dict):
            raise ValueError("actuation interval must be an object")
        token = row.get("intent_token")
        key = row.get("key")
        if not isinstance(token, str) or not token or not isinstance(key, str) or not key:
            raise ValueError("actuation interval requires intent_token and key")
        # Admission precedes the side effect; it is a conservative lower
        # bound for possible held-input time, unlike an after-the-fact ACK.
        start = _nonnegative_int(row.get("admitted_ns"), "admitted_ns")
        end = _nonnegative_int(row.get("release_sync_ns"), "release_sync_ns")
        if end < start:
            raise ValueError("release_sync_ns precedes down_ack_ns")
        if type(row.get("release_verified")) is not bool:
            raise ValueError("release_verified must be bool")
        identity = (token, key, start, end)
        if identity in seen:
            raise ValueError("duplicate per-key actuation interval")
        seen.add(identity)
        output.append({
            "intent_token": token,
            "key": key,
            "start": start,
            "end": end,
            "release_verified": row["release_verified"],
        })
    return output


def _covers_bracket(intervals: list[dict], lower: int, upper: int) -> bool:
    """Check that a verified same-intent interval union spans (lower, upper]."""
    usable = sorted(
        (row["start"], row["end"])
        for row in intervals
        if row["release_verified"] and row["end"] > lower and row["start"] <= upper
    )
    cursor = lower
    for start, end in usable:
        if start > cursor:
            return False
        cursor = max(cursor, end)
        if cursor >= upper:
            return True
    return False


def attribute_positive_events(
    samples: list[dict], events: list[dict], intervals: list[dict]
) -> list[dict]:
    """Return conservative event-to-intent temporal associations.

    Each positive event is bracketed by its immediately preceding scorer sample
    and its own observed sample. A unique result requires a single intent token
    to cover that entire interval with verified per-key bounds; overlap by a
    different token is ambiguous. Partial, missing, or unverified coverage is
    unresolved. The output explicitly leaves causal attribution unestablished.
    """
    times = _validated_samples(samples)
    sample_positions = {time_ns: index for index, time_ns in enumerate(times)}
    action_rows = _validated_intervals(intervals)
    by_intent: dict[str, list[dict]] = defaultdict(list)
    for row in action_rows:
        by_intent[row["intent_token"]].append(row)

    output = []
    seen_sequences = set()
    for event in events:
        if not isinstance(event, dict) or event.get("schema") != EVENT_SCHEMA:
            raise ValueError("invalid scorer event schema")
        sequence = _nonnegative_int(event.get("event_sequence"), "event_sequence")
        if sequence in seen_sequences:
            raise ValueError("duplicate scorer event sequence")
        seen_sequences.add(sequence)
        observed = _nonnegative_int(event.get("observed_ns"), "observed_ns")
        if event.get("polarity") != "positive" or event.get("useful") is not True:
            continue
        if event.get("controller_visible") is not False:
            raise ValueError("scorer event must remain controller-invisible")
        position = sample_positions.get(observed)
        if position is None:
            raise ValueError("event sample is absent from scorer sample stream")

        if position == 0:
            output.append({
                "event_sequence": sequence,
                "kind": event.get("kind"),
                "detection_interval_ns": None,
                "status": "UNRESOLVED",
                "reason": "no_prior_scorer_sample",
                "possible_intent_tokens": [],
                "intent_token": None,
                "causal_attribution": "NOT_ESTABLISHED",
            })
            continue

        lower = times[position - 1]
        upper = observed
        intersecting: dict[str, list[dict]] = defaultdict(list)
        for row in action_rows:
            # A non-authoritative release timestamp cannot exclude a held key
            # after that timestamp; preserve it as a possible overlap.
            possible = row["start"] <= upper and (
                not row["release_verified"] or row["end"] > lower
            )
            if possible:
                intersecting[row["intent_token"]].append(row)

        tokens = sorted(intersecting)
        status = "UNRESOLVED"
        reason = "no_complete_verified_intent_coverage"
        intent_token = None
        if len(tokens) > 1:
            status = "AMBIGUOUS"
            reason = "multiple_intents_intersect_detection_interval"
        elif len(tokens) == 1:
            token = tokens[0]
            rows = intersecting[token]
            if any(not row["release_verified"] for row in rows):
                reason = "unverified_release_boundary"
            elif _covers_bracket(rows, lower, upper):
                status = "TEMPORALLY_UNIQUE"
                reason = "one_verified_intent_covers_full_detection_interval"
                intent_token = token

        output.append({
            "event_sequence": sequence,
            "kind": event.get("kind"),
            "detection_interval_ns": [lower, upper],
            "status": status,
            "reason": reason,
            "possible_intent_tokens": tokens,
            "intent_token": intent_token,
            "causal_attribution": "NOT_ESTABLISHED",
        })
    return output
