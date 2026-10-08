#!/usr/bin/env python3
"""Run the frozen candidate and raw auditor in a new provenance-bound directory."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import uuid

PACKAGE = Path(__file__).resolve().parent
FROZEN_RUNNER = PACKAGE / "executed-runner.py"
FROZEN_AUDITOR = PACKAGE / "audit_raw.py"
SOURCE_PATHS = (
    "runtime/core_v1/compiled_gui.py",
    "research/live_control/integrated_efficiency_compiled_adapter_v1.py",
    "research/live_control/integrated_efficiency_compiled_adapter_v2.py",
)

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def git_value(root, *args):
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        return None
    return result.stdout.decode("utf-8", "replace").strip()

def write_exclusive(path, content):
    with path.open("xb") as stream:
        stream.write(content)

def run_bounded(command, *, cwd, env, timeout):
    try:
        result = subprocess.run(
            command, cwd=cwd, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False, timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout or b""
        stderr = error.stderr or b""
        if isinstance(stdout, str):
            stdout = stdout.encode("utf-8", "replace")
        if isinstance(stderr, str):
            stderr = stderr.encode("utf-8", "replace")
        return None, stdout, stderr, "timeout"
    except OSError as error:
        return None, b"", (str(error) + "\n").encode("utf-8", "replace"), "launch_error"
    return result, result.stdout, result.stderr, "completed"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True,
                        help="Repository checkout containing runtime/ and research/.")
    parser.add_argument("--output-root", type=Path, required=True,
                        help="External writable directory for uniquely named reruns.")
    parser.add_argument("--run-id", help="Optional unique name; defaults to a random UUID.")
    parser.add_argument("--timeout-seconds", type=float, default=120,
                        help="Per-process timeout (default: 120 seconds).")
    args = parser.parse_args()

    source_root = args.source_root.resolve(strict=True)
    output_root = args.output_root.resolve()
    if not FROZEN_RUNNER.is_file() or not FROZEN_AUDITOR.is_file():
        parser.error("frozen runner and raw auditor must be adjacent to this script")
    if source_root == output_root or source_root in output_root.parents:
        parser.error("output root must be outside the source checkout")
    if PACKAGE == output_root or PACKAGE in output_root.parents:
        parser.error("output root must be outside this frozen evidence package")
    for relative in SOURCE_PATHS:
        if not (source_root / relative).is_file():
            parser.error(f"source file missing: {relative}")
    run_id = args.run_id or uuid.uuid4().hex
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", run_id):
        parser.error("--run-id must be a short path-safe identifier")
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive")
    output_root.mkdir(parents=True, exist_ok=True)
    run_dir = output_root / run_id
    try:
        run_dir.mkdir(exist_ok=False)
    except FileExistsError:
        print(f"refusing existing run directory: {run_dir}", file=sys.stderr)
        return 2

    copied_runner = run_dir / "executed-runner.py"
    copied_auditor = run_dir / "audit_raw.py"
    with FROZEN_RUNNER.open("rb") as source, copied_runner.open("xb") as dest:
        shutil.copyfileobj(source, dest)
    with FROZEN_AUDITOR.open("rb") as source, copied_auditor.open("xb") as dest:
        shutil.copyfileobj(source, dest)

    env = os.environ.copy()
    prior_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(source_root) + (os.pathsep + prior_pythonpath if prior_pythonpath else "")
    source_hashes_before = {relative: sha256(source_root / relative) for relative in SOURCE_PATHS}
    started = datetime.now(timezone.utc).isoformat()
    candidate, candidate_stdout, candidate_stderr, candidate_status = run_bounded(
        [sys.executable, "-B", str(copied_runner)], cwd=run_dir, env=env,
        timeout=args.timeout_seconds,
    )
    write_exclusive(run_dir / "candidate-stdout.bin", candidate_stdout)
    write_exclusive(run_dir / "candidate-stderr.bin", candidate_stderr)

    audit = None
    audit_stdout = b""
    audit_stderr = b""
    audit_result = None
    raw = run_dir / "raw-differential.json"
    if candidate and candidate.returncode == 0 and raw.is_file():
        audit, audit_stdout, audit_stderr, audit_status = run_bounded(
            [sys.executable, "-B", str(copied_auditor)], cwd=run_dir, env=env,
            timeout=args.timeout_seconds,
        )
        write_exclusive(run_dir / "audit-stdout.bin", audit_stdout)
        write_exclusive(run_dir / "audit-stderr.bin", audit_stderr)
        if audit:
            try:
                audit_result = json.loads(audit_stdout.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                audit_result = None
    else:
        audit_status = "not_run"

    finished = datetime.now(timezone.utc).isoformat()
    source_hashes_after = {relative: sha256(source_root / relative) for relative in SOURCE_PATHS}
    source_top = git_value(source_root, "rev-parse", "--show-toplevel")
    source_branch = git_value(source_root, "branch", "--show-current")
    clean_state = None
    if source_top:
        clean_state = git_value(source_root, "status", "--porcelain", "--untracked-files=no") == ""
    raw_exists = raw.is_file()
    experiment_id = None
    if raw_exists:
        try:
            experiment_id = json.loads(raw.read_text(encoding="utf-8")).get("experiment_id")
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            pass
    metadata = {
        "format": "fresh-synthetic-rerun-provenance-v3",
        "run_id": run_id,
        "candidate_experiment_id": (
            experiment_id
        ),
        "started_utc": started,
        "finished_utc": finished,
        "candidate_command": [Path(sys.executable).name, "-B", "executed-runner.py"],
        "auditor_command": [Path(sys.executable).name, "-B", "audit_raw.py"] if audit else None,
        "cwd": "fresh-run-directory",
        "source_root": "repository-root",
        "source_git_head": git_value(source_root, "rev-parse", "HEAD"),
        "source_git_branch": source_branch or None,
        "source_git_detached": bool(source_top and not source_branch),
        "tracked_worktree_clean": clean_state,
        "python_version": sys.version,
        "python_executable": Path(sys.executable).name,
        "platform": platform.platform(),
        "wrapper_sha256": sha256(Path(__file__).resolve()),
        "frozen_runner_sha256": sha256(FROZEN_RUNNER),
        "frozen_auditor_sha256": sha256(FROZEN_AUDITOR),
        "copied_runner_sha256": sha256(copied_runner),
        "copied_auditor_sha256": sha256(copied_auditor),
        "source_sha256": {relative: sha256(source_root / relative) for relative in SOURCE_PATHS},
        "source_sha256_before": source_hashes_before,
        "source_sha256_after": source_hashes_after,
        "source_unchanged_during_run": source_hashes_before == source_hashes_after,
        "candidate_status": candidate_status,
        "auditor_status": audit_status,
        "candidate_exit_code": candidate.returncode if candidate else None,
        "auditor_exit_code": audit.returncode if audit else None,
        "audit_result": audit_result,
        "raw_exists": raw_exists,
        "raw_sha256": sha256(raw) if raw_exists else None,
        "candidate_stdout_sha256": hashlib.sha256(candidate_stdout).hexdigest(),
        "candidate_stderr_sha256": hashlib.sha256(candidate_stderr).hexdigest(),
        "audit_stdout_sha256": hashlib.sha256(audit_stdout).hexdigest(),
        "audit_stderr_sha256": hashlib.sha256(audit_stderr).hexdigest(),
        "native_os_inputs": 0,
        "model_requests": 0,
    }
    write_exclusive(run_dir / "RUN.json",
                    (json.dumps(metadata, sort_keys=True, indent=2) + "\n").encode())
    print(json.dumps({"run_id": run_id,
                      "candidate_status": candidate_status,
                      "candidate_exit_code": candidate.returncode if candidate else None,
                      "auditor_status": audit_status,
                      "auditor_exit_code": metadata["auditor_exit_code"],
                      "audit_result": audit_result,
                      "raw_sha256": metadata["raw_sha256"]},
                     sort_keys=True, indent=2))
    if not candidate or candidate.returncode != 0 or not raw_exists or not audit or audit.returncode != 0:
        return (candidate.returncode if candidate else 1) or (audit.returncode if audit else 1) or 1
    if not metadata["source_unchanged_during_run"]:
        return 1
    if not isinstance(audit_result, dict) or audit_result.get("audit") != "PASS_RAW_RECONSTRUCTION":
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
