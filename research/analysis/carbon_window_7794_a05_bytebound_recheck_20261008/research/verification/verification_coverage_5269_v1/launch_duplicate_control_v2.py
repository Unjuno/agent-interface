"""One-shot launcher for duplicate construction correction; no formal replay."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

STUDY = Path(__file__).resolve().parent
REPO = STUDY.parents[2]
OUT = STUDY / "results" / "duplicate-control-03"
IMAGE = "python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f"
CONTAINER_STUDY = "/repo/research/verification/verification_coverage_5269_v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    result = OUT / "DUPLICATE-CONTROL-03.json"
    receipt, marker = OUT / "execution.json", OUT / "invocation-started.json"
    if result.exists() or receipt.exists() or marker.exists():
        raise SystemExit("refusing repeat/overwrite of duplicate construction 03")
    argv = [
        "docker", "--context", "orbstack", "run", "--rm",
        "--name", "unjuno-5269-duplicate-control-03-20260930",
        "--network", "none", "--cpus=1", "--memory=512m", "--pids-limit=128",
        "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m",
        "-v", f"{REPO}:/repo:ro", "-v", f"{OUT}:/out:rw",
        "-w", CONTAINER_STUDY, IMAGE, "python", "-I", "-S", "-B", "-c",
        "import sys,runpy; sys.path.insert(0,'" + CONTAINER_STUDY + "'); "
        "runpy.run_path('" + CONTAINER_STUDY + "/duplicate_control_v2.py',run_name='__main__')",
    ]
    started = datetime.now(timezone.utc).isoformat()
    marker.write_text(json.dumps({"argv": argv, "started_at": started,
                                  "formal_replay": False}, sort_keys=True, indent=2) + "\n")
    run = subprocess.run(argv, capture_output=True, text=True, check=False)
    ended = datetime.now(timezone.utc).isoformat()
    (OUT / "container.stdout.txt").write_text(run.stdout)
    (OUT / "container.stderr.txt").write_text(run.stderr)
    receipt.write_text(json.dumps({
        "argv": argv, "started_at": started, "ended_at": ended,
        "exit_code": run.returncode, "image": IMAGE,
        "source_commit": subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                                         capture_output=True, text=True, check=True).stdout.strip(),
        "auditor_source_sha256": sha(STUDY / "duplicate_control_v2.py"),
        "coverage_source_sha256": sha(STUDY / "coverage.py"),
        "formal_replay": False,
        "stdout_sha256": hashlib.sha256(run.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(run.stderr.encode()).hexdigest(),
    }, sort_keys=True, indent=2) + "\n")
    print(run.stdout, end="")
    if run.returncode:
        print(run.stderr, file=sys.stderr, end="")
        raise SystemExit(run.returncode)


if __name__ == "__main__":
    main()
