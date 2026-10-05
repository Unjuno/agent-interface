"""Project unambiguous same-step V4/batch key receipts into release measurements.

Cross-step holds, repeated admissions for one identity, and lease renewal across
the pair need stronger admission custody; they remain unready in this helper.
This offline projection does not establish application consumption.
"""


def _is_int(value):
    return type(value) is int


def _identity(row):
    identity = tuple(row.get(name) for name in
                     ("id", "step", "key", "owner_id", "intent_token"))
    if (not all(type(value) is str and value for value in
                (identity[0], identity[2], identity[3], identity[4]))
            or not _is_int(identity[1]) or identity[1] < 0):
        return None
    return identity


def _valid_pair(admission, release):
    # The key DOWN producer emits input_admission without an operation field.
    if (admission.get("event") != "input_admission"
            or ("operation" in admission and admission["operation"] != "down")):
        return False
    if release.get("event") != "input_release_transition" or release.get("operation") != "up":
        return False
    identity = _identity(admission)
    if identity is None or identity != _identity(release):
        return False
    if (release.get("release_batch_schema") != "input-release-batch-v3"
            or release.get("release_batch_identifier") != admission.get("id")
            or not _is_int(release.get("release_batch_step"))
            or release.get("release_batch_step") != admission.get("step")
            or release.get("release_batch_complete") is not True
            or not _is_int(release.get("release_batch_size"))
            or not _is_int(release.get("release_batch_position"))
            or release.get("backend_owned_before_release") is not True
            or release.get("ordinary_release_candidate") is not True
            or not _is_int(release.get("owner_thread_keyup_receipt_count"))
            or release.get("owner_thread_keyup_receipt_count") != 1
            or release.get("owner_thread_keyup_history_complete") is not True
            or release.get("owner_thread_keyup_verified") is not True
            or release.get("owner_transition_verified") is not True
            or ("owner_sample_after_batch_available" in release
                and release["owner_sample_after_batch_available"] is not True)
            or release.get("owner_sample_ordered_after_batch") is not True
            or release.get("owner_identity_matches_after_batch") is not True
            or release.get("intent_token_matches_after_batch") is not True
            or release.get("owner_thread_keyup_verified_after_batch") is not True
            or release.get("owned_keycodes_after_batch") != []
            or release.get("physical_verification_authoritative") is not False):
        return False
    receipt = release.get("owner_thread_keyup_receipt")
    if not isinstance(receipt, dict) or receipt.get("event") != "owner_explicit_keyup":
        return False
    batch_key_order = receipt.get("release_batch_key_order")
    if (receipt.get("operation") != "up"
            or receipt.get("key") != identity[2]
            or receipt.get("owner_id") != identity[3]
            or receipt.get("intent_token") != identity[4]
            or not _is_int(release.get("valid_until_ns"))
            or not _is_int(receipt.get("valid_until_ns"))
            or not _is_int(admission.get("valid_until_ns"))
            or admission["valid_until_ns"] != release["valid_until_ns"]
            or receipt.get("valid_until_ns") != release.get("valid_until_ns")
            or receipt.get("server_sync_completed") is not True
            or receipt.get("server_keyup_verified") is not True
            or receipt.get("server_key_down_after_keyup") is not False
            or receipt.get("key_state_source") != "x11_query_keymap"
            or receipt.get("physical_verification_authoritative") is not False
            or receipt.get("cancel_requested_after_sync") is not False):
        return False
    if (not _is_int(receipt.get("release_batch_initial_up_count"))
            or receipt["release_batch_initial_up_count"] != release["release_batch_size"]
            or type(batch_key_order) is not list
            or len(batch_key_order) != release["release_batch_size"]
            or any(type(key) is not str or not key for key in batch_key_order)
            or not 0 <= release["release_batch_position"] < len(batch_key_order)
            or batch_key_order[release["release_batch_position"]] != identity[2]):
        return False
    times = [admission.get("admitted_ns"), admission.get("input_ack_ns"),
             release.get("release_call_started_ns"),
             receipt.get("owner_keyrelease_started_ns"),
             receipt.get("owner_sync_returned_ns"),
             receipt.get("owner_keymap_sampled_ns"),
             release.get("release_call_returned_ns"),
             release.get("owner_sample_after_started_ns"),
             release.get("owner_sample_after_finished_ns")]
    if (not all(_is_int(value) for value in times) or times != sorted(times)
            or release["release_call_started_ns"] >= release["valid_until_ns"]):
        return False
    attempts = receipt.get("server_keyup_attempts")
    count = receipt.get("server_keyup_attempt_count")
    if (type(attempts) is not list or not _is_int(count) or count != len(attempts)
            or count < 1 or count > 3):
        return False
    prior_sample = None
    prior_down_state = None
    for index, attempt in enumerate(attempts, 1):
        if not isinstance(attempt, dict):
            return False
        start, sync, sample = (attempt.get("keyrelease_started_ns"),
                               attempt.get("sync_returned_ns"),
                               attempt.get("keymap_sampled_ns"))
        if (not _is_int(attempt.get("attempt")) or attempt["attempt"] != index
                or not all(_is_int(t) for t in (start, sync, sample))
                or not start <= sync <= sample
                or type(attempt.get("server_key_down_before")) is not bool
                or type(attempt.get("server_key_down_after")) is not bool
                or (prior_sample is not None and prior_sample > start)
                or (prior_down_state is not None
                    and attempt["server_key_down_before"] is not prior_down_state)
                or (index == 1 and attempt["server_key_down_before"] is not True)):
            return False
        prior_sample = sample
        prior_down_state = attempt["server_key_down_after"]
    return (attempts[0]["keyrelease_started_ns"] == times[3]
            and attempts[-1]["sync_returned_ns"] == times[4]
            and attempts[-1]["keymap_sampled_ns"] == times[5]
            and attempts[-1]["server_key_down_after"] is False)


