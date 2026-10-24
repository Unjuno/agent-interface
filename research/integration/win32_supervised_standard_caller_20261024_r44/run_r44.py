"""Run the frozen two-phase R42 attempt once; never replay either phase."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import argparse
import subprocess
import sys
import time
from pathlib import Path

PACKET = Path(__file__).resolve().parent
ROOT = PACKET.parents[2]
CONDITIONS = json.loads((PACKET / "conditions.json").read_text(encoding="utf-8"))
RUN = PACKET / "run"


def save(path: Path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2,
                               ensure_ascii=False) + "\n", encoding="utf-8")


def audit_combined():
    return subprocess.run([sys.executable, str(PACKET / "audit_r44.py")],
        cwd=ROOT, capture_output=True, text=True, timeout=20)


def main() -> int:
    if sys.platform != "win32":
        raise SystemExit("R44 requires native Windows")
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight-only", action="store_true",
        help="run the input-free preflight and retain it without starting a fixture")
    args = parser.parse_args()
    for path in (RUN, PACKET / "raw.json", PACKET / "audit_r36.json",
                 PACKET / "task_raw.json", PACKET / "audit_r44.json",
                 PACKET / "phase2_status.json",
                 PACKET / "phases.json", PACKET / "PRERUN_CUSTODY.json",
                 PACKET / "SHA256SUMS"):
        if path.exists():
            raise SystemExit(f"one-shot evidence already exists; refusing to overwrite: {path}")

    preflight_path = PACKET / "preflight.json"
    if args.preflight_only:
        if preflight_path.exists():
            raise SystemExit("preflight evidence already exists; refusing to overwrite")
        preflight = subprocess.run([sys.executable, str(PACKET / "preflight_r44.py")],
            cwd=ROOT, capture_output=True, text=True, timeout=45)
        print(preflight.stdout)
        if preflight.stderr:
            print(preflight.stderr, file=sys.stderr)
        return preflight.returncode
    if preflight_path.exists():
        existing = json.loads(preflight_path.read_text(encoding="utf-8"))
        age = (dt.datetime.now(dt.timezone.utc)
            - dt.datetime.fromisoformat(existing["utc"])).total_seconds()
        expected_conditions = hashlib.sha256(
            (PACKET / "conditions.json").read_bytes()).hexdigest()
        if (existing.get("status") != "PASS"
                or existing.get("attempt_id") != CONDITIONS["attempt_id"]
                or existing.get("source_commit") != CONDITIONS["source_commit"]
                or existing.get("conditions_sha256") != expected_conditions
                or not 0 <= age <= 300):
            raise SystemExit("retained preflight is not a fresh PASS for this frozen attempt")
        preflight_stdout = json.dumps({"retained_preflight": True,
            "status": existing["status"], "age_seconds": age}, sort_keys=True)
        preflight_stderr = ""
    else:
        preflight = subprocess.run([sys.executable, str(PACKET / "preflight_r44.py")],
            cwd=ROOT, capture_output=True, text=True, timeout=45)
        if preflight.returncode:
            print(preflight.stdout)
            print(preflight.stderr, file=sys.stderr)
            return preflight.returncode
        preflight_stdout, preflight_stderr = preflight.stdout, preflight.stderr
    custody = {
        "schema": "win32-r44-prerun-custody-v1",
        "attempt_id": CONDITIONS["attempt_id"],
        "source_commit": CONDITIONS["source_commit"],
        "conditions_sha256": hashlib.sha256(
            (PACKET / "conditions.json").read_bytes()).hexdigest(),
        "preflight_sha256": hashlib.sha256(preflight_path.read_bytes()).hexdigest(),
        "preflight_stdout": preflight_stdout,
        "preflight_stderr": preflight_stderr,
        "native_input_sent": False,
        "phase1_output_absent_before_launch": not RUN.exists(),
        "frozen_files": CONDITIONS["frozen_files"],
    }
    save(PACKET / "PRERUN_CUSTODY.json", custody)

    phases = {"schema": "win32-r44-phases-v1",
        "attempt_id": CONDITIONS["attempt_id"],
        "phase1_started_monotonic_ns": time.monotonic_ns()}
    stage1 = subprocess.run([sys.executable, str(PACKET / "probe.py")],
        cwd=ROOT, capture_output=True, text=True,
        timeout=CONDITIONS["timeouts_seconds"]["attempt_total"] + 15)
    phases["phase1_process_returned_monotonic_ns"] = time.monotonic_ns()
    phases["phase1_exit_code"] = stage1.returncode
    phases["phase1_stdout"] = stage1.stdout
    phases["phase1_stderr"] = stage1.stderr
    if not (PACKET / "raw.json").exists():
        save(PACKET / "phase2_status.json", {
            "status": "NOT_STARTED_PHASE1_RAW_MISSING",
            "phase1_exit_code": stage1.returncode})
        save(PACKET / "phases.json", phases)
        return stage1.returncode or 1

    audit1 = subprocess.run([sys.executable, str(PACKET / "audit_release.py")],
        cwd=ROOT, capture_output=True, text=True, timeout=20)
    phases["phase1_audit_returned_monotonic_ns"] = time.monotonic_ns()
    phases["phase1_audit_exit_code"] = audit1.returncode
    phases["phase1_audit_stdout"] = audit1.stdout
    phases["phase1_audit_stderr"] = audit1.stderr
    if audit1.returncode or not (PACKET / "audit_r36.json").exists():
        save(PACKET / "phase2_status.json", {
            "status": "NOT_STARTED_PHASE1_AUDIT_UNAVAILABLE",
            "phase1_exit_code": stage1.returncode,
            "phase1_audit_exit_code": audit1.returncode})
        audit_combined()
        save(PACKET / "phases.json", phases)
        return audit1.returncode or 1

    release = json.loads((PACKET / "audit_r36.json").read_text(encoding="utf-8"))
    if (stage1.returncode != 0
            or release.get("strict_release_gate_passed") is not True):
        save(PACKET / "phase2_status.json", {
            "status": "NOT_STARTED_PHASE1_GATE_FAILED",
            "phase1_exit_code": stage1.returncode,
            "phase1_release_status": release.get("status"),
            "phase1_strict_release_gate_passed": release.get("strict_release_gate_passed")})
        save(PACKET / "phases.json", phases)
        audit_combined()
        return 0

    phases["phase2_started_monotonic_ns"] = time.monotonic_ns()
    phase2 = subprocess.run([sys.executable, str(PACKET / "task_probe.py")],
        cwd=ROOT, capture_output=True, text=True,
        timeout=CONDITIONS["phase2_protocol"]["max_attempt_total_seconds"] + 15)
    phases["phase2_process_returned_monotonic_ns"] = time.monotonic_ns()
    phases["phase2_exit_code"] = phase2.returncode
    phases["phase2_stdout"] = phase2.stdout
    phases["phase2_stderr"] = phase2.stderr
    if (PACKET / "run" / "phase2_task" / "result.json").exists():
        task_raw = json.loads((PACKET / "run" / "phase2_task" / "result.json").read_text(encoding="utf-8"))
        save(PACKET / "task_raw.json", task_raw)
    elif not (PACKET / "task_raw.json").exists():
        save(PACKET / "task_raw.json", {
            "attempt_id": CONDITIONS["attempt_id"] + "-phase2",
            "status": "FAIL_OR_UNKNOWN",
            "harness_returncode": phase2.returncode,
            "stdout": phase2.stdout,
            "stderr": phase2.stderr})
    save(PACKET / "phases.json", phases)
    combined = audit_combined()
    print(combined.stdout)
    if combined.stderr:
        print(combined.stderr, file=sys.stderr)
    return phase2.returncode or combined.returncode


if __name__ == "__main__":
    raise SystemExit(main())
