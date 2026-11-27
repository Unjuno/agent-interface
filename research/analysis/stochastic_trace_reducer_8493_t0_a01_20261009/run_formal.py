#!/usr/bin/env python3
"""Guard and run exactly one candidate and one separate audit subprocess."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
RESULTS = PACKAGE / "results"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_once(argv: list[str], env: dict[str, str], timeout: int) -> dict:
    record = {"argv": argv, "started_utc": now(), "attempted": True}
    try:
        result = subprocess.run(argv, cwd=PACKAGE, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=timeout, check=False)
        stdout, stderr = result.stdout, result.stderr
        record.update({"completed_utc": now(), "process_started": True,
                       "exit_code": result.returncode, "timed_out": False})
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or b""; stderr = exc.stderr or b""
        if isinstance(stdout, str): stdout = stdout.encode()
        if isinstance(stderr, str): stderr = stderr.encode()
        record.update({"completed_utc": now(), "process_started": True,
                       "exit_code": 124, "timed_out": True})
    except OSError as exc:
        stdout, stderr = b"", (type(exc).__name__+":"+str(exc)+"\n").encode()
        record.update({"completed_utc": now(), "process_started": False,
                       "exit_code": 127, "timed_out": False})
    return {**record, "stdout": stdout, "stderr": stderr}


def write_process(prefix: str, record: dict) -> dict:
    (RESULTS/(prefix+".stdout.txt")).write_bytes(record["stdout"])
    (RESULTS/(prefix+".stderr.txt")).write_bytes(record["stderr"])
    (RESULTS/(prefix+".exit.txt")).write_text(str(record["exit_code"])+"\n", encoding="ascii")
    return {k: v for k, v in record.items() if k not in ("stdout", "stderr")}


def main() -> int:
    freeze_path = PACKAGE / "FREEZE.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    frozen_sha = sha(freeze_path.read_bytes())
    if sys.version.split()[0] != freeze["python_version"]:
        raise SystemExit("STOP_PYTHON_VERSION_MISMATCH")
    if platform.system() != freeze["host_system"] or platform.machine() != freeze["host_arch"]:
        raise SystemExit("STOP_HOST_MISMATCH")
    root = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=PACKAGE,
                          capture_output=True, text=True, check=True).stdout.strip()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PACKAGE,
                          capture_output=True, text=True, check=True).stdout.strip()
    branch = subprocess.run(["git", "branch", "--show-current"], cwd=PACKAGE,
                            capture_output=True, text=True, check=True).stdout.strip()
    parents = subprocess.run(["git", "rev-list", "--parents", "-n", "1", "HEAD"], cwd=PACKAGE,
                             capture_output=True, text=True, check=True).stdout.split()
    status = subprocess.run(["git", "status", "--porcelain=v1"], cwd=PACKAGE,
                            capture_output=True, text=True, check=True).stdout
    relative_package = str(PACKAGE.relative_to(root))
    if relative_package != freeze["repo_relative_path"] or branch != freeze["branch"]:
        raise SystemExit("STOP_WORKTREE_IDENTITY_MISMATCH")
    if len(parents) != 2 or parents[1] != freeze["base_commit"]:
        raise SystemExit("STOP_FROZEN_COMMIT_PARENT_MISMATCH")
    if status:
        raise SystemExit("STOP_WORKTREE_NOT_CLEAN")
    if sha((PACKAGE/"fixture.json").read_bytes()) != freeze["fixture_sha256"]:
        raise SystemExit("STOP_FIXTURE_HASH_MISMATCH")
    for relative, expected in freeze["files"].items():
        if sha((PACKAGE/relative).read_bytes()) != expected:
            raise SystemExit("STOP_SOURCE_HASH_MISMATCH:"+relative)
    if RESULTS.exists() and any(RESULTS.iterdir()):
        raise SystemExit("STOP_RESULTS_NOT_EMPTY")
    RESULTS.mkdir(exist_ok=True)
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
           "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1",
           "PYTHONHASHSEED": "0", "TMPDIR": str(RESULTS)}
    py = sys.executable
    candidate_argv = [py, "-B", "candidate.py", "--output", "results/candidate.raw.json",
                      "--freeze-digest", frozen_sha]
    (RESULTS/"candidate.started.utc").write_text(now()+"\n", encoding="ascii")
    candidate = run_once(candidate_argv, env, 120)
    candidate_record = write_process("candidate", candidate)
    audit_argv = [py, "-B", "audit.py", "--raw", "results/candidate.raw.json",
                  "--output", "results/AUDIT.json", "--freeze-digest", frozen_sha]
    auditor = run_once(audit_argv, env, 180)
    audit_record = write_process("audit", auditor)
    run = {"schema": "unjuno.issue8493.formal-run.v1", "allocation": freeze["allocation"],
           "freeze_sha256": frozen_sha, "freeze_commit": head, "base_commit": freeze["base_commit"],
           "host": {"system": platform.platform(), "architecture": platform.machine(),
                    "python": sys.version, "python_executable": py, "container": False},
           "candidate_invocations": 1, "auditor_invocations": 1, "retries": 0,
           "candidate": candidate_record, "auditor": audit_record,
           "candidate_raw_sha256": sha((RESULTS/"candidate.raw.json").read_bytes()) if (RESULTS/"candidate.raw.json").is_file() else None,
           "audit_sha256": sha((RESULTS/"AUDIT.json").read_bytes()) if (RESULTS/"AUDIT.json").is_file() else None,
           "finalized_utc": now()}
    (RESULTS/"RUN.json").write_text(json.dumps(run, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    return 0 if candidate["exit_code"] == 0 and auditor["exit_code"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