def project(records):
    """Return ready only when every admission/release has one strict matching pair."""
    admissions = [row for row in records if isinstance(row, dict)
                  and row.get("event") == "input_admission"]
    releases = [row for row in records if isinstance(row, dict)
                and row.get("event") == "input_release_transition"]
    if not admissions or len(admissions) != len(releases):
        return {"measurement_ready": False, "rows": []}
    by_identity = {}
    for admission in admissions:
        key = _identity(admission)
        if key is None or key in by_identity:
            return {"measurement_ready": False, "rows": []}
        by_identity[key] = admission
    projected = []
    batch_positions = {}
    for release in releases:
        # Consume the identity: one release cannot stand in for a different key.
        admission = by_identity.pop(_identity(release), None)
        if admission is None or not _valid_pair(admission, release):
            return {"measurement_ready": False, "rows": []}
        batch = (release["owner_id"], release["intent_token"],
                 release["release_batch_identifier"], release["release_batch_step"])
        batch_positions.setdefault(batch, []).append(release)
        receipt = release["owner_thread_keyup_receipt"]
        projected.append({
            "event": "input_release_measurement",
            "id": admission["id"], "step": admission["step"],
            "key": admission["key"], "owner_id": admission["owner_id"],
            "intent_token": admission["intent_token"],
            "admitted_ns": admission["admitted_ns"],
            "input_ack_ns": admission["input_ack_ns"],
            "release_call_started_ns": release["release_call_started_ns"],
            "owner_keyrelease_started_ns": receipt["owner_keyrelease_started_ns"],
            "owner_sync_returned_ns": receipt["owner_sync_returned_ns"],
            "owner_keymap_sampled_ns": receipt["owner_keymap_sampled_ns"],
            "release_call_returned_ns": release["release_call_returned_ns"],
            "application_consumption": "unobserved",
            "physical_verification_authoritative": False,
        })
    if by_identity:
        return {"measurement_ready": False, "rows": []}
    for batch_rows in batch_positions.values():
        sizes = {row["release_batch_size"] for row in batch_rows}
        indexes = [row["release_batch_position"] for row in batch_rows]
        if (len(sizes) != 1 or sorted(indexes) != list(range(len(batch_rows)))
                or next(iter(sizes)) != len(batch_rows)):
            return {"measurement_ready": False, "rows": []}
        ordered_rows = sorted(batch_rows, key=lambda row: row["release_batch_position"])
        previous_initial_sync = None
        for row in ordered_rows:
            first_attempt = row["owner_thread_keyup_receipt"]["server_keyup_attempts"][0]
            if (previous_initial_sync is not None
                    and previous_initial_sync > first_attempt["keyrelease_started_ns"]):
                return {"measurement_ready": False, "rows": []}
            previous_initial_sync = first_attempt["sync_returned_ns"]
    return {"measurement_ready": True, "rows": projected}
