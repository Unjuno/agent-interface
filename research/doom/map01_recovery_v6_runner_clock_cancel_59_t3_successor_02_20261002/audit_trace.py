"""Independent raw-only auditor for Issue #6252 T3U."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess

BASE = "97afcb82f90616589801a256893f886010ed6d27"
ALLOCATION = "MAP01-V6-RUNNER-CLOCK-CANCEL-59-T3U-20261002-01"
HERE = pathlib.Path(__file__).resolve().parent
SOURCES = {
    "v6_runner": "research/doom/map01_recovery_cover_mechanism_v6_runner.py",
    "executor": "research/live_control/executor_v10.py",
    "lease": "research/live_control/lease.py",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def audit(raw: dict, freeze: dict, freeze_bytes: bytes) -> dict:
    errors: list[str] = []
    if raw.get("schema") != "map01-v6-runner-shared-clock-t3u-v1": errors.append("schema")
    if raw.get("allocation") != ALLOCATION: errors.append("allocation")
    if raw.get("base_commit") != BASE: errors.append("base_commit")
    if raw.get("candidate_invocations") != 1 or raw.get("retries") != 0: errors.append("invocations_or_retries")
    if raw.get("freeze_sha256") != sha(freeze_bytes): errors.append("freeze_sha256")
    if raw.get("frozen_candidate_sha256") != freeze.get("candidate_sha256"): errors.append("candidate_binding")
    if raw.get("frozen_auditor_sha256") != freeze.get("auditor_sha256"): errors.append("auditor_binding")
    if sha((HERE / "run_experiment.py").read_bytes()) != freeze.get("candidate_sha256"): errors.append("candidate_file_sha")
    if sha(pathlib.Path(__file__).read_bytes()) != freeze.get("auditor_sha256"): errors.append("auditor_file_sha")
    if sha((HERE / "test_audit_trace.py").read_bytes()) != freeze.get("tests_sha256"): errors.append("test_file_sha")

    manifest = raw.get("source_manifest", {})
    frozen_manifest = freeze.get("source_manifest", {})
    for name, path in SOURCES.items():
        try:
            src = subprocess.check_output(["git", "show", f"{BASE}:{path}"])
            blob = git("rev-parse", f"{BASE}:{path}")
        except subprocess.CalledProcessError:
            errors.append(f"source_missing:{name}")
            continue
        for label, item in (("raw", manifest.get(name, {})), ("freeze", frozen_manifest.get(name, {}))):
            if item.get("path") != path: errors.append(f"{label}_source_path:{name}")
            if item.get("git_blob") != blob: errors.append(f"{label}_source_blob:{name}")
            if item.get("sha256") != sha(src): errors.append(f"{label}_source_sha:{name}")

    try:
        v6 = subprocess.check_output(["git", "show", f"{BASE}:{SOURCES['v6_runner']}"]).decode()
        end_pos = v6.index("planner_end_ns = session.runtime_clock()")
        cancel_pos = v6.index('session.send({"op": "cancel", "id": fallback_id})', end_pos)
        if not end_pos < cancel_pos: errors.append("source_order")
    except (subprocess.CalledProcessError, ValueError):
        errors.append("source_order_missing")

    expected = {
        "A-clock-before-cancel-within-lease": (600, 400, 2000),
        "B-lease-before-clock-return": (600, 1600, 1500),
    }
    case_rows = raw.get("cases")
    if not isinstance(case_rows, list) or len(case_rows) != 2:
        errors.append("case_count")
        case_rows = []
    rows = {row.get("case"): row for row in case_rows}
    if len(rows) != 2: errors.append("case_names_or_duplicates")
    for name, config in expected.items():
        row = rows.get(name)
        if row is None:
            errors.append(f"missing_case:{name}")
            continue
        if (row.get("planner_wait_ms"), row.get("clock_delay_ms"), row.get("lease_ms")) != config:
            errors.append(f"config:{name}")
        start, timer, returned, end, release = (row.get(key) for key in
            ("planner_start_ns", "timer_expired_ns", "clock_return_ns", "planner_end_ns", "release_ns"))
        summary = row.get("runner_arm_summary", {})
        fallback_id = summary.get("fallback_id")
        if end != returned: errors.append(f"returned_value_binding:{name}")
        if summary.get("planner_window", {}).get("end_ns") != end: errors.append(f"summary_end:{name}")
        events = row.get("events", [])
        terminal = [e for e in events if e.get("event") == "terminal" and e.get("id") == fallback_id]
        receipt = [e for e in events if e.get("event") == "input_released" and e.get("id") == fallback_id]
        cancel = [e for e in events if e.get("event") == "cancel_requested" and e.get("id") == fallback_id]
        if len(terminal) != 1 or terminal[0].get("release", {}).get("verified") is not True:
            errors.append(f"terminal_verified_release:{name}")
        if (len(receipt) != 1 or receipt[0].get("verified") is not True
                or receipt[0].get("release_ns") != release):
            errors.append(f"release_receipt:{name}")
        if len(cancel) != 1: errors.append(f"cancel_event_count:{name}")
        if row.get("terminal_release_verified") is not True: errors.append(f"runner_release_summary:{name}")
        if not all(type(value) is int for value in (start, timer, returned, end, release)):
            errors.append(f"integer_timestamps:{name}")
            continue
        if name.startswith("A-"):
            if len(cancel) == 1 and cancel[0].get("matched") is not True: errors.append("A_cancel_not_matched")
            if type(row.get("cancel_observed_ns")) is not int: errors.append("A_cancel_not_observed")
            else:
                if not 350 <= (release - timer) / 1e6 <= 2000: errors.append("A_timer_release_window")
                if abs(release - end) > 50_000_000: errors.append("A_release_after_clock")
                if abs(release - row["cancel_observed_ns"]) > 50_000_000: errors.append("A_release_after_cancel")
            if terminal and terminal[0].get("status") != "cancelled": errors.append("A_terminal_status")
            if end <= timer: errors.append("A_end_not_after_timer")
        else:
            deadline = start + 1_500_000_000
            if abs(release - deadline) > 50_000_000: errors.append("B_release_not_at_lease_deadline")
            if release >= returned: errors.append("B_release_not_before_clock_return")
            if row.get("cancel_observed_ns") is not None: errors.append("B_cancel_observed")
            if len(cancel) == 1 and cancel[0].get("matched") is not False: errors.append("B_cancel_was_matched")
            if terminal and terminal[0].get("status") != "expired": errors.append("B_terminal_status")

    return {"schema": "map01-v6-runner-shared-clock-audit-t3u-v1", "allocation": ALLOCATION,
        "status": "PASS_RUNNER_CLOCK_DELAY_SCOPED" if not errors else "FAIL_AUDIT",
        "cases_checked": len(case_rows), "errors": errors, "retries": 0,
        "limits": ["mock session/backend only", "no OS pipe or process", "no transport or natural latency estimate",
                   "no game, GUI, input, or physical occupancy claim"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, type=pathlib.Path)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    args = parser.parse_args()
    freeze_bytes = (HERE / "FREEZE.json").read_bytes()
    result = audit(json.loads(args.raw.read_text()), json.loads(freeze_bytes), freeze_bytes)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "PASS_RUNNER_CLOCK_DELAY_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
