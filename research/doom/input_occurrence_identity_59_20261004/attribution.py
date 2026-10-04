"""Session-bound possible-envelope association using per-key occurrence IDs."""
from __future__ import annotations

from collections import defaultdict

SAMPLE_SCHEMA = "independent-progress-sample-v2"
EVENT_SCHEMA = "independent-progress-event-v2"


def normalize_releases(rows):
    """Flatten explicit key-up and V13 cancellation receipts without guessing."""
    result = []
    for row in rows:
        if type(row) is not dict:
            continue
        receipt = row
        if row.get("event") in ("input_release_transition", "input_release"):
            receipt = row.get("owner_thread_keyup_receipt")
        if type(receipt) is dict and receipt.get("event") == "owner_explicit_keyup":
            result.append({
                "session_id": row.get("session_id"),
                "program_id": row.get("id"),
                "step": row.get("step"),
                "input_occurrence_id": receipt.get("input_occurrence_id"),
                "owner_id": receipt.get("owner_id"),
                "intent_token": receipt.get("intent_token"),
                "keycode": receipt.get("keycode"),
                "key": receipt.get("key"),
                "release_started_ns": receipt.get("owner_keyrelease_started_ns"),
                "release_finished_ns": receipt.get("owner_sync_returned_ns"),
                "release_verified": (
                    receipt.get("server_sync_completed") is True
                    and receipt.get("cancel_requested_after_sync") is False
                ),
                "source": "explicit_keyup",
            })
        elif row.get("event") in ("input_released", "input_release_unverified"):
            owner_release = row.get("owner_release")
            if type(owner_release) is not dict:
                continue
            for interval in owner_release.get("key_release_intervals_ns", []):
                if type(interval) is not dict:
                    continue
                bounds = interval.get("interval_ns")
                if type(bounds) is not list or len(bounds) != 2:
                    continue
                result.append({
                    "session_id": row.get("session_id"),
                    "program_id": row.get("id"),
                    "step": interval.get("step"),
                    "input_occurrence_id": interval.get("input_occurrence_id"),
                    "owner_id": interval.get("owner_id"),
                    "intent_token": interval.get("intent_token"),
                    "keycode": interval.get("keycode"),
                    "key": interval.get("key"),
                    "release_started_ns": bounds[0],
                    "release_finished_ns": bounds[1],
                    "release_verified": (
                        row.get("event") == "input_released"
                        and owner_release.get("verified") is True
                    ),
                    "source": "cancellation_batch",
                })
    return result


def _session_ids(sources):
    seen = []
    for name, rows in sources:
        if not isinstance(rows, list):
            raise ValueError(f"{name}s must be a list")
        for row in rows:
            if type(row) is not dict:
                raise ValueError(f"{name} row must be an object")
            value = row.get("session_id")
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} row requires non-empty session_id")
            seen.append(value)
    if seen and any(value != seen[0] for value in seen[1:]):
        raise ValueError("session_id mismatch across scorer and actuation records")
    return seen[0] if seen else None


