"""Independent raw-only audit for the frozen v6 runner timing allocation."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess

BASE = "279679a33f6029c6e13eca6be51890d8bebb25e7"
ALLOCATION = "MAP01-V6-RUNNER-CLOCK-CANCEL-59-T3S-20261002-01"
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


def audit(raw: dict, freeze: dict) -> dict:
    errors: list[str] = []
    if raw.get("schema") != "map01-v6-runner-clock-cancel-t3-successor-v1": errors.append("schema")
    if raw.get("allocation") != ALLOCATION: errors.append("allocation")
    if raw.get("base_commit") != BASE: errors.append("base_commit")
    if raw.get("candidate_invocations") != 1 or raw.get("retries") != 0: errors.append("invocation_count")
    if raw.get("freeze_sha256") != sha((HERE / "FREEZE.json").read_bytes()): errors.append("freeze_hash")
    if raw.get("frozen_candidate_sha256") != freeze.get("candidate_sha256"): errors.append("candidate_hash_binding")
    if raw.get("frozen_auditor_sha256") != freeze.get("auditor_sha256"): errors.append("auditor_hash_binding")
    if sha((HERE / "run_experiment.py").read_bytes()) != freeze.get("candidate_sha256"): errors.append("candidate_file_hash")
    if sha(pathlib.Path(__file__).read_bytes()) != freeze.get("auditor_sha256"): errors.append("auditor_file_hash")

    expected = {
        "v6_runner": "research/doom/map01_recovery_cover_mechanism_v6_runner.py",
        "executor": "research/live_control/executor_v10.py",
        "lease": "research/live_control/lease.py",
    }
    manifest = raw.get("source_manifest", {})
    frozen_manifest = freeze.get("source_manifest", {})
    for name, path in expected.items():
        item = manifest.get(name, {})
        frozen_item = frozen_manifest.get(name, {})
        try:
            src = subprocess.check_output(["git", "show", f"{BASE}:{path}"])
            blob = git("rev-parse", f"{BASE}:{path}")
        except subprocess.CalledProcessError:
            errors.append(f"source_missing:{name}")
            continue
        if item.get("path") != path or frozen_item.get("path") != path: errors.append(f"source_path:{name}")
        if item.get("git_blob") != blob or frozen_item.get("git_blob") != blob: errors.append(f"source_blob:{name}")
        if item.get("sha256") != sha(src) or frozen_item.get("sha256") != sha(src): errors.append(f"source_sha:{name}")

    try:
        v6 = subprocess.check_output(["git", "show", f"{BASE}:{SOURCES['v6_runner']}"]).decode()
        clock_pos = v6.index("planner_end_ns = session.runtime_clock()")
        cancel_pos = v6.index('session.send({"op": "cancel", "id": fallback_id})', clock_pos)
        if clock_pos >= cancel_pos: errors.append("source_order")
    except (subprocess.CalledProcessError, ValueError):
        errors.append("source_order_unavailable")

    cases = raw.get("cases")
    if not isinstance(cases, list) or len(cases) != 2:
        errors.append("case_count")
        cases = []
    by_name = {row.get("case"): row for row in cases}
    if len(by_name) != 2: errors.append("case_names_or_duplicates")
    configs = {
        "A-clock-before-cancel-within-lease": (600, 400, 2000),
        "B-lease-before-clock-return": (600, 1600, 1500),
    }
    for name, config in configs.items():
        row = by_name.get(name)
        if row is None:
            errors.append(f"missing_case:{name}")
            continue
        if (row.get("planner_wait_ms"), row.get("clock_delay_ms"), row.get("lease_ms")) != config:
            errors.append(f"config:{name}")
        start, timer, end, cancel, release = (row.get(key) for key in
            ("planner_start_ns", "timer_expired_ns", "clock_return_ns", "cancel_observed_ns", "release_ns"))
        summary = row.get("runner_arm_summary", {})
        if summary.get("planner_window", {}).get("end_ns") != row.get("planner_end_ns"):
            errors.append(f"summary_end:{name}")
        if row.get("planner_end_ns") != end:
            errors.append(f"end_clock:{name}")
        events = row.get("events", [])
        fallback_id = summary.get("fallback_id")
        terminals = [e for e in events if e.get("event") == "terminal" and e.get("id") == fallback_id]
        releases = [e for e in events if e.get("event") == "input_released" and e.get("id") == fallback_id]
        cancels = [e for e in events if e.get("event") == "cancel_requested" and e.get("id") == fallback_id]
        if len(terminals) != 1 or terminals[0].get("release", {}).get("verified") is not True:
            errors.append(f"terminal_release:{name}")
        if len(releases) != 1 or releases[0].get("verified") is not True or releases[0].get("release_ns") != release:
            errors.append(f"release_receipt:{name}")
        if len(cancels) != 1: errors.append(f"cancel_receipt_count:{name}")
        if row.get("terminal_release_verified") is not True: errors.append(f"runner_release:{name}")
        if not all(type(x) is int for x in (start, timer, end, release)):
            errors.append(f"timestamps:{name}")
            continue
        if name.startswith("A-"):
            if len(cancels) == 1 and cancels[0].get("matched") is not True: errors.append("A_cancel_unmatched")
            if type(cancel) is not int: errors.append("A_cancel_not_observed")
            else:
                if not 350 <= (release - timer) / 1e6 <= 2000: errors.append("A_timer_release_window")
                if abs(release - cancel) > 50_000_000: errors.append("A_release_after_cancel")
                if abs(release - end) > 50_000_000: errors.append("A_release_after_clock")
            if len(terminals) == 1 and terminals[0].get("status") != "cancelled": errors.append("A_status")
            if end <= timer: errors.append("A_clock_before_timer")
        else:
            deadline = start + 1_500_000_000
            if abs(release - deadline) > 50_000_000: errors.append("B_lease_deadline")
            if release >= end: errors.append("B_release_not_before_clock")
            if cancel is not None: errors.append("B_cancel_observed")
            if len(cancels) == 1 and cancels[0].get("matched") is not False: errors.append("B_cancel_matched")
            if len(terminals) == 1 and terminals[0].get("status") != "expired": errors.append("B_status")

    status = "PASS_RUNNER_CLOCK_DELAY_SCOPED" if not errors else "FAIL_AUDIT"
    return {"schema": "map01-v6-runner-clock-cancel-audit-v1", "allocation": ALLOCATION,
            "status": status, "errors": errors, "cases_checked": len(cases), "retries": 0,
            "scope": "raw-only independent timing/receipt audit; no game, GUI, transport, or physical input claim"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, type=pathlib.Path)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    args = parser.parse_args()
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    result = audit(json.loads(args.raw.read_text()), freeze)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "PASS_RUNNER_CLOCK_DELAY_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
