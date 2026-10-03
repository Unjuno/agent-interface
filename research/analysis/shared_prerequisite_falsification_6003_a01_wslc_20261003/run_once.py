#!/usr/bin/env python3
"""Capture one frozen WSLc invocation and retain raw subprocess evidence."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time


ROOT = Path(__file__).resolve().parent
REPOSITORY = ROOT.parents[2]


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git(*arguments: str) -> str:
    process = subprocess.run(
        ["git", "-C", str(REPOSITORY), *arguments],
        check=True, capture_output=True,
    )
    return process.stdout.decode("utf-8").strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", choices=("candidate", "auditor"), required=True)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    freeze_bytes = (ROOT / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    freeze_hash = digest(freeze_bytes)
    if freeze["freeze_time_utc"].startswith("PENDING"):
        raise SystemExit("STOP_FREEZE_INCOMPLETE")
    if ROOT != Path(freeze["host_paths"]["package"]).resolve():
        raise SystemExit("STOP_PACKAGE_PATH_MISMATCH")
    if git("branch", "--show-current") != freeze["branch"]:
        raise SystemExit("STOP_BRANCH_MISMATCH")
    if git("status", "--porcelain", "--untracked-files=all"):
        raise SystemExit("STOP_SOURCE_WORKTREE_NOT_CLEAN")
    head = git("rev-parse", "HEAD")
    actual_hashes = {}
    for name, expected in freeze["sha256"].items():
        actual_hashes[name] = digest((ROOT / name).read_bytes())
        if actual_hashes[name] != expected:
            raise SystemExit("STOP_SOURCE_HASH_MISMATCH:" + name)

    output = Path(freeze["host_paths"][args.role])
    result_root = Path(freeze["host_paths"]["result_root"]).resolve()
    if output.resolve().parent != result_root:
        raise SystemExit("STOP_OUTPUT_PATH_MISMATCH")
    if output.exists() and any(output.iterdir()):
        raise SystemExit("STOP_ROLE_ALREADY_ATTEMPTED")
    argv = freeze["commands"][args.role]
    if not Path(argv[0]).is_file():
        raise SystemExit("STOP_WSLC_EXECUTABLE_MISSING")
    if args.role == "auditor":
        candidate_dir = Path(freeze["host_paths"]["candidate"])
        candidate_bytes = (candidate_dir / "candidate_result.json").read_bytes()
        candidate_receipt = json.loads((candidate_dir / "receipt.json").read_bytes())
        result = json.loads(candidate_bytes)
        if result.get("freeze_sha256") != freeze_hash:
            raise SystemExit("STOP_CANDIDATE_FREEZE_MISMATCH")
        if candidate_receipt["freeze_sha256"] != freeze_hash:
            raise SystemExit("STOP_CANDIDATE_RECEIPT_MISMATCH")
        if candidate_receipt["output_sha256"].get("candidate_result.json") != digest(candidate_bytes):
            raise SystemExit("STOP_CANDIDATE_BYTES_CHANGED")
    if args.check_only:
        print(json.dumps({"role": args.role, "status": "READY", "head": head,
                          "freeze_sha256": freeze_hash}, sort_keys=True))
        return 0

    output.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    attempt = {"role": args.role, "started_utc": started, "argv": argv,
               "source_commit": head, "freeze_sha256": freeze_hash,
               "source_sha256": actual_hashes}
    (output / "attempt.json").write_text(
        json.dumps(attempt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    clock_start = time.perf_counter()
    launch_error = None
    try:
        process = subprocess.run(argv, capture_output=True)
        stdout, stderr, exit_code = process.stdout, process.stderr, process.returncode
    except OSError as error:
        stdout, stderr, exit_code = b"", b"", None
        launch_error = str(error)
    elapsed = time.perf_counter() - clock_start
    (output / "stdout.bin").write_bytes(stdout)
    (output / "stderr.bin").write_bytes(stderr)
    hashes = {path.name: digest(path.read_bytes())
              for path in sorted(output.iterdir()) if path.is_file()}
    receipt = {**attempt, "finished_utc": datetime.now(timezone.utc).isoformat(),
               "wall_seconds": elapsed, "exit_code": exit_code,
               "launch_error": launch_error, "output_sha256": hashes,
               "resource_limits": "requested only; effective enforcement is unproven"}
    (output / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"role": args.role, "exit_code": exit_code,
                      "wall_seconds": elapsed, "launch_error": launch_error,
                      "output_sha256": hashes}, sort_keys=True))
    return exit_code if exit_code is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
