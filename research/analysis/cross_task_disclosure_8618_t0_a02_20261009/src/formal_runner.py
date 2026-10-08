#!/usr/bin/env python3
"""One-shot, no-network candidate and separate-auditor execution wrapper."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


NETWORK_DENY_PROFILE = "(version 1) (deny network*) (allow default)"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def load_freeze(root: Path, package: Path, freeze_path: Path, freeze_commit: str) -> dict[str, Any]:
    freeze = json.loads(freeze_path.read_text())
    head = git(root, "rev-parse", "HEAD")
    dirty = git(root, "status", "--porcelain")
    if head != freeze_commit:
        raise RuntimeError(f"HEAD {head} does not equal frozen commit {freeze_commit}")
    if dirty:
        raise RuntimeError("working tree is not clean at formal launch")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", freeze["base_main_sha"], head], cwd=root, check=False)
    if ancestor.returncode != 0:
        raise RuntimeError("frozen base main is not an ancestor of the freeze commit")
    for relative, expected in freeze["sha256"].items():
        actual = sha256(package / relative)
        if actual != expected:
            raise RuntimeError(f"frozen hash mismatch for {relative}: {actual}")
    return freeze


def invoke(command: list[str], cwd: Path, stdout_path: Path, stderr_path: Path) -> dict[str, Any]:
    start_utc = utc_now()
    start_ns = time.monotonic_ns()
    with stdout_path.open("xb") as stdout_file, stderr_path.open("xb") as stderr_file:
        completed = subprocess.run(command, cwd=cwd, stdout=stdout_file, stderr=stderr_file, check=False)
    end_ns = time.monotonic_ns()
    return {
        "command": command,
        "start_utc": start_utc,
        "end_utc": utc_now(),
        "duration_ns": end_ns - start_ns,
        "exit_code": completed.returncode,
        "stdout_sha256": sha256(stdout_path),
        "stderr_sha256": sha256(stderr_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--freeze", required=True, type=Path)
    parser.add_argument("--freeze-commit", required=True)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--sandbox-exec", required=True, type=Path)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    root = args.repo_root.resolve()
    package = args.package.resolve()
    raw_dir = package / "raw"
    audit_dir = package / "audit"
    lock = raw_dir / "EXECUTION_LOCK.json"
    if not args.preflight_only and lock.exists():
        raise RuntimeError("formal allocation already invoked or invocation state is uncertain; refusing retry")
    freeze = load_freeze(root, package, args.freeze.resolve(), args.freeze_commit)
    if args.preflight_only:
        print(json.dumps({"preflight": "PASS_NO_CANDIDATE_INVOKED", "freeze_commit": args.freeze_commit, "allocation_id": freeze["allocation_id"]}, sort_keys=True))
        return
    raw_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)
    runner_start_utc = utc_now()
    runner_command = [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]]
    lock.write_text(json.dumps({
        "allocation_id": freeze["allocation_id"],
        "state": "STARTED_BEFORE_CANDIDATE_INVOCATION",
        "freeze_commit": args.freeze_commit,
        "marked_utc": utc_now(),
    }, indent=2, sort_keys=True) + "\n")

    protocol = package / "input/protocol.json"
    policy = package / "input/policy_fixture.json"
    oracle = package / "input/oracle_fixture.json"
    candidate = package / "src/candidate.py"
    auditor = package / "src/auditor.py"
    candidate_command = [
        str(args.sandbox_exec), "-p", NETWORK_DENY_PROFILE, sys.executable,
        str(candidate), "--protocol", str(protocol), "--policy", str(policy),
        "--output", str(raw_dir / "candidate.jsonl"),
    ]
    candidate_result = invoke(
        candidate_command, root, raw_dir / "candidate.stdout.txt", raw_dir / "candidate.stderr.txt"
    )
    lock.write_text(json.dumps({
        "allocation_id": freeze["allocation_id"],
        "state": "CANDIDATE_EXITED",
        "freeze_commit": args.freeze_commit,
        "candidate": candidate_result,
        "updated_utc": utc_now(),
    }, indent=2, sort_keys=True) + "\n")

    auditor_result = None
    if candidate_result["exit_code"] == 0:
        audit_command = [
            str(args.sandbox_exec), "-p", NETWORK_DENY_PROFILE, sys.executable,
            str(auditor), "--protocol", str(protocol), "--policy", str(policy),
            "--oracle", str(oracle), "--raw", str(raw_dir / "candidate.jsonl"),
            "--output", str(audit_dir / "audit.json"),
        ]
        auditor_result = invoke(
            audit_command, root, audit_dir / "auditor.stdout.txt", audit_dir / "auditor.stderr.txt"
        )
    state = "AUDIT_EXITED" if auditor_result is not None else "CANDIDATE_NONZERO_NO_AUDIT"
    receipt = {
        "allocation_id": freeze["allocation_id"],
        "freeze_commit": args.freeze_commit,
        "state": state,
        "runner_pid": os.getpid(),
        "runner_command": runner_command,
        "runner_start_utc": runner_start_utc,
        "candidate": candidate_result,
        "candidate_raw_sha256": sha256(raw_dir / "candidate.jsonl") if (raw_dir / "candidate.jsonl").exists() else None,
        "auditor": auditor_result,
        "audit_sha256": sha256(audit_dir / "audit.json") if (audit_dir / "audit.json").exists() else None,
        "runner_end_utc": utc_now(),
    }
    receipt_path = raw_dir / "execution_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    lock.write_text(json.dumps({
        "allocation_id": freeze["allocation_id"],
        "state": state,
        "freeze_commit": args.freeze_commit,
        "receipt_sha256": sha256(receipt_path),
        "updated_utc": utc_now(),
    }, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "state": state,
        "candidate_exit_code": candidate_result["exit_code"],
        "auditor_exit_code": None if auditor_result is None else auditor_result["exit_code"],
        "receipt": str(receipt_path),
    }, sort_keys=True))
    if candidate_result["exit_code"] != 0 or (auditor_result and auditor_result["exit_code"] != 0):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
