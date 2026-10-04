#!/usr/bin/env python3
"""Independent read-only audit of the retained V16 full-main constructions."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


SOURCE = Path("research/doom/v16_fullmain_59_4d74_20261004")
ONE_HOLD = Path("research/doom/v16_one_hold_59_4d74_20261004")


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _audit_manifest(source: Path) -> tuple[list[str], int]:
    errors: list[str] = []
    raw = _json(source / "FILES.sha256.json")
    rows = raw if isinstance(raw, list) else raw["files"]
    listed = {row["path"]: row for row in rows}
    actual = {
        path.relative_to(source).as_posix(): path
        for path in source.rglob("*")
        if path.is_file() and path.name != "FILES.sha256.json" and "__pycache__" not in path.parts and path.suffix != ".pyc"
    }
    if set(listed) != set(actual):
        errors.append("manifest_file_set_mismatch")
    for name in sorted(set(listed) & set(actual)):
        blob = actual[name].read_bytes()
        row = listed[name]
        if len(blob) != row.get("bytes") or hashlib.sha256(blob).hexdigest() != row.get("sha256"):
            errors.append(f"manifest_hash_mismatch:{name}")
    return errors, len(listed)


def audit(repo: Path) -> dict[str, Any]:
    source = repo / SOURCE
    errors: list[str] = []
    manifest_errors, manifest_count = _audit_manifest(source)
    errors.extend(manifest_errors)

    first = source / "construction01/out"
    first_events = _jsonl(first / "session/events.jsonl")
    first_delivered = _jsonl(first / "session/delivered.jsonl")
    first_names = [row.get("event") for row in first_events]
    first_delivered_names = [row.get("event") for row in first_delivered]
    first_exit = _json(first / "exit.json")
    if first_exit.get("exit_code") != 0:
        errors.append("construction01_process_exit_not_zero")
    if "ready" not in first_names or "typed_observation" not in first_names:
        errors.append("construction01_missing_ready_observation")
    if "command" in first_names or "command" in first_delivered_names or "post_control_score" in first_names:
        errors.append("construction01_stop_was_not_preserved")

    second = source / "construction02/out"
    result = _json(second / "RESULT.json")
    events = _jsonl(second / "session/events.jsonl")
    event_names = [row.get("event") for row in events]
    commands = [row for row in events if row.get("event") == "command"]
    scores = [row for row in events if row.get("event") == "post_control_score"]
    delivered = _jsonl(second / "session/delivered.jsonl")
    delivered_commands = [row for row in delivered if row.get("event") == "command"]
    samples = _jsonl(second / "session/scorer-samples.jsonl")
    updates = _jsonl(second / "session/scorer-client-updates.jsonl")
    summary = _json(second / "session/scorer-summary.json")
    owner = _json(second / "session/owner-events.json")
    if result.get("status") != "PASS_NO_ACTION_FULLMAIN_FINISH_SCOPED":
        errors.append("construction02_result_disposition_mismatch")
    if event_names.count("ready") != 1 or len(commands) != 1 or commands[0].get("command", {}).get("op") != "finish":
        errors.append("construction02_finish_sequence_mismatch")
    if len(delivered_commands) != 1 or delivered_commands[0].get("command", {}).get("op") != "finish":
        errors.append("construction02_finish_delivery_mismatch")
    if len(scores) != 1 or scores[0].get("scorer_refresh_calls_after_control") != 1:
        errors.append("construction02_post_control_score_mismatch")
    if result.get("executor_acceptances") != 0 or any(row.get("event") == "submit" for row in events):
        errors.append("construction02_unexpected_input_admission")
    if len(samples) != 2 or [row.get("payload", {}).get("producer", {}).get("sample_sequence") for row in samples] != [1, 2]:
        errors.append("construction02_sample_sequence_mismatch")
    if len(updates) != 2 or any(row.get("controller_visible") is not False for row in samples + updates):
        errors.append("construction02_scorer_provenance_mismatch")
    if summary.get("sample_count") != 2 or summary.get("event_count") != 0 or summary.get("event_summary", {}).get("positive_useful_events") != 0:
        errors.append("construction02_useful_event_summary_mismatch")
    if not isinstance(owner, list) or len(owner) != 1:
        errors.append("construction02_owner_release_row_mismatch")
    else:
        release = owner[0]
        if release.get("event") != "owner_release" or release.get("verified") is not True or release.get("keys_down") or release.get("buttons_down"):
            errors.append("construction02_owner_release_not_verified_empty")
        if scores and release.get("verified_ns", 0) < scores[0].get("emit_ns", 0):
            errors.append("construction02_release_timestamp_precedes_post_control_score")

    one_hold_source = repo / ONE_HOLD
    one_hold_manifest_errors, one_hold_manifest_count = _audit_manifest(one_hold_source)
    errors.extend(f"one_hold_{error}" for error in one_hold_manifest_errors)
    one_hold = one_hold_source / "out"
    one_hold_result = _json(one_hold / "RESULT.json")
    one_hold_events = _jsonl(one_hold / "session/events.jsonl")
    one_hold_admissions = [row for row in one_hold_events if row.get("event") == "input_admission"]
    one_hold_transitions = [row for row in one_hold_events if row.get("event") == "input_release_transition"]
    one_hold_owner = _json(one_hold / "session/owner-events.json")
    one_hold_keyups = [row for row in one_hold_owner if row.get("event") == "owner_explicit_keyup"]
    one_hold_empty_releases = [row for row in one_hold_owner if row.get("event") == "owner_release" and row.get("reason") == "release"]
    one_hold_summary = _json(one_hold / "session/scorer-summary.json")
    one_hold_samples = _jsonl(one_hold / "session/scorer-samples.jsonl")
    admission_identity = one_hold_admissions[0] if len(one_hold_admissions) == 1 else {}
    transition_identity = one_hold_transitions[0] if len(one_hold_transitions) == 1 else {}
    keyup_receipt = transition_identity.get("owner_thread_keyup_receipt", {})
    identity_fields = ("owner_id", "intent_token", "id", "step", "key")
    identity_join_verified = (
        bool(admission_identity)
        and all(admission_identity.get(key) not in (None, "") for key in identity_fields)
        and all(admission_identity.get(key) == transition_identity.get(key) for key in identity_fields)
        and all(admission_identity.get(key) == keyup_receipt.get(key) for key in ("owner_id", "intent_token", "key"))
        and transition_identity.get("release_batch_identifier") == admission_identity.get("id")
        and transition_identity.get("release_batch_step") == admission_identity.get("step")
    )
    if one_hold_result.get("status") != "PASS_ONE_HOLD_COMPOSITION_SCOPED" or one_hold_result.get("accepted") != 1 or one_hold_result.get("completed") != 1:
        errors.append("one_hold_result_disposition_mismatch")
    if len(one_hold_admissions) != 1 or len(one_hold_transitions) != 1 or len(one_hold_keyups) != 1:
        errors.append("one_hold_input_release_rows_mismatch")
    if len(one_hold_keyups) == 1:
        keyup = one_hold_keyups[0]
        if keyup.get("physical_verification_authoritative") is not False or keyup.get("server_sync_completed") is not True:
            errors.append("one_hold_keyup_authority_fields_mismatch")
    if len(one_hold_transitions) == 1:
        transition = one_hold_transitions[0]
        if transition.get("physical_verification_authoritative") is not False or transition.get("release_batch_complete") is not True:
            errors.append("one_hold_transition_authority_fields_mismatch")
        if transition.get("physical_key_measurement") is not None:
            errors.append("one_hold_unexpected_physical_edge_measurement")
    if not identity_join_verified:
        errors.append("one_hold_identity_join_mismatch")
    if len(one_hold_empty_releases) != 1 or one_hold_empty_releases[0].get("verified") is not True or one_hold_empty_releases[0].get("keys_down") or one_hold_empty_releases[0].get("buttons_down"):
        errors.append("one_hold_verified_empty_release_mismatch")
    if one_hold_summary.get("sample_count") != 17 or len(one_hold_samples) != 17 or one_hold_summary.get("event_count") != 0 or one_hold_summary.get("event_summary", {}).get("positive_useful_events") != 0:
        errors.append("one_hold_feedback_summary_mismatch")
    if one_hold_result.get("frame_changed") is not True:
        errors.append("one_hold_changed_frame_missing")

    return {
        "audit": "PASS_SCOPED_V16_LIFECYCLE" if not errors else "FAIL_V16_LIFECYCLE_AUDIT",
        "errors": errors,
        "manifest_files": manifest_count,
        "construction01": {
            "exit_code": first_exit.get("exit_code"),
            "ready_observed": "ready" in first_names,
            "typed_observation_observed": "typed_observation" in first_names,
            "finish_delivered": "command" in first_names,
            "post_control_score": "post_control_score" in first_names,
        },
        "construction02": {
            "finish_commands": len(commands),
            "finish_deliveries": len(delivered_commands),
            "executor_acceptances": result.get("executor_acceptances"),
            "scorer_samples": len(samples),
            "scorer_events": summary.get("event_count"),
            "positive_useful_events": summary.get("event_summary", {}).get("positive_useful_events"),
            "owner_close_verified_empty": bool(owner) and owner[0].get("verified") is True and not owner[0].get("keys_down") and not owner[0].get("buttons_down"),
            "post_score_precedes_close_release": bool(scores and owner) and scores[0].get("emit_ns", 0) < owner[0].get("verified_ns", 0),
        },
        "one_hold": {
            "manifest_files": one_hold_manifest_count,
            "accepted": one_hold_result.get("accepted"),
            "input_admissions": len(one_hold_admissions),
            "release_transitions": len(one_hold_transitions),
            "owner_keyup_rows": len(one_hold_keyups),
            "physical_release_authoritative": one_hold_keyups[0].get("physical_verification_authoritative") if one_hold_keyups else None,
            "owner_sync_completed": one_hold_keyups[0].get("server_sync_completed") if one_hold_keyups else None,
            "identity_join_verified": identity_join_verified,
            "physical_edge_measurement_present": bool(one_hold_transitions and one_hold_transitions[0].get("physical_key_measurement")),
            "release_transition_follows_owner_sync": bool(one_hold_transitions and one_hold_keyups) and one_hold_transitions[0].get("emit_ns", 0) >= one_hold_keyups[0].get("owner_sync_returned_ns", 0),
            "verified_empty_owner_release": bool(one_hold_empty_releases) and one_hold_empty_releases[0].get("verified") is True,
            "scorer_samples": len(one_hold_samples),
            "positive_useful_events": one_hold_summary.get("event_summary", {}).get("positive_useful_events"),
            "frame_changed": one_hold_result.get("frame_changed"),
        },
        "scope": "Two no-action and one single-hold protocol records only; no gameplay qualification, physical per-key release timing, positive useful feedback, threat response, recovery, or causal task-effect qualification.",
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    print(json.dumps(audit(args.repo), indent=2, sort_keys=True))
