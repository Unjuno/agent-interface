"""Independent full-field verifier for the retained V39 release result."""
import hashlib
import json
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
FREEZE_PATH = "research/doom/v39_release_trace_completeness_posthoc_a01_20261008/FREEZE.json"
FREEZE_COMMIT = "a0d0602b89b1f5a05f851728fe90684ec4bfeff5"
FREEZE_BLOB = "11ee4e82eccb79b4a377e5bbb42389acc44e3204"
FREEZE_SHA256 = "533b942ea7b7137c566288e93fda67968a55e4fa6292a05f05c1d5717efedf2e"
FROZEN_MAIN = "6149fc1856ce86de41b168de8ca12690347f524d"
PER_KEY_FIELDS = frozenset((
    "per_key", "key_release_ns", "keyup_ns", "key_release_attempts",
    "key_release_intervals_ns", "server_keyup_attempts",
))
PER_KEY_EVENT_TYPES = frozenset(("input_release_measurement", "input_release_transition"))


def _repo_root():
    for parent in HERE.parents:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("cannot locate repository root")


def _git(repo, *args, text=False):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=text)


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _check_blob(repo, commit, path, expected_blob, expected_sha256, expected_bytes):
    data = _git(repo, "show", f"{commit}:{path}")
    blob = _git(repo, "rev-parse", f"{commit}:{path}", text=True).strip()
    if (blob != expected_blob or hashlib.sha256(data).hexdigest() != expected_sha256 or
            len(data) != expected_bytes):
        raise ValueError(f"pinned input identity mismatch: {path}")
    return data


def load_pinned_inputs(repo=None):
    """Load evidence independently, checking the original freeze and every raw blob."""
    repo = Path(repo) if repo is not None else _repo_root()
    freeze_bytes = _check_blob(
        repo, FREEZE_COMMIT, FREEZE_PATH, FREEZE_BLOB, FREEZE_SHA256, 2326)
    freeze = json.loads(freeze_bytes)
    if freeze.get("frozen_main") != FROZEN_MAIN:
        raise ValueError("pinned freeze source commit mismatch")

    values = {}
    for path, spec in freeze["inputs"].items():
        data = _check_blob(repo, FROZEN_MAIN, path, spec["git_blob"],
                           spec["sha256"], spec["bytes"])
        values[path] = data
    events_path = next(path for path in values if path.endswith("events.jsonl"))
    owner_path = next(path for path in values if path.endswith("owner-events.json"))
    report_path = next(path for path in values if path.endswith("report.json"))
    prior_path = next(path for path in values if path.endswith("audit-v2.json"))
    prereg_path = next(path for path in values if path.endswith("_prereg.json"))
    events = [json.loads(row) for row in values[events_path].decode("utf-8").splitlines()
              if row.strip()]
    owner_events = json.loads(values[owner_path])
    report = json.loads(values[report_path])
    prior_audit = json.loads(values[prior_path])
    prereg = json.loads(values[prereg_path])
    return freeze, events, owner_events, report, prior_audit, prereg


def has_per_key_release_timestamps(owner_events):
    """Recognize the actual V12 terminal and explicit-key-up receipt field names."""
    for row in owner_events:
        if not isinstance(row, dict):
            continue
        terminal_attempts = row.get("key_release_attempts")
        if isinstance(terminal_attempts, dict):
            for receipt in terminal_attempts.values():
                attempts = receipt.get("attempts") if isinstance(receipt, dict) else None
                if isinstance(attempts, list) and any(
                        isinstance(attempt, dict) and all(
                            type(attempt.get(field)) is int for field in (
                                "keyrelease_started_ns", "sync_returned_ns",
                                "keymap_sampled_ns"))
                        for attempt in attempts):
                    return True
        explicit_attempts = row.get("server_keyup_attempts")
        if isinstance(explicit_attempts, list) and any(
                isinstance(attempt, dict) and all(
                    type(attempt.get(field)) is int for field in (
                        "keyrelease_started_ns", "sync_returned_ns",
                        "keymap_sampled_ns"))
                for attempt in explicit_attempts):
            return True
        intervals = row.get("key_release_intervals_ns")
        if isinstance(intervals, list) and any(
                isinstance(interval, dict) and
                isinstance(interval.get("interval_ns"), list) and
                len(interval["interval_ns"]) == 2 and
                all(type(value) is int for value in interval["interval_ns"])
                for interval in intervals):
            return True
    return False


