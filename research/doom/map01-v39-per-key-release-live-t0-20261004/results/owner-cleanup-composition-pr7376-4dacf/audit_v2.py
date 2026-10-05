#!/usr/bin/env python3
"""Raw-only follow-up audit for the retained owner-cleanup composition record."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
RAW_PATH = ROOT / "candidate.raw.json"
OUTPUT_PATH = ROOT / "audit_v2.json"


def evaluate(raw: object) -> dict[str, bool]:
    checks: dict[str, bool] = {}
    if type(raw) is not dict:
        return {"raw_object": False}

    events = raw.get("events")
    events = events if type(events) is list else []
    admissions = [row for row in events
                  if type(row) is dict and row.get("event") == "input_admission"]
    releases = [row for row in events
                if type(row) is dict and row.get("event") == "input_release_transition"]
    owner_records = raw.get("owner_events")
    owner_records = owner_records if type(owner_records) is list else []
    cleanups = [row for row in owner_records
                if type(row) is dict and row.get("event") == "owner_release"]

    checks["one_admission_and_release"] = (
        len(admissions) == 1 and admissions[0].get("key") == "space"
        and len(releases) == 1 and releases[0].get("key") == "space"
        and releases[0].get("operation") == "up")
    checks["one_verified_cancel_cleanup"] = (
        len(cleanups) == 1 and cleanups[0].get("reason") == "cancelled"
        and cleanups[0].get("verified") is True
        and cleanups[0].get("keys_down") == []
        and cleanups[0].get("buttons_down") == [])

    if len(releases) == 1 and len(cleanups) == 1:
        release = releases[0]
        cleanup = cleanups[0]
        started = release.get("release_call_started_ns")
        returned = release.get("release_call_returned_ns")
        verified = cleanup.get("verified_ns")
        interval_valid = (
            type(started) is int and type(returned) is int
            and started <= returned)
        checks["release_call_interval_ordered"] = interval_valid
        checks["cleanup_timestamp_inside_release_bracket"] = (
            interval_valid and type(verified) is int
            and started <= verified <= returned)
        checks["cleanup_flag_agrees_with_timestamp"] = (
            release.get("owner_cleanup_intervened") is True
            and release.get("owner_release_history_complete") is True)
        checks["snapshot_preceded_cleanup"] = (
            release.get("cancel_requested_at_request") is False)
        checks["fail_closed_transition_publication"] = (
            release.get("ordinary_release_candidate") is False
            and release.get("owner_transition_verified") is False
            and release.get("owned_keycodes_after_batch") == []
            and release.get("release_batch_size") == 1
            and release.get("release_batch_position") == 0
            and release.get("grants_input_authority") is False
            and release.get("physical_verification_authoritative") is False)
    else:
        checks.update({
            "release_call_interval_ordered": False,
            "cleanup_timestamp_inside_release_bracket": False,
            "cleanup_flag_agrees_with_timestamp": False,
            "snapshot_preceded_cleanup": False,
            "fail_closed_transition_publication": False,
        })

    checks["one_press_and_release"] = raw.get("xtest_events") == [[2, 38], [3, 38]]
    checks["no_key_left_down"] = raw.get("down_after") == []
    return checks


def mutation_controls(raw: object) -> list[dict[str, object]]:
    if type(raw) is not dict:
        return []
    cases: list[dict[str, object]] = []

    def add(name: str, mutate) -> None:
        altered = copy.deepcopy(raw)
        mutate(altered)
        checks = evaluate(altered)
        cases.append({"name": name, "rejected": not all(checks.values())})

    def release_of(d):
        return next(row for row in d["events"]
                    if row.get("event") == "input_release_transition")

    def cleanup_of(d):
        return next(row for row in d["owner_events"]
                    if row.get("event") == "owner_release")

    add("cleanup_before_release_call", lambda d: cleanup_of(d).__setitem__(
        "verified_ns", release_of(d)["release_call_started_ns"] - 1))
    add("cleanup_after_release_return", lambda d: cleanup_of(d).__setitem__(
        "verified_ns", release_of(d)["release_call_returned_ns"] + 1))
    add("inverted_release_interval", lambda d: release_of(d).__setitem__(
        "release_call_returned_ns", release_of(d)["release_call_started_ns"] - 1))
    add("missing_cleanup_timestamp", lambda d: cleanup_of(d).pop("verified_ns"))
    add("boolean_cleanup_timestamp", lambda d: cleanup_of(d).__setitem__(
        "verified_ns", True))
    add("duplicate_cleanup_receipt", lambda d: d["owner_events"].append(
        copy.deepcopy(cleanup_of(d))))
    add("cleanup_intervened_flag_cleared", lambda d: release_of(d).__setitem__(
        "owner_cleanup_intervened", False))
    add("transition_claims_verified", lambda d: release_of(d).__setitem__(
        "owner_transition_verified", True))
    return cases


def main(raw_path: Path = RAW_PATH) -> int:
    raw_bytes = raw_path.read_bytes()
    try:
        raw = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        report = {"schema": "v39-owner-cleanup-composition-audit-v2",
                  "status": "FAIL_PARSE", "error": type(exc).__name__}
        print(json.dumps(report, sort_keys=True))
        return 1

    checks = evaluate(raw)
    mutations = mutation_controls(raw)
    errors = []
    if not all(checks.values()):
        errors.append("baseline_checks_failed")
    if len(mutations) != 8 or any(item["rejected"] is not True for item in mutations):
        errors.append("mutation_controls_not_all_rejected")
    report = {
        "schema": "v39-owner-cleanup-composition-audit-v2",
        "status": "PASS_TEMPORAL_RECEIPT_BINDING_SCOPED" if not errors else "FAIL",
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "auditor_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "parent_audit_status": "PASS_CONSTRUCTION_OWNER_CLEANUP_FAIL_CLOSED",
        "baseline_checks_passed": sum(checks.values()),
        "baseline_checks_total": len(checks),
        "checks": checks,
        "mutation_controls": mutations,
        "mutation_controls_rejected": sum(item["rejected"] is True for item in mutations),
        "mutation_controls_total": len(mutations),
        "candidate_invocations": 0,
        "auditor_invocations": 1,
        "retries": 0,
        "errors": errors,
        "scope": ("Raw-only re-audit of one deterministic fake-Xlib/XTest construction record. "
                  "The verified owner-cleanup timestamp is checked inside the recorded "
                  "release-call bracket; this is not live X11, physical input, application "
                  "effect, task-control, or latency evidence."),
    }
    OUTPUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else RAW_PATH))
