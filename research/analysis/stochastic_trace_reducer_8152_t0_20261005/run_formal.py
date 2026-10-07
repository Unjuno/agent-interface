#!/usr/bin/env python3
"""One-shot, offline OrbStack candidate then independent auditor execution."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IMAGE = "python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151"
DOCKER = "/Users/taka/.orbstack/bin/docker"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def container(script: str, args: list[str], result_files: list[Path]) -> int:
    cmd = [DOCKER, "run", "--rm", "--pull=never", "--network=none", "--read-only",
           "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m", "--cap-drop=ALL",
           "--security-opt=no-new-privileges", "--cpus=2", "--memory=2g", "--pids-limit=64"]
    for name in ("spec.py", "simulator.py", script):
        cmd += ["-v", f"{ROOT/name}:/pkg/{name}:ro"]
    for path in result_files:
        cmd += ["-v", f"{path}:/results/{path.name}:rw"]
    cmd += [IMAGE, "python", "-B", f"/pkg/{script}", *args]
    completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
    log = ROOT/"results"/("candidate.log" if script == "candidate.py" else "audit.log")
    log.write_text(completed.stdout + completed.stderr)
    return completed.returncode


def render_report() -> None:
    subprocess.run([sys.executable, "-B", str(ROOT/"report.py")], check=True)


def main() -> int:
    freeze = json.loads((ROOT/"FREEZE.json").read_text())
    for name, expected in freeze["files"].items():
        if sha(ROOT/name) != expected:
            raise SystemExit(f"STOP: frozen source changed: {name}")
    results = ROOT/"results"
    if any(results.iterdir()):
        raise SystemExit("STOP: formal results already exist; do not rerun")
    git_root = ROOT.parents[2]
    head = subprocess.check_output(["git", "-C", str(git_root), "rev-parse", "HEAD"], text=True).strip()
    upstream = subprocess.check_output(["git", "-C", str(git_root), "rev-parse", "origin/main"], text=True).strip()
    if head != upstream or head != freeze.get("base_commit"):
        raise SystemExit("STOP: experiment base differs from the frozen, locally fetched origin/main")
    (results/"RUN.json").write_text(json.dumps({"base_commit": head, "image": IMAGE,
        "freeze_sha256": sha(ROOT/"FREEZE.json"),
        "candidate_invocations": 0, "auditor_invocations": 0}, indent=2, sort_keys=True)+"\n")
    raw = results/"candidate.raw.json"
    raw.touch()
    freeze_digest = sha(ROOT/"FREEZE.json")
    run = json.loads((results/"RUN.json").read_text()); run["candidate_invocations"] = 1
    (results/"RUN.json").write_text(json.dumps(run, indent=2, sort_keys=True)+"\n")
    rc_candidate = container("candidate.py", ["/results/candidate.raw.json", freeze_digest], [raw])
    run = json.loads((results/"RUN.json").read_text()); run["candidate_invocations"] = 1; run["candidate_exit_code"] = rc_candidate
    run["candidate_sha256"] = sha(raw); run["candidate_log_sha256"] = sha(results/"candidate.log")
    (results/"RUN.json").write_text(json.dumps(run, indent=2, sort_keys=True)+"\n")
    audit_path = results/"AUDIT.json"
    audit_path.touch()
    run = json.loads((results/"RUN.json").read_text()); run["auditor_invocations"] = 1
    (results/"RUN.json").write_text(json.dumps(run, indent=2, sort_keys=True)+"\n")
    rc_audit = container("audit.py", ["/results/candidate.raw.json", "/results/AUDIT.json", freeze_digest], [raw, audit_path])
    run = json.loads((results/"RUN.json").read_text()); run["auditor_invocations"] = 1; run["auditor_exit_code"] = rc_audit
    run["audit_sha256"] = sha(audit_path); run["audit_log_sha256"] = sha(results/"audit.log")
    (results/"RUN.json").write_text(json.dumps(run, indent=2, sort_keys=True)+"\n")
    render_report()
    return rc_candidate if rc_candidate else rc_audit


if __name__ == "__main__":
    raise SystemExit(main())
