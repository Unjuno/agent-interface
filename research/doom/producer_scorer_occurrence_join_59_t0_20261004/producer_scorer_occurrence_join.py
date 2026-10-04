"""Join acknowledged scorer updates to uniquely identified admitted key inputs.

The join is evidence plumbing only. It establishes neither causal attribution
nor application consumption, and requires run identity on every input stream.
"""
from __future__ import annotations

from occurrence_attribution import attribute_progress_events, normalize_releases


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


def _validate_sample_stream(samples: list[dict]) -> tuple[str, dict[int, dict]]:
    if not isinstance(samples, list) or not samples:
        raise ValueError("at least one acknowledged scorer sample is required")
    by_time = {}
    run_id = None
    previous_time = -1
    previous_sample_sequence = 0
    previous_update_sequence = 0
    previous_update_returned = -1
    previous_state = None
    previous_producer = None
    for row in samples:
        if type(row) is not dict or row.get("schema") != SAMPLE_SCHEMA:
            raise ValueError("invalid scorer sample schema")
        sample_ns = _integer(row.get("sample_ns"), "sample_ns")
        if sample_ns <= previous_time:
            raise ValueError("scorer sample clock must be strictly increasing")
        for counter in ("kill_count", "death_count"):
            _integer(row.get(counter), counter)
        for flag in ("episode_finished", "player_dead", "map_exit"):
            if type(row.get(flag)) is not bool:
                raise ValueError(f"{flag} must be bool")
        if row["map_exit"] and (not row["episode_finished"] or row["player_dead"]):
            raise ValueError("map_exit requires a finished episode and living player")
        state = (row["kill_count"], row["death_count"], row["episode_finished"],
                 row["player_dead"], row["map_exit"])
        producer = row.get("producer")
        if type(producer) is not dict:
            raise ValueError("sample lacks acknowledged producer provenance")
        current_run = _nonempty_string(producer, "run_id", "producer sample")
        if run_id is None:
            run_id = current_run
        elif current_run != run_id:
            raise ValueError("run_id mismatch across producer samples")

        sample_sequence = _integer(producer.get("sample_sequence"),
                                   "sample_sequence", minimum=1)
        update_sequence = _integer(producer.get("update_sequence"),
                                   "update_sequence", minimum=1)
        status = producer.get("observation_status")
        if sample_sequence != previous_sample_sequence + 1:
            raise ValueError("producer sample sequence must be strictly increasing by one")
        if previous_state is not None and previous_state[2] and state != previous_state:
            raise ValueError("terminal scorer state must remain unchanged")
        if status == "UPDATE_RETURNED":
            if previous_state is not None and previous_state[2]:
                raise ValueError("terminal repeat cannot claim a new engine update")
            if update_sequence != sample_sequence:
                raise ValueError("acknowledged update sequence must equal sample sequence")
            if update_sequence <= previous_update_sequence:
                raise ValueError("acknowledged update sequence must increase")
            tic_before = _integer(producer.get("tic_before"), "tic_before")
            tic_after = _integer(producer.get("tic_after"), "tic_after")
            if tic_after <= tic_before:
                raise ValueError("acknowledged engine tic must advance")
            started = _integer(producer.get("update_started_ns"), "update_started_ns")
            returned = _integer(producer.get("update_returned_ns"), "update_returned_ns")
            if not started <= returned <= sample_ns:
                raise ValueError("sample must follow its completed acknowledged update")
            if started < previous_update_returned:
                raise ValueError("producer update clocks must be monotonic")
        elif status == "TERMINAL_REPEAT_NO_UPDATE":
            if previous_state is None or not previous_state[2] or state != previous_state:
                raise ValueError("terminal repeat must repeat a prior terminal state")
            if update_sequence != previous_update_sequence:
                raise ValueError("terminal repeat must retain the last update sequence")
            if update_sequence == 0:
                raise ValueError("terminal repeat has no prior acknowledged update")
            returned = _integer(producer.get("update_returned_ns"), "update_returned_ns")
            if sample_ns < returned:
                raise ValueError("terminal repeat sample precedes update acknowledgment")
            for field in ("tic_before", "tic_after", "update_started_ns"):
                if producer.get(field) != previous_producer.get(field):
                    raise ValueError("terminal repeat must retain prior update metadata")
        else:
            raise ValueError("sample producer status is unavailable or unknown")

        by_time[sample_ns] = producer
        previous_time = sample_ns
        previous_sample_sequence = sample_sequence
        previous_update_sequence = update_sequence
        previous_state = state
        previous_producer = producer
        previous_update_returned = returned
    assert run_id is not None
    return run_id, by_time


def _require_same_run(rows: list[dict], source: str, run_id: str) -> None:
    if not isinstance(rows, list):
        raise ValueError(f"{source} rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError(f"{source} row must be an object")
        if _nonempty_string(row, "run_id", source) != run_id:
            raise ValueError(f"run_id mismatch across scorer and {source} records")


def attribute_acknowledged_events(
    samples: list[dict],
    events: list[dict],
    admissions: list[dict],
    raw_releases: list[dict],
    semantic_bindings: list[dict],
) -> list[dict]:
    """Require producer/action identity continuity, then use the frozen reducer.

    Each scorer event must land on exactly one acknowledged sample clock. The
    event is enriched from that sample; caller-provided producer metadata is
    rejected. Every admission, raw release, and semantic binding must carry the
    same run_id. The occurrence reducer then enforces unique active occurrence,
    matching owner/intent/key identities, action binding and release bounds.
    """
    run_id, producer_by_time = _validate_sample_stream(samples)
    _require_same_run(admissions, "admission", run_id)
    _require_same_run(raw_releases, "release", run_id)
    _require_same_run(semantic_bindings, "semantic binding", run_id)
    if not isinstance(events, list):
        raise ValueError("scorer events must be a list")

    enriched = []
    seen_event_sequences = set()
    for event in events:
        if type(event) is not dict or event.get("schema") != EVENT_SCHEMA:
            raise ValueError("invalid scorer event schema")
        sequence = _integer(event.get("event_sequence"), "event_sequence", minimum=1)
        if sequence in seen_event_sequences:
            raise ValueError("duplicate scorer event sequence")
        seen_event_sequences.add(sequence)
        observed_ns = _integer(event.get("observed_ns"), "observed_ns")
        producer = producer_by_time.get(observed_ns)
        if producer is None:
            raise ValueError("event must match exactly one acknowledged sample")
        if "producer" in event or "run_id" in event:
            raise ValueError("event producer identity must come from linked sample")
        enriched.append({
            **event,
            "run_id": run_id,
            "producer": {
                "run_id": producer["run_id"],
                "sample_sequence": producer["sample_sequence"],
                "update_sequence": producer["update_sequence"],
                "observation_status": producer["observation_status"],
            },
        })

    raw_release_rows = normalize_releases(raw_releases)
    attributed = attribute_progress_events(
        enriched, admissions, raw_release_rows, semantic_bindings)
    producer_by_event = {row["event_sequence"]: row["producer"] for row in enriched}
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
