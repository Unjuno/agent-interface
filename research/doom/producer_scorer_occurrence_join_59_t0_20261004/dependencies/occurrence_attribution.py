"""Fail-closed scorer-to-admitted-key-occurrence temporal association."""

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
                "input_occurrence_id": receipt.get("input_occurrence_id"),
                "owner_id": receipt.get("owner_id"),
                "intent_token": receipt.get("intent_token"),
                "keycode": receipt.get("keycode"),
                "release_started_ns": receipt.get("owner_keyrelease_started_ns"),
                "release_finished_ns": receipt.get("owner_sync_returned_ns"),
                "source": "explicit_keyup",
                "verified": (
                    receipt.get("server_sync_completed") is True
                    and receipt.get("cancel_requested_after_sync") is False
                ),
                "program_id": row.get("id"),
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
                    "input_occurrence_id": interval.get("input_occurrence_id"),
                    "owner_id": interval.get("owner_id"),
                    "intent_token": interval.get("intent_token"),
                    "keycode": interval.get("keycode"),
                    "release_started_ns": bounds[0],
                    "release_finished_ns": bounds[1],
                    "source": "cancellation_batch",
                    "program_id": row.get("id"),
                    "verified": owner_release.get("verified"),
                })
    return result


def attribute_progress_events(progress_events, admissions, releases,
                              semantic_bindings):
    """Associate an event only with a uniquely active occurrence and action hash.

    The interval `[input_ack_ns, release_started_ns)` is the only interval used
    as an admitted-key window. A scorer timestamp inside a key-up request/XSync
    bracket is explicitly unresolved. A result is temporal association, never
    causation or proof of application consumption.
    """
    admissions_by_id = {}
    for row in admissions:
        if type(row) is not dict:
            continue
        occurrence_id = row.get("input_occurrence_id")
        if not isinstance(occurrence_id, str) or not occurrence_id:
            continue
        admissions_by_id.setdefault(occurrence_id, []).append(row)

    releases_by_id = {}
    for row in releases:
        if type(row) is not dict:
            continue
        occurrence_id = row.get("input_occurrence_id")
        if not isinstance(occurrence_id, str) or not occurrence_id:
            continue
        releases_by_id.setdefault(occurrence_id, []).append(row)

    bindings = {}
    for row in semantic_bindings:
        if type(row) is not dict:
            continue
        key = (row.get("program_id"), row.get("step"))
        bindings.setdefault(key, []).append(row)

    output = []
    for event in progress_events:
        base = {"event_sequence": event.get("event_sequence") if type(event) is dict else None}
        if (type(event) is not dict or event.get("schema") != EVENT_SCHEMA
                or event.get("controller_visible") is not False
                or type(event.get("observed_ns")) is not int):
            output.append({**base, "status": "unresolved_invalid_progress_event"})
            continue
        now = event["observed_ns"]
        active = []
        boundary = []
        invalid = []
        for occurrence_id, occurrences in admissions_by_id.items():
            if len(occurrences) != 1:
                invalid.append(occurrence_id)
                continue
            admission = occurrences[0]
            matching_releases = releases_by_id.get(occurrence_id, [])
            if len(matching_releases) != 1:
                invalid.append(occurrence_id)
                continue
            release = matching_releases[0]
            required_match = all((
                isinstance(admission.get("id"), str) and bool(admission["id"]),
                type(admission.get("step")) is int and admission["step"] >= 0,
                isinstance(admission.get("owner_id"), str) and bool(admission["owner_id"]),
                isinstance(admission.get("intent_token"), str) and bool(admission["intent_token"]),
                type(admission.get("keycode")) is int and admission["keycode"] > 0,
                release.get("owner_id") == admission.get("owner_id"),
                release.get("intent_token") == admission.get("intent_token"),
                release.get("keycode") == admission.get("keycode"),
                release.get("program_id", admission.get("id")) == admission.get("id"),
                type(admission.get("input_ack_ns")) is int,
                type(release.get("release_started_ns")) is int,
                type(release.get("release_finished_ns")) is int,
                admission["input_ack_ns"] <= release["release_started_ns"]
                <= release["release_finished_ns"],
                type(release.get("verified", True)) is bool,
                release.get("verified", True) is True,
            ))
            if not required_match:
                invalid.append(occurrence_id)
                continue
            action_rows = bindings.get((admission.get("id"), admission.get("step")), [])
            if len(action_rows) != 1:
                invalid.append(occurrence_id)
                continue
            semantic_hash = action_rows[0].get("semantic_action_sha256")
            if (not isinstance(semantic_hash, str) or len(semantic_hash) != 64
                    or any(char not in "0123456789abcdef" for char in semantic_hash)):
                invalid.append(occurrence_id)
                continue
            if admission["input_ack_ns"] <= now < release["release_started_ns"]:
                active.append((occurrence_id, admission, action_rows[0]))
            elif release["release_started_ns"] <= now < release["release_finished_ns"]:
                boundary.append(occurrence_id)

        if invalid:
            output.append({**base, "status": "unresolved_invalid_or_nonunique_lifecycle",
                           "occurrence_ids": sorted(set(invalid))})
        elif boundary:
            output.append({**base, "status": "unresolved_release_boundary",
                           "occurrence_ids": sorted(boundary)})
        elif len(active) == 1:
            occurrence_id, admission, binding = active[0]
            output.append({**base, "status": "unique_temporal_occurrence",
                           "input_occurrence_id": occurrence_id,
                           "program_id": admission["id"], "step": admission["step"],
                           "semantic_action_sha256": binding["semantic_action_sha256"],
                           "causation_claimed": False})
        elif len(active) > 1:
            output.append({**base, "status": "ambiguous_multiple_active_occurrences",
                           "occurrence_ids": sorted(item[0] for item in active)})
        else:
            output.append({**base, "status": "unresolved_no_active_occurrence"})
    return output
