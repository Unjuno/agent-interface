#!/usr/bin/env python3
"""Strict successor audit; v1 output remains retained as historical evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from audit import ONE_HOLD, SOURCE, audit as audit_v1


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def audit_v2(repo: Path) -> dict[str, Any]:
    result = audit_v1(repo)
    errors = list(result["errors"])
    holds: list[str] = []

    construction_events = _jsonl(repo / SOURCE / "construction02/out/session/events.jsonl")
    terminal_rows = [row for row in construction_events if row.get("event") == "terminal"]
    if len(terminal_rows) != 1 or terminal_rows[0].get("status") != "completed":
        holds.append("construction02_terminal_lifecycle_unobserved")

    one_hold_events = _jsonl(repo / ONE_HOLD / "out/session/events.jsonl")
    transitions = [row for row in one_hold_events if row.get("event") == "input_release_transition"]
    owner_rows = json.loads((repo / ONE_HOLD / "out/session/owner-events.json").read_text(encoding="utf-8"))
    keyups = [row for row in owner_rows if row.get("event") == "owner_explicit_keyup"]
    empty_releases = [row for row in owner_rows if row.get("event") == "owner_release" and row.get("reason") == "release"]

    if len(transitions) == len(keyups) == 1:
        transition, keyup = transitions[0], keyups[0]
        receipt = transition.get("owner_thread_keyup_receipt")
        if (
            not isinstance(receipt, dict)
            or receipt.get("operation") != "up"
            or receipt.get("server_sync_completed") is not True
            or keyup.get("operation") != "up"
            or keyup.get("server_sync_completed") is not True
            or receipt.get("operation") != keyup.get("operation")
            or receipt.get("server_sync_completed") != keyup.get("server_sync_completed")
        ):
            errors.append("one_hold_nested_keyup_semantics_mismatch")

        if len(empty_releases) != 1:
            errors.append("one_hold_empty_release_sample_count_mismatch")
        else:
            verified_ns = empty_releases[0].get("verified_ns")
            release_emit_ns = transition.get("emit_ns")
            if type(verified_ns) is not int or type(release_emit_ns) is not int or verified_ns <= release_emit_ns:
                errors.append("one_hold_empty_release_not_after_keyup_transition")
    else:
        errors.append("one_hold_keyup_order_inputs_missing")

    result["audit_v1"] = result.pop("audit")
    result["errors"] = errors
    result["holds"] = holds
    result["audit"] = (
        "FAIL_V16_LIFECYCLE_AUDIT" if errors else
        "HOLD_LIFECYCLE_TERMINAL_UNOBSERVED" if holds else
        "PASS_SCOPED_V16_LIFECYCLE"
    )
    result["v2_checks"] = {
        "construction02_terminal_rows": len(terminal_rows),
        "nested_keyup_requires_operation_up_and_server_sync": not any(
            error == "one_hold_nested_keyup_semantics_mismatch" for error in errors
        ),
        "verified_empty_sample_follows_release_transition": not any(
            error == "one_hold_empty_release_not_after_keyup_transition" for error in errors
        ),
    }
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    print(json.dumps(audit_v2(args.repo), indent=2, sort_keys=True))
