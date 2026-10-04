"""Bind acknowledged scorer events to session-scoped possible input envelopes.

This adapter enforces the current session-envelope contract. It does not claim
that an input was held, caused progress, or was consumed by an application.
"""
from __future__ import annotations

from occurrence_attribution import attribute_positive_events, normalize_releases


SAMPLE_SCHEMA = "independent-progress-sample-v2"
EVENT_SCHEMA = "independent-progress-event-v2"


def _nonempty_string(row: dict, key: str, source: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{source} requires non-empty {key}")
    return value


def _integer(value, name: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def _validate_samples(samples: list[dict]) -> tuple[str, list[dict], dict[int, dict]]:
    if not isinstance(samples, list) or not samples:
        raise ValueError("at least one acknowledged scorer sample is required")
    run_id = None
    previous_time = -1
    previous_sample_sequence = 0
    previous_update_sequence = 0
    previous_update_returned = -1
    previous_state = None
    previous_producer = None
    session_samples = []
    producer_by_time = {}
    for source_row in samples:
        if type(source_row) is not dict or source_row.get("schema") != SAMPLE_SCHEMA:
            raise ValueError("invalid scorer sample schema")
        sample_ns = _integer(source_row.get("sample_ns"), "sample_ns")
        if sample_ns <= previous_time:
            raise ValueError("scorer sample clock must be strictly increasing")
        for counter in ("kill_count", "death_count"):
            _integer(source_row.get(counter), counter)
        for flag in ("episode_finished", "player_dead", "map_exit"):
            if type(source_row.get(flag)) is not bool:
                raise ValueError(f"{flag} must be bool")
        if source_row["map_exit"] and (
            not source_row["episode_finished"] or source_row["player_dead"]
        ):
            raise ValueError("map_exit requires finished episode and living player")
        state = (source_row["kill_count"], source_row["death_count"],
                 source_row["episode_finished"], source_row["player_dead"],
                 source_row["map_exit"])
        producer = source_row.get("producer")
        if type(producer) is not dict:
            raise ValueError("sample lacks acknowledged producer provenance")
        current_run = _nonempty_string(producer, "run_id", "producer sample")
        if run_id is None:
            run_id = current_run
        elif current_run != run_id:
            raise ValueError("producer run_id mismatch across samples")
        if "session_id" in source_row and source_row["session_id"] != current_run:
            raise ValueError("sample session_id does not match producer run_id")

        sample_sequence = _integer(producer.get("sample_sequence"),
                                   "sample_sequence", minimum=1)
        update_sequence = _integer(producer.get("update_sequence"),
                                   "update_sequence", minimum=1)
        if sample_sequence != previous_sample_sequence + 1:
            raise ValueError("producer sample sequence must increase by one")
        status = producer.get("observation_status")
        if previous_state is not None and previous_state[2] and state != previous_state:
            raise ValueError("terminal scorer state must remain unchanged")
        if status in ("UPDATE_RETURNED", "EXTERNAL_UPDATE_RETURNED"):
            if previous_state is not None and previous_state[2]:
                raise ValueError("terminal repeat cannot claim a new engine update")
            if update_sequence <= previous_update_sequence:
                raise ValueError("producer update sequence must increase")
            tic_before = _integer(producer.get("tic_before"), "tic_before")
            tic_after = _integer(producer.get("tic_after"), "tic_after")
            if tic_after <= tic_before:
                raise ValueError("acknowledged engine tic must advance")
            started = _integer(producer.get("update_started_ns"), "update_started_ns")
            returned = _integer(producer.get("update_returned_ns"), "update_returned_ns")
            if not started <= returned <= sample_ns or started < previous_update_returned:
                raise ValueError("sample must follow monotonic completed update clocks")
            if status == "EXTERNAL_UPDATE_RETURNED" and not source_row["episode_finished"]:
                raise ValueError("external update acknowledgment is terminal-only in V16")
        elif status == "TERMINAL_REPEAT_NO_UPDATE":
            if previous_state is None or not previous_state[2] or state != previous_state:
                raise ValueError("terminal repeat must repeat a prior terminal state")
            if update_sequence != previous_update_sequence or update_sequence == 0:
                raise ValueError("terminal repeat must retain the prior update sequence")
            returned = _integer(producer.get("update_returned_ns"), "update_returned_ns")
            if sample_ns < returned:
                raise ValueError("terminal repeat sample precedes update acknowledgment")
            for field in ("tic_before", "tic_after", "update_started_ns"):
                if producer.get(field) != previous_producer.get(field):
                    raise ValueError("terminal repeat must retain prior update metadata")
        else:
            raise ValueError("sample producer status is unavailable or unknown")

        tagged = dict(source_row, session_id=current_run)
        session_samples.append(tagged)
        producer_by_time[sample_ns] = producer
        previous_time = sample_ns
        previous_sample_sequence = sample_sequence
        previous_update_sequence = update_sequence
        previous_update_returned = returned
        previous_state = state
        previous_producer = producer
    assert run_id is not None
    return run_id, session_samples, producer_by_time


def _require_session(rows: list[dict], source: str, session_id: str) -> None:
    if not isinstance(rows, list):
        raise ValueError(f"{source} rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError(f"{source} row must be an object")
        if _nonempty_string(row, "session_id", source) != session_id:
            raise ValueError(f"session_id mismatch across scorer and {source} records")


def attribute_acknowledged_events(
    samples: list[dict],
    events: list[dict],
    admissions: list[dict],
    raw_releases: list[dict],
    semantic_bindings: list[dict],
) -> list[dict]:
    """Link events to exact acknowledged samples and the current envelope reducer.

    The producer run UUID supplies the scorer sample/event session identity.
    Owner-side records must already carry the exact same session_id; this
    function fails closed rather than tagging unrelated actuation rows.
    """
    session_id, session_samples, producer_by_time = _validate_samples(samples)
    _require_session(admissions, "admission", session_id)
    _require_session(raw_releases, "release", session_id)
    _require_session(semantic_bindings, "semantic binding", session_id)
    if not isinstance(events, list):
        raise ValueError("scorer events must be a list")

    enriched_events = []
    seen_sequences = set()
    for event in events:
        if type(event) is not dict or event.get("schema") != EVENT_SCHEMA:
            raise ValueError("invalid scorer event schema")
        sequence = _integer(event.get("event_sequence"), "event_sequence")
        if sequence in seen_sequences:
            raise ValueError("duplicate scorer event sequence")
        seen_sequences.add(sequence)
        observed_ns = _integer(event.get("observed_ns"), "observed_ns")
        producer = producer_by_time.get(observed_ns)
        if producer is None:
            raise ValueError("event must match exactly one acknowledged sample")
        if "producer" in event:
            raise ValueError("event producer identity must come from linked sample")
        if "session_id" in event and event["session_id"] != session_id:
            raise ValueError("event session_id does not match producer run")
        enriched_events.append({
            **event,
            "session_id": session_id,
            "producer": {
                "run_id": producer["run_id"],
                "sample_sequence": producer["sample_sequence"],
                "update_sequence": producer["update_sequence"],
                "observation_status": producer["observation_status"],
            },
        })

    releases = normalize_releases(raw_releases)
    attributed = attribute_positive_events(
        session_samples, enriched_events, admissions, releases, semantic_bindings)
    producer_by_event = {
        event["event_sequence"]: event["producer"] for event in enriched_events
    }
    return [
        {
            **row,
            "producer_run_id": producer_by_event[row["event_sequence"]]["run_id"],
            "producer_sample_sequence": producer_by_event[row["event_sequence"]]["sample_sequence"],
            "producer_update_sequence": producer_by_event[row["event_sequence"]]["update_sequence"],
            "causation_claimed": False,
        }
        for row in attributed
    ]