def _unique_map(events, name):
    rows = [row for row in events if row.get("event") == name]
    ids = [row.get("id") for row in rows]
    if (any(not isinstance(identifier, str) or not identifier for identifier in ids) or
            len(ids) != len(set(ids))):
        raise ValueError(f"raw {name} IDs are not unique nonempty strings")
    return {row["id"]: row for row in rows}


def _empty_release(release):
    return (isinstance(release, dict) and release.get("verified") is True and
            release.get("keys_down") == [] and release.get("buttons_down") == [] and
            type(release.get("verified_ns")) is int)


def _expected_result(events, owner_events, report, prior_audit, prereg, freeze):
    if prereg.get("allocation_id") != freeze.get("allocation_id"):
        raise ValueError("freeze and preregistration allocation IDs differ")
    accepted = _unique_map(events, "accepted")
    terminals = _unique_map(events, "terminal")
    cancels = [row for row in events if row.get("event") == "cancel_requested"]
    cancel_ids = [row.get("id") for row in cancels]
    if (any(not isinstance(identifier, str) or not identifier for identifier in cancel_ids) or
            len(cancel_ids) != len(set(cancel_ids))):
        raise ValueError("raw cancel_requested IDs are not unique nonempty strings")
    release_events = [row for row in events if row.get("event") in
                      ("input_released", "input_release_unverified")]
    release_ids = [row.get("id") for row in release_events]
    if (any(not isinstance(identifier, str) or not identifier for identifier in release_ids) or
            len(release_ids) != len(set(release_ids))):
        raise ValueError("raw release event IDs are not unique nonempty strings")
    if set(release_ids) - set(terminals):
        raise ValueError("raw release event lacks a terminal")
    if set(accepted) != set(terminals):
        raise ValueError("raw accepted and terminal ID sets differ")
    if len(cancels) != 7 or prior_audit.get("formal_pass") is not True:
        raise ValueError("raw allocation cardinality or prior audit status changed")

    early = {row["id"]: row for row in release_events if row.get("event") == "input_released"}
    unverified = {row["id"]: row for row in release_events
                  if row.get("event") == "input_release_unverified"}
    if set(early) & set(unverified):
        raise ValueError("raw ID has both verified and unverified release events")
    held_ids = {row.get("id") for row in events if row.get("event") == "keys_held"}
    cancellation_rows = []

    for cancel in cancels:
        identifier = cancel["id"]
        terminal = terminals.get(identifier)
        if terminal is None:
            raise ValueError(f"cancel lacks terminal: {identifier}")
        terminal_release = terminal.get("release", {})
        if (terminal.get("status") != "cancelled" or not _empty_release(terminal_release) or
                type(cancel.get("requested_ns")) is not int or
                type(terminal.get("terminal_ns")) is not int or
                not cancel["requested_ns"] <= terminal_release["verified_ns"] <=
                terminal["terminal_ns"]):
            raise ValueError(f"cancel terminal release chronology invalid: {identifier}")

        cause = (terminal.get("interruption") or {}).get("record")
        active = identifier in held_ids
        row = {
            "id": identifier,
            "prior_keys_held_event": active,
            "interruption_owner_release": cause is not None,
            "input_release_event": identifier in early,
            "input_release_unverified_event": identifier in unverified,
            "cancel_requested_ns": cancel["requested_ns"],
            "terminal_ns": terminal["terminal_ns"],
            "terminal_owner_verified_ns": terminal_release["verified_ns"],
        }
        if cause is not None:
            if (cause.get("event") != "owner_release" or
                    cause.get("reason") != "cancelled" or not _empty_release(cause) or
                    type(cause.get("verified_ns")) is not int or
                    not cancel["requested_ns"] <= cause["verified_ns"] <= terminal["terminal_ns"]):
                raise ValueError(f"raw interruption owner receipt invalid: {identifier}")
            row["cause_owner_verified_ns"] = cause["verified_ns"]
            row["cancel_to_owner_verified_ms"] = (
                cause["verified_ns"] - cancel["requested_ns"]) / 1e6
            row["owner_verified_to_terminal_ms"] = (
                terminal["terminal_ns"] - cause["verified_ns"]) / 1e6
            if identifier in early:
                early_row = early[identifier]
                if (early_row.get("owner_release") != cause or
                        early_row.get("grants_input_authority") is not False or
                        type(early_row.get("published_ns")) is not int or
                        not cause["verified_ns"] <= early_row["published_ns"] <=
                        terminal["terminal_ns"]):
                    raise ValueError(f"raw early release receipt invalid: {identifier}")
                row["owner_verified_to_release_event_ms"] = (
                    early_row["published_ns"] - cause["verified_ns"]) / 1e6
        cancellation_rows.append(row)

    active_rows = [row for row in cancellation_rows
                   if row["prior_keys_held_event"] and row["interruption_owner_release"]]
    coverage = sum(row["input_release_event"] for row in active_rows)
    latencies = [row["cancel_to_owner_verified_ms"] for row in active_rows]
    score = report.get("score", {})
    outcome = {key: score.get(key) for key in
               ("kill_count", "death_count", "map_exit", "episode_finished")}
    if outcome["episode_finished"] is not False:
        raise ValueError("raw report no longer has the retained unfinished outcome")

    per_key_event_count = sum(
        row.get("event") in PER_KEY_EVENT_TYPES for row in events)
    has_per_key = has_per_key_release_timestamps(owner_events)
    terminal_only_covers = sum(
        row["id"].startswith("cover-") and row["interruption_owner_release"] and
        not row["input_release_event"] for row in active_rows)
    terminal_only_covers_text = {
        0: "no", 1: "one", 2: "two",
    }.get(terminal_only_covers, str(terminal_only_covers))
    decision = (
        "Aggregate owner/terminal release reconciles for all cancellations. "
        f"Early input_released coverage is {coverage}/{len(active_rows)} for prior-key-held "
        f"interrupted programs; {terminal_only_covers_text} cover interruptions appear only in "
        "terminal receipts. "
        "This is telemetry coverage evidence, not a failed release. "
        + ("Per-key release timestamps are present in owner records but do not establish "
           "physical-key duration or application consumption. Useful application feedback "
           "and task completion remain unmeasured." if has_per_key else
           "Per-key up time, useful application feedback, and task completion remain "
           "unmeasured.")
    )
    return {
        "schema": "map01-v39-release-trace-completeness-result-v2",
        "status": "PASS_TRACE_RECONCILIATION_WITH_EARLY_EVENT_GAP",
        "main_commit": freeze["frozen_main"],
        "allocation_id": freeze["allocation_id"],
        "prior_audit_formal_pass": prior_audit["formal_pass"],
        "accepted_terminal_ids_match": True,
        "cancel_requests": len(cancels),
        "cancelled_terminals_with_empty_verified_release": len(cancellation_rows),
        "cancellations_with_prior_keys_held": sum(
            row["prior_keys_held_event"] for row in cancellation_rows),
        "active_interruption_owner_receipts": len(active_rows),
        "active_interruption_receipts_with_input_released_event": coverage,
        "active_interruption_coverage": {
            "numerator": coverage, "denominator": len(active_rows)},
        "active_interruption_rows": active_rows,
        "all_cancellation_rows": cancellation_rows,
        "aggregate_cancel_to_owner_verified_ms": {
            "min": min(latencies), "max": max(latencies)},
        "input_release_event_rows": len(early),
        "input_release_unverified_event_rows": len(unverified),
        "per_key_release_measurement_events": per_key_event_count,
        "owner_release_has_per_key_timestamps": has_per_key,
        # No event in this frozen trace is an independently scored useful-feedback timestamp.
        "independent_useful_feedback_timestamp": False,
        "task_outcome": outcome,
        "decision": decision,
    }


def validate_result(result, events, owner_events, report, prior_audit, prereg, freeze):
    expected = _expected_result(
        events, owner_events, report, prior_audit, prereg, freeze)
    actual_fields = set(result) if isinstance(result, dict) else set()
    expected_fields = set(expected)
    if actual_fields != expected_fields:
        different = sorted(actual_fields ^ expected_fields)
        raise ValueError(f"result field set mismatch: {different}")
    for field, expected_value in expected.items():
        if _canonical(result[field]) != _canonical(expected_value):
            raise ValueError(f"{field}: supplied result does not match pinned raw evidence")
    return True


def validate_pinned_result(result, repo=None):
    freeze, events, owner_events, report, prior_audit, prereg = load_pinned_inputs(repo)
    return validate_result(
        result, events, owner_events, report, prior_audit, prereg, freeze)
