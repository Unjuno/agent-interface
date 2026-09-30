"""One-shot host launcher for pinned, isolated OrbStack allocations."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

IMAGE = "python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f"
STUDY = Path(__file__).resolve().parent
REPO = STUDY.parents[2]
OUT = STUDY / "results" / "formal-01"
CONTAINER_STUDY = "/repo/research/verification/verification_coverage_5269_v1"


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_freeze():
    freeze = json.loads((STUDY / "FREEZE.json").read_text())
    commit = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                            capture_output=True, text=True, check=True).stdout.strip()
    branch = subprocess.run(["git", "-C", str(REPO), "branch", "--show-current"],
                            capture_output=True, text=True, check=True).stdout.strip()
    if commit != freeze["base_sha"] or branch != freeze["branch"]:
        raise SystemExit("freeze base or branch mismatch; no allocation run")
    for relative, expected in {**freeze["source_sha256"], **freeze["parent_inputs"]}.items():
        actual = digest(REPO / relative)
        if actual != expected:
            raise SystemExit(f"frozen file hash mismatch; no allocation run: {relative}")


def run_one(name, script, output_guard):
    OUT.mkdir(parents=True, exist_ok=True)
    receipt = OUT / f"{name}-execution.json"
    started_marker = OUT / f"{name}-invocation-started.json"
    if receipt.exists() or started_marker.exists() or output_guard.exists():
        raise SystemExit(f"refusing repeat/overwrite: {name} allocation evidence already exists")
    args = [
        "docker", "--context", "orbstack", "run", "--rm",
        "--name", f"unjuno-5269-coverage-{name}-01-20260930",
        "--network", "none", "--cpus=1", "--memory=512m", "--pids-limit=128",
        "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m",
        "-v", f"{REPO}:/repo:ro", "-v", f"{OUT}:/out:rw",
        "-w", CONTAINER_STUDY, IMAGE, "python", "-I", "-S", "-B", "-c",
        "import sys,runpy; sys.path.insert(0,'" + CONTAINER_STUDY + "'); "
        "runpy.run_path('" + CONTAINER_STUDY + "/" + script + "',run_name='__main__')",
    ]
    started = now()
    started_marker.write_text(json.dumps({"name": name, "started_at": started,
                                          "argv": args}, sort_keys=True, indent=2) + "\n")
    completed = subprocess.run(args, capture_output=True, text=True, check=False)
    ended = now()
    (OUT / f"{name}-container.stdout.txt").write_text(completed.stdout)
    (OUT / f"{name}-container.stderr.txt").write_text(completed.stderr)
    record = {"name": name, "argv": args, "started_at": started, "ended_at": ended,
              "exit_code": completed.returncode, "stdout_sha256": hashlib.sha256(
                  completed.stdout.encode()).hexdigest(), "stderr_sha256": hashlib.sha256(
                  completed.stderr.encode()).hexdigest(), "image": IMAGE,
              "host_architecture": __import__("platform").machine(),
              "source_commit": subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                  capture_output=True, text=True, check=True).stdout.strip()}
    receipt.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
    print(completed.stdout, end="")
    if completed.returncode:
        print(completed.stderr, file=sys.stderr, end="")
        raise SystemExit(completed.returncode)


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"--formal", "--audit"}:
        raise SystemExit("usage: python launch.py --formal|--audit")
    verify_freeze()
    if sys.argv[1] == "--formal":
        run_one("formal", "run_formal.py", OUT / "RAW-01.json")
    else:
        formal_receipt = OUT / "formal-execution.json"
        if not formal_receipt.exists():
            raise SystemExit("formal allocation receipt missing; audit not run")
        formal = json.loads(formal_receipt.read_text())
        if formal.get("exit_code") != 0 or not (OUT / "RAW-01.json").exists():
            raise SystemExit("formal allocation did not complete cleanly; audit not run")
        run_one("audit", "audit.py", OUT / "AUDIT-01.json")


if __name__ == "__main__":
    main()
