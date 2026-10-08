from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ALLOCATION = "MAP01-V6-RUNNER-CLOCK-CANCEL-59-T3V-20261002-01"
BASE = "4cf0a3dfde1219671b671bf0a9079a11dcb2e159"
EXPECTED = {
    "A-clock-before-cancel-within-lease": {"planner_wait_ms": 600, "clock_delay_ms": 400, "lease_ms": 2000},
    "B-lease-before-clock-return": {"planner_wait_ms": 600, "clock_delay_ms": 1600, "lease_ms": 1500},
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def audit_case(row, expected):
    errors = []
    for key, value in expected.items():
        if row.get(key) != value:
            errors.append("FROZEN_CASE_MISMATCH:" + key)
    if row.get("planner_end_ns") != row.get("clock_return_ns"):
        errors.append("CLOCK_RETURN_NOT_BOUND_TO_PLANNER_END")
    if row.get("terminal_release_verified") is not True:
        errors.append("RUNNER_RELEASE_RECEIPT_NOT_VERIFIED")
    fallback_id = row.get("runner_arm_summary", {}).get("fallback_id")
    events = row.get("events", [])
    cancels = [e for e in events if e.get("event") == "cancel_requested" and e.get("id") == fallback_id]
    terminals = [e for e in events if e.get("event") == "terminal" and e.get("id") == fallback_id]
    releases = [e for e in events if e.get("event") == "input_released" and e.get("id") == fallback_id]
    if len(cancels) != 1 or len(terminals) != 1 or len(releases) != 1:
        return errors + ["IDENTITY_EVENT_CARDINALITY"]
    cancel, terminal, release = cancels[0], terminals[0], releases[0]
    release_ns = release.get("release_ns")
    if release.get("verified") is not True or release_ns != row.get("release_ns"):
        errors.append("RELEASE_RECEIPT_MISMATCH")
    if terminal.get("release", {}).get("verified") is not True:
        errors.append("TERMINAL_RELEASE_NOT_VERIFIED")
    if terminal.get("terminal_ns", 0) < release_ns:
        errors.append("TERMINAL_PRECEDES_RELEASE")
    if row.get("name") == "A-clock-before-cancel-within-lease":
        if cancel.get("matched") is not True or row.get("cancel_observed_ns") is None:
            errors.append("A_CANCEL_NOT_MATCHED_AND_OBSERVED")
        if terminal.get("status") != "completed" or row.get("fallback_terminal_status") != "completed":
            errors.append("A_COOPERATIVE_TERMINAL_STATUS")
        if not (row.get("clock_return_ns", 0) <= cancel.get("requested_ns", 0)
                <= row.get("cancel_observed_ns", 0) <= release_ns <= terminal.get("terminal_ns", 0)):
            errors.append("A_EVENT_ORDER")
        timer_lag = release_ns - row.get("timer_expired_ns", 0)
        if not 350_000_000 <= timer_lag <= 2_000_000_000:
            errors.append("A_TIMER_RELEASE_BOUND")
        if release_ns - cancel.get("requested_ns", 0) > 50_000_000:
            errors.append("A_CANCEL_RELEASE_BOUND")
    elif row.get("name") == "B-lease-before-clock-return":
        deadline = row.get("planner_start_ns", 0) + expected["lease_ms"] * 1_000_000
        if terminal.get("status") != "expired" or row.get("fallback_terminal_status") != "expired":
            errors.append("B_LEASE_TERMINAL_STATUS")
        if not deadline <= release_ns <= deadline + 50_000_000:
            errors.append("B_LEASE_RELEASE_BOUND")
        if release_ns >= row.get("clock_return_ns", 0):
            errors.append("B_RELEASE_NOT_PRE_RETURN")
        if cancel.get("matched") is not False or cancel.get("requested_ns", 0) < row.get("clock_return_ns", 0):
            errors.append("B_LATE_CANCEL_NOT_UNMATCHED")
        if row.get("cancel_observed_ns") is not None:
            errors.append("B_CANCEL_OBSERVED_AFTER_LEASE_RELEASE")
        if not (release_ns <= terminal.get("terminal_ns", 0) <= row.get("clock_return_ns", 0)):
            errors.append("B_EVENT_ORDER")
    else:
        errors.append("UNDECLARED_CASE")
    return errors


def audit_payload(payload, freeze):
    errors = []
    if payload.get("allocation") != ALLOCATION or payload.get("base_commit") != BASE:
        errors.append("ALLOCATION_OR_BASE_MISMATCH")
    freeze_bytes = (HERE / "FREEZE.json").read_bytes()
    if payload.get("freeze_sha256") != sha256(freeze_bytes):
        errors.append("FREEZE_HASH_MISMATCH")
    if payload.get("candidate_invocations") != 1 or payload.get("retries") != 0:
        errors.append("INVOCATION_COUNT_MISMATCH")
    if payload.get("package_sha256") != freeze.get("package_sha256"):
        errors.append("PACKAGE_HASH_SET_MISMATCH")
    if payload.get("source_manifest") != freeze.get("source_manifest"):
        errors.append("SOURCE_MANIFEST_MISMATCH")
    cases = payload.get("cases", [])
    if len(cases) != 2:
        errors.append("CASE_COUNT_MISMATCH")
    names = [item.get("row", {}).get("name") for item in cases]
    if set(names) != set(EXPECTED) or len(set(names)) != 2:
        errors.append("CASE_SET_MISMATCH")
    for item in cases:
        row = item.get("row", {})
        name = row.get("name")
        if name not in EXPECTED:
            continue
        case_errors = audit_case(row, EXPECTED[name])
        if item.get("gate_errors") != [] or case_errors:
            errors.extend(f"{name}:{error}" for error in (case_errors or item.get("gate_errors", [])))
    if payload.get("candidate_gate_errors") != []:
        errors.append("CANDIDATE_REPORTED_GATE_FAILURE")
    if payload.get("status") != "PASS_CANDIDATE_GATES":
        errors.append("CANDIDATE_STATUS_NOT_PASS")
    return {"status": "PASS_AUDIT" if not errors else "FAIL_AUDIT",
            "allocation": ALLOCATION, "candidate_invocations": 1, "auditor_invocations": 1,
            "retries": 0, "case_count": len(cases), "errors": errors}


def main():
    raw_path = HERE / "results" / "candidate_raw.json"
    freeze_path = HERE / "FREEZE.json"
    try:
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
        freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
        result = audit_payload(payload, freeze)
    except Exception as exc:
        result = {"status": "FAIL_AUDIT", "allocation": ALLOCATION,
                  "candidate_invocations": "not-invoked-by-auditor", "auditor_invocations": 1,
                  "retries": 0, "case_count": 0, "errors": ["AUDITOR_EXCEPTION:" + repr(exc)]}
    path = HERE / "results" / "audit_result.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
