"""Single-shot, lease-gated launcher. No retry path exists by design."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from protocol import (ALLOCATION, IMAGE_ID, SEEDS, canonical, docker_argv,
                      exact_argv_matches, sha256_bytes)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ISSUE = 5085
LEASE_SCHEMA = "needle-docker-owner-lease-v1"
REQUIRED_LEASE_FIELDS = ("allocation", "issue", "owner_comment_url", "docker_context",
                         "main_sha", "branch", "expires_at_utc", "lease_id")


def stop(reason: str):
    raise SystemExit("STOP_" + reason)


def read_json(path: Path):
    try:
        return json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError) as exc:
        stop("INVALID_JSON:" + str(exc))


def validate_lease(lease: dict, main_sha: str, branch: str, current_context: str):
    if not isinstance(lease, dict) or lease.get("schema") != LEASE_SCHEMA:
        stop("NO_EXPLICIT_OWNER_LEASE")
    if any(not isinstance(lease.get(key), str) or not lease[key].strip()
           for key in REQUIRED_LEASE_FIELDS):
        stop("LEASE_FIELD_MISSING")
    if (lease["allocation"] != ALLOCATION or lease["issue"] != ISSUE
            or lease["main_sha"] != main_sha or lease["branch"] != branch
            or lease["docker_context"] != current_context):
        stop("LEASE_SCOPE_MISMATCH")
    if not lease["owner_comment_url"].startswith("https://github.com/Unjuno/agent-interface/issues/5085#"):
        stop("LEASE_OWNER_COMMENT_UNVERIFIABLE")
    if lease["lease_id"] in ("none", "unknown", "pending"):
        stop("LEASE_ID_INVALID")
    try:
        expiry = datetime.fromisoformat(lease["expires_at_utc"].replace("Z", "+00:00"))
    except ValueError:
        stop("LEASE_EXPIRY_INVALID")
    if expiry.tzinfo is None or expiry <= datetime.now(timezone.utc):
        stop("LEASE_EXPIRED_OR_UNZONED")


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--preflight"]:
        print(json.dumps({"allocation": ALLOCATION, "formal_docker_calls": 0,
                          "lease_required": True, "result": "PREFLIGHT_ONLY"}, sort_keys=True))
        return 0
    if len(args) != 7 or args[0] != "--formal":
        stop("USAGE:formal LEASE.json MAIN_SHA BRANCH DOCKER_CONTEXT SOURCE_DIR OUTPUT_DIR")
    lease_path, main_sha, branch, expected_context, source_text, output_text = args[1:]
    lease = read_json(Path(lease_path))
    try:
        source, output = Path(source_text).resolve(strict=True), Path(output_text).resolve(strict=True)
    except OSError as exc:
        stop("MOUNT_PATH_INVALID:" + str(exc))
    if source != HERE.resolve(strict=True):
        stop("SOURCE_PATH_NOT_EXPERIMENT_DIRECTORY")
    if not output.is_dir() or any(output.iterdir()):
        stop("OUTPUT_NOT_EMPTY")
    context_result = subprocess.run(["docker", "context", "show"], check=False,
                                    capture_output=True, text=True, timeout=10)
    if context_result.returncode != 0:
        stop("DOCKER_CONTEXT_UNAVAILABLE")
    current_context = context_result.stdout.strip()
    if current_context != expected_context:
        stop("DOCKER_CONTEXT_CHANGED")
    validate_lease(lease, main_sha, branch, current_context)
    try:
        actual_branch = subprocess.run(["git", "branch", "--show-current"], cwd=ROOT,
                                       check=True, capture_output=True, text=True, timeout=10).stdout.strip()
        current_main = subprocess.run(["git", "rev-parse", "refs/remotes/origin/main"], cwd=ROOT,
                                      check=True, capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        stop("GIT_MAIN_OR_BRANCH_UNVERIFIABLE")
    if actual_branch != branch or current_main != main_sha:
        stop("STALE_MAIN_OR_BRANCH")

    argv = docker_argv(source, output)
    canonical_argv = list(argv)
    receipt = {
        "schema": "needle-role-skill-joint-retention-formal-receipt-v1",
        "allocation": ALLOCATION, "issue": 5081, "lease_id": lease["lease_id"],
        "owner_comment_url": lease["owner_comment_url"], "main_sha": main_sha,
        "branch": branch, "docker_context": current_context,
        "source_path": str(source), "output_path": str(output),
        "image_id": IMAGE_ID, "seeds": list(SEEDS), "formal_invocations": 1,
        "retries": 0, "command_argv": canonical_argv,
        "command_argv_sha256": sha256_bytes(canonical(canonical_argv)),
        "started_at_ns": time.time_ns(),
    }
    receipt_path = output / "formal_receipt.json"
    # This one invocation is deliberate. There is no retry or partial rerun.
    proc = subprocess.run(argv, check=False, capture_output=True, text=True)
    raw_path = output / "formal_result.json"
    raw_sha = sha256_bytes(raw_path.read_bytes()) if raw_path.is_file() else None
    completed = {**receipt, "exit_code": proc.returncode,
                 "finished_at_ns": time.time_ns(),
                 "stdout": proc.stdout, "stderr": proc.stderr,
                 "raw_result_sha256": raw_sha,
                 "formal_result_present": raw_path.is_file()}
    with receipt_path.open("xb") as stream:
        stream.write(canonical(completed) + b"\n")
    print(json.dumps({"allocation": ALLOCATION, "exit_code": proc.returncode,
                      "formal_invocations": 1, "retries": 0,
                      "raw_result_sha256": raw_sha}, sort_keys=True))
    return 0 if proc.returncode == 0 and raw_sha else 2


if __name__ == "__main__":
    raise SystemExit(main())