def attribute_positive_events(samples, events, admissions, releases, bindings):
    """Return possible intent envelopes, never unique-key or causal attribution.

    A progress event is bracketed by its immediately preceding scorer sample
    and the sample at which the event was observed. Admission-to-release/XSync
    bounds can describe only a possible input envelope. Strict coverage does
    not prove that a key remained down or caused the progress event.

    V12 records admitted_ns before issuing XTest KeyPress and input_ack_ns
    after XSync returns. The admission bound is therefore the earliest
    possible dispatch time; the later ACK does not prove that dispatch waited
    until acknowledgment.
    """
    session_id = _session_ids((
        ("sample", samples), ("event", events), ("admission", admissions),
        ("release", releases), ("action binding", bindings),
    ))
    sample_times = []
    sample_by_time = {}
    for row in samples:
        if row.get("schema") != SAMPLE_SCHEMA:
            raise ValueError("invalid scorer sample schema")
        time_ns = row.get("sample_ns")
        if type(time_ns) is not int or time_ns < 0:
            raise ValueError("sample_ns must be a non-negative integer")
        if sample_times and time_ns <= sample_times[-1]:
            raise ValueError("scorer sample clock must be strictly increasing")
        sample_times.append(time_ns)
        sample_by_time[time_ns] = row

    admissions_by_occurrence = {}
    for row in admissions:
        occurrence_id = row.get("input_occurrence_id")
        if not isinstance(occurrence_id, str) or not occurrence_id:
            raise ValueError("admission requires input_occurrence_id")
        admissions_by_occurrence.setdefault(occurrence_id, []).append(row)

    releases_by_occurrence = {}
    for row in releases:
        occurrence_id = row.get("input_occurrence_id")
        if not isinstance(occurrence_id, str) or not occurrence_id:
            raise ValueError("release requires input_occurrence_id")
        releases_by_occurrence.setdefault(occurrence_id, []).append(row)

    bindings_by_action = {}
    for row in bindings:
        key = (row.get("program_id"), row.get("step"))
        bindings_by_action.setdefault(key, []).append(row)

    intervals = []
    for occurrence_id, admission_rows in admissions_by_occurrence.items():
        if len(admission_rows) != 1:
            raise ValueError("duplicate admission occurrence ID")
        release_rows = releases_by_occurrence.get(occurrence_id, [])
        if len(release_rows) != 1:
            raise ValueError("each admission requires exactly one release occurrence")
        admission, release = admission_rows[0], release_rows[0]
        intent_token = admission.get("intent_token")
        if not isinstance(intent_token, str) or not intent_token.strip():
            raise ValueError("admission requires non-empty intent_token")
        identity_fields = ("session_id", "owner_id", "intent_token", "keycode")
        if any(admission.get(name) != release.get(name) for name in identity_fields):
            raise ValueError("release identity does not match its admission")
        if release.get("program_id") not in (None, admission.get("id")):
            raise ValueError("release program ID does not match its admission")
        start = admission.get("admitted_ns")
        ack = admission.get("input_ack_ns")
        release_start = release.get("release_started_ns")
        release_end = release.get("release_finished_ns")
        if any(type(value) is not int or value < 0
               for value in (start, ack, release_start, release_end)):
            raise ValueError("admission and release bounds must be non-negative integers")
        if not (start <= ack <= release_start <= release_end):
            raise ValueError("input occurrence timestamps are not ordered")
        if type(release.get("release_verified")) is not bool:
            raise ValueError("release_verified must be bool")
        action_rows = bindings_by_action.get((admission.get("id"), admission.get("step")), [])
        if len(action_rows) != 1:
            raise ValueError("admission requires exactly one semantic action binding")
        binding = action_rows[0]
        semantic_hash = binding.get("semantic_action_sha256")
        if (binding.get("session_id") != session_id
                or not isinstance(semantic_hash, str) or len(semantic_hash) != 64
                or any(char not in "0123456789abcdef" for char in semantic_hash)):
            raise ValueError("invalid session-bound semantic action binding")
        intervals.append({
            "input_occurrence_id": occurrence_id,
            "intent_token": admission["intent_token"],
            "key": admission.get("key"),
            "program_id": admission["id"],
            "step": admission["step"],
            "semantic_action_sha256": semantic_hash,
            "start": start,
            "end": release_end,
            "release_verified": release["release_verified"],
        })
    if set(releases_by_occurrence) != set(admissions_by_occurrence):
        raise ValueError("release has no matching admission occurrence")

    output = []
    seen_sequences = set()
    for event in events:
        if event.get("schema") != EVENT_SCHEMA:
            raise ValueError("invalid scorer event schema")
        sequence = event.get("event_sequence")
        observed = event.get("observed_ns")
        if type(sequence) is not int or sequence < 0 or sequence in seen_sequences:
            raise ValueError("invalid or duplicate scorer event sequence")
        seen_sequences.add(sequence)
        if type(observed) is not int or observed not in sample_by_time:
            raise ValueError("event timestamp must identify a retained scorer sample")
        if event.get("controller_visible") is not False:
            raise ValueError("scorer event must remain controller-invisible")
        if event.get("polarity") != "positive" or event.get("useful") is not True:
            continue
        position = sample_times.index(observed)
        base = {"session_id": session_id, "event_sequence": sequence,
                "kind": event.get("kind"), "causal_attribution": "NOT_ESTABLISHED"}
        if position == 0:
            output.append({**base, "detection_interval_ns": None,
                           "status": "UNRESOLVED",
                           "reason": "no_prior_scorer_sample",
                           "possible_intent_tokens": [],
                           "possible_occurrence_ids": [],
                           "semantic_action_sha256s": []})
            continue
        lower, upper = sample_times[position - 1], observed
        possible = [row for row in intervals
                    if row["start"] <= upper and
                    (not row["release_verified"] or row["end"] >= lower)]
        tokens = sorted({row["intent_token"] for row in possible})
        result = {**base, "detection_interval_ns": [lower, upper],
                  "possible_intent_tokens": tokens,
                  "possible_occurrence_ids": sorted(
                      row["input_occurrence_id"] for row in possible),
                  "semantic_action_sha256s": sorted({
                      row["semantic_action_sha256"] for row in possible})}
        status, reason = "UNRESOLVED", "no_complete_verified_intent_coverage"
        if len(tokens) > 1:
            status, reason = "AMBIGUOUS", "multiple_intents_intersect_detection_interval"
        elif len(tokens) == 1:
            rows = [row for row in possible if row["intent_token"] == tokens[0]]
            if any(not row["release_verified"] for row in rows):
                reason = "unverified_release_boundary"
            elif any(row["start"] == lower or row["end"] == upper for row in rows):
                reason = "endpoint_tie_without_authenticated_order"
            else:
                usable = sorted((row["start"], row["end"]) for row in rows
                                if row["release_verified"]
                                and row["end"] > lower and row["start"] < upper)
                cursor = lower
                for start, end in usable:
                    if start > cursor:
                        break
                    cursor = max(cursor, end)
                    if cursor > upper:
                        break
                if cursor > upper:
                    status, reason = ("SINGLE_POSSIBLE_INTENT_ENVELOPE",
                                      "one_verified_envelope_strictly_spans_detection_interval")
        output.append({**result, "status": status, "reason": reason,
                       "intent_token": None})
    return output
