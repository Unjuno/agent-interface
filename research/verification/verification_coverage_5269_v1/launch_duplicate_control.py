"""One-shot container launch for duplicate-control construction supplement."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

STUDY = Path(__file__).resolve().parent
REPO = STUDY.parents[2]
OUT = STUDY / "results" / "duplicate-control-02"
IMAGE = "python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f"
CONTAINER_STUDY = "/repo/research/verification/verification_coverage_5269_v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    result = OUT / "DUPLICATE-CONTROL-02.json"
    receipt = OUT / "execution.json"
    marker = OUT / "invocation-started.json"
    if result.exists() or receipt.exists() or marker.exists():
        raise SystemExit("refusing repeat/overwrite of duplicate construction supplement")
    argv = [
        "docker", "--context", "orbstack", "run", "--rm",
        "--name", "unjuno-5269-duplicate-control-02-20260930",
        "--network", "none", "--cpus=1", "--memory=512m", "--pids-limit=128",
        "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m",
        "-v", f"{REPO}:/repo:ro", "-v", f"{OUT}:/out:rw",
        "-w", CONTAINER_STUDY, IMAGE, "python", "-I", "-S", "-B", "-c",
        "import sys,runpy; sys.path.insert(0,'" + CONTAINER_STUDY + "'); "
        "runpy.run_path('" + CONTAINER_STUDY + "/duplicate_control.py',run_name='__main__')",
    ]
    started = datetime.now(timezone.utc).isoformat()
    marker.write_text(json.dumps({"argv": argv, "started_at": started,
                                  "formal_replay": False}, sort_keys=True, indent=2) + "\n")
    result_run = subprocess.run(argv, capture_output=True, text=True, check=False)
    ended = datetime.now(timezone.utc).isoformat()
    (OUT / "container.stdout.txt").write_text(result_run.stdout)
    (OUT / "container.stderr.txt").write_text(result_run.stderr)
    receipt.write_text(json.dumps({
        "argv": argv, "started_at": started, "ended_at": ended,
        "exit_code": result_run.returncode, "image": IMAGE,
        "source_commit": subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                                         capture_output=True, text=True, check=True).stdout.strip(),
        "duplicate_control_source_sha256": sha(STUDY / "duplicate_control.py"),
        "coverage_source_sha256": sha(STUDY / "coverage.py"),
        "frozen_coverage_source_sha256": "8fd2ede5e300ff2265ee0f427a8476ca5e42795e8c08f2cc304f9d5edee86fd7",
        "formal_replay": False,
        "stdout_sha256": hashlib.sha256(result_run.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(result_run.stderr.encode()).hexdigest(),
    }, sort_keys=True, indent=2) + "\n")
    print(result_run.stdout, end="")
    if result_run.returncode:
        print(result_run.stderr, file=sys.stderr, end="")
        raise SystemExit(result_run.returncode)


if __name__ == "__main__":
    main()
