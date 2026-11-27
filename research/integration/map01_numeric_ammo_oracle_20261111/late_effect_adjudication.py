"""Adjudicate post-terminal input and application-effect evidence separately.

This module consumes retained records only. A neutral key-state sample is not
treated as proof that the application did or did not process a late event.
"""
from __future__ import annotations


def _integer(value):
    return type(value) is int and value >= 0


def adjudicate_late_effect(*, terminal_ns, horizon_end_ns, key_samples,
                           effect_observation, max_key_sample_gap_ns=20_000_000):
    """Classify late key-state recurrence and separately witnessed app effect.

    ``effect_observation`` must describe a complete, exact-generation observer
    covering the full terminal-to-horizon interval. Its ``events`` rows must
    carry ``monotonic_ns`` and an explicit boolean ``matches_task_effect``.
    Missing/incomplete app observation yields ``unknown`` rather than absence.
    """
    if not _integer(terminal_ns) or not _integer(horizon_end_ns) or horizon_end_ns < terminal_ns:
        raise ValueError("invalid terminal/horizon interval")
    if type(key_samples) is not list:
        raise ValueError("key_samples must be a list")

    valid_samples = []
    malformed = 0
    for row in key_samples:
        if type(row) is not dict:
            malformed += 1
            continue
        before, after, down = (row.get("monotonic_before_ns"),
                               row.get("monotonic_after_ns"),
                               row.get("w_key_down"))
        if not (_integer(before) and _integer(after) and before <= after
                and type(down) is bool and row.get("error_type") is None):
            malformed += 1
            continue
        valid_samples.append((before, after, down))
    valid_samples.sort(key=lambda item: (item[0], item[1]))

    if not _integer(max_key_sample_gap_ns) or max_key_sample_gap_ns == 0:
        raise ValueError("max_key_sample_gap_ns must be a positive integer")
    in_window = [row for row in valid_samples
                 if row[1] >= terminal_ns and row[0] <= horizon_end_ns]
    gaps = [b[0] - a[0] for a, b in zip(in_window, in_window[1:])]
    post_terminal = [row for row in in_window if row[0] >= terminal_ns]
    first_neutral_index = next((i for i, row in enumerate(post_terminal)
                                if row[2] is False), None)
    recurrence = None
    if first_neutral_index is not None:
        recurrence = any(row[2] is True for row in post_terminal[first_neutral_index + 1:]
                         if row[0] <= horizon_end_ns)
    key_trace_complete = (malformed == 0 and bool(in_window)
                          and in_window[0][0] <= terminal_ns
                          and in_window[-1][1] >= horizon_end_ns
                          and max(gaps, default=0) <= max_key_sample_gap_ns
                          and all(row[2] in (True, False) for row in in_window))

    observation = effect_observation if type(effect_observation) is dict else {}
    events = observation.get("events")
    observation_valid = (
        observation.get("complete") is True
        and observation.get("exact_generation") is True
        and _integer(observation.get("start_ns"))
        and _integer(observation.get("end_ns"))
        and observation["start_ns"] <= terminal_ns
        and observation["end_ns"] >= horizon_end_ns
        and observation.get("read_error") is None
        and type(events) is list
    )
    matching_events = []
    if observation_valid:
        for event in events:
            if type(event) is not dict or not _integer(event.get("monotonic_ns")):
                observation_valid = False
                matching_events = []
                break
            if (terminal_ns <= event["monotonic_ns"] <= horizon_end_ns
                    and type(event.get("matches_task_effect")) is bool):
                if event["matches_task_effect"]:
                    matching_events.append(event)
            elif terminal_ns <= event["monotonic_ns"] <= horizon_end_ns:
                observation_valid = False
                matching_events = []
                break

    effect_status = ("observed" if matching_events else
                     "absent" if observation_valid else "unknown")
    return {
        "status": "verified" if key_trace_complete and observation_valid else "not_verified",
        "interval": {"terminal_ns": terminal_ns, "horizon_end_ns": horizon_end_ns},
        "key_state": {
            "valid_sample_count": len(valid_samples),
            "malformed_sample_count": malformed,
            "post_terminal_sample_count": len(post_terminal),
            "max_observed_gap_ns": max(gaps, default=None),
            "max_allowed_gap_ns": max_key_sample_gap_ns,
            "trace_covers_interval": key_trace_complete,
            "neutral_sample_seen": first_neutral_index is not None,
            "down_recurrence_after_neutral": recurrence,
            "interpretation": "sampled key state only; does not establish application event delivery",
        },
        "application_effect": {
            "status": effect_status,
            "observer_valid": observation_valid,
            "matching_event_count": len(matching_events),
            "reason": None if observation_valid else "complete exact-generation horizon observer unavailable",
        },
    }
