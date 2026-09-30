"""One-shot delivery for the corrected audit; never reruns formal allocation."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

STUDY = Path(__file__).resolve().parent
REPO = STUDY.parents[2]
OUT = STUDY / "results" / "formal-01"
IMAGE = "python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f"
CONTAINER_STUDY = "/repo/research/verification/verification_coverage_5269_v1"


def stamp():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out_file = OUT / "AUDIT-02.json"
    marker = OUT / "audit-correction-invocation-started.json"
    execution = OUT / "audit-correction-execution.json"
    if not (OUT / "RAW-01.json").exists() or not (OUT / "AUDIT-01.json").exists():
        raise SystemExit("formal raw and preserved AUDIT-01 must exist")
    if out_file.exists() or marker.exists() or execution.exists():
        raise SystemExit("refusing repeat/overwrite of corrected audit")
    argv = [
        "docker", "--context", "orbstack", "run", "--rm",
        "--name", "unjuno-5269-coverage-audit-correction-02-20260930",
        "--network", "none", "--cpus=1", "--memory=512m", "--pids-limit=128",
        "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m",
        "-v", f"{REPO}:/repo:ro", "-v", f"{OUT}:/out:rw",
        "-w", CONTAINER_STUDY, IMAGE, "python", "-I", "-S", "-B", "-c",
        "import sys,runpy; sys.path.insert(0,'" + CONTAINER_STUDY + "'); "
        "runpy.run_path('" + CONTAINER_STUDY + "/audit_v2.py',run_name='__main__')",
    ]
    started = stamp()
    marker.write_text(json.dumps({"started_at": started, "argv": argv,
                                  "formal_allocation_repeated": False},
                                 sort_keys=True, indent=2) + "\n")
    run = subprocess.run(argv, capture_output=True, text=True, check=False)
    ended = stamp()
    (OUT / "audit-correction-container.stdout.txt").write_text(run.stdout)
    (OUT / "audit-correction-container.stderr.txt").write_text(run.stderr)
    record = {
        "started_at": started, "ended_at": ended, "argv": argv,
        "exit_code": run.returncode, "image": IMAGE,
        "source_commit": subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                                         capture_output=True, text=True, check=True).stdout.strip(),
        "auditor_sha256": sha(STUDY / "audit_v2.py"),
        "historical_audit_01_sha256": sha(OUT / "AUDIT-01.json"),
        "raw_sha256": sha(OUT / "RAW-01.json"),
        "formal_allocation_repeated": False,
        "stdout_sha256": hashlib.sha256(run.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(run.stderr.encode()).hexdigest(),
        "host_architecture": platform.machine(),
    }
    execution.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
    print(run.stdout, end="")
    if run.returncode:
        print(run.stderr, file=sys.stderr, end="")
        raise SystemExit(run.returncode)


if __name__ == "__main__":
    main()
