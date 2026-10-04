#!/usr/bin/env python3
"""Independent read-only audit of the retained V16 full-main constructions."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


SOURCE = Path("research/doom/v16_fullmain_59_4d74_20261004")


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def audit(repo: Path) -> dict[str, Any]:
    source = repo / SOURCE
    errors: list[str] = []
    manifest = _json(source / "FILES.sha256.json")
    rows = manifest if isinstance(manifest, list) else manifest["files"]
    listed = {row["path"]: row for row in rows}
    actual: dict[str, Path] = {}
    for path in source.rglob("*"):
        if path.is_file() and path.name != "FILES.sha256.json":
            actual[path.relative_to(source).as_posix()] = path
    if set(listed) != set(actual):
        errors.append("manifest_file_set_mismatch")
    for name in sorted(set(listed) & set(actual)):
        blob = actual[name].read_bytes()
        row = listed[name]
        if len(blob) != row.get("bytes") or hashlib.sha256(blob).hexdigest() != row.get("sha256"):
            errors.append(f"manifest_hash_mismatch:{name}")

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

    return {
        "audit": "PASS_SCOPED_V16_FULLMAIN_NO_ACTION" if not errors else "FAIL_V16_FULLMAIN_AUDIT",
        "errors": errors,
        "manifest_files": len(listed),
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
        "scope": "No-action protocol composition only; no gameplay, admitted input, per-key physical release timing, independent positive feedback, threat response, recovery, or task-effect qualification.",
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    print(json.dumps(audit(args.repo), indent=2, sort_keys=True))
