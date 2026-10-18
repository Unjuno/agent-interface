#!/usr/bin/env python3
"""Single-shot OrbStack candidate then independent raw-only auditor."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
IMAGE = "python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151"
FROZEN_BASE = "a6d12178e6ce70b178ba73c5d2d37d483fa3abda"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def container_common():
    return ["docker", "run", "--pull=never", "--rm", "--network=none", "--read-only",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m", "--cap-drop=ALL",
            "--security-opt=no-new-privileges", "--cpus=1", "--memory=1g"]


def mount(source, target, readonly=True):
    mode = "ro" if readonly else "rw"
    return ["--mount", f"type=bind,src={source},dst={target},{mode}"]


def invoke(command, stdout_path, stderr_path):
    result = subprocess.run(command, text=True, capture_output=True, timeout=900)
    stdout_path.write_text(result.stdout)
    stderr_path.write_text(result.stderr)
    return result.returncode


def main():
    frozen_path = ROOT / "FROZEN.json"
    frozen = json.loads(frozen_path.read_text())
    if frozen.get("base_commit") != FROZEN_BASE:
        raise SystemExit("STOP_FROZEN_BASE_MISMATCH")
    if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() != FROZEN_BASE:
        raise SystemExit("STOP_CURRENT_HEAD_DIFFERS_FROM_FREEZE")
    for relative, expected in frozen["source_sha256"].items():
        if sha256(ROOT / relative) != expected:
            raise SystemExit("STOP_FROZEN_SOURCE_HASH_MISMATCH:" + relative)
    results = ROOT / "results"
    if results.exists() and any(results.iterdir()):
        raise SystemExit("STOP_OUTPUT_DIRECTORY_NOT_EMPTY")
    results.mkdir(exist_ok=True)
    audit_output = results / "audit-output"
    audit_output.mkdir(exist_ok=True)
    candidate_output = results / "candidate_output.json"
    command_candidate = (container_common() +
        mount(ROOT / "candidate.py", "/work/candidate.py") +
        mount(ROOT / "public_input.json", "/work/public_input.json") +
        mount(results, "/out", readonly=False) +
        ["-w", "/work", IMAGE, "python", "-B", "/work/candidate.py",
         "--input", "/work/public_input.json", "--output", "/out/candidate_output.json"])
    receipt = {"allocation": frozen["allocation"], "started_at_utc": datetime.now(timezone.utc).isoformat(),
               "candidate_invocations": 1, "auditor_invocations": 0, "retries": 0,
               "candidate_command": command_candidate, "auditor_command": None,
               "candidate_exit": None, "auditor_exit": None, "state": "CANDIDATE_RUNNING"}
    write_json(ROOT / "FORMAL_STARTED.json", receipt)
    candidate_exit = invoke(command_candidate, results / "candidate.stdout.txt", results / "candidate.stderr.txt")
    receipt["candidate_exit"] = candidate_exit
    receipt["state"] = "CANDIDATE_COMPLETE" if candidate_exit == 0 else "STOP_CANDIDATE_EXIT_NONZERO"
    write_json(ROOT / "FORMAL_STARTED.json", receipt)
    if candidate_exit != 0 or not candidate_output.is_file():
        write_json(ROOT / "RUN_RECORD.json", receipt)
        raise SystemExit(receipt["state"])

    command_auditor = (container_common() +
        mount(ROOT / "auditor.py", "/work/auditor.py") +
        mount(ROOT / "public_input.json", "/work/public_input.json") +
        mount(ROOT / "oracle_input.json", "/work/oracle_input.json") +
        mount(candidate_output, "/work/candidate_output.json") +
        mount(audit_output, "/out", readonly=False) +
        ["-w", "/work", IMAGE, "python", "-B", "/work/auditor.py",
         "--public", "/work/public_input.json", "--oracle", "/work/oracle_input.json",
         "--candidate", "/work/candidate_output.json", "--output", "/out/audit.json"])
    receipt["auditor_invocations"] = 1
    receipt["auditor_command"] = command_auditor
    receipt["state"] = "AUDITOR_RUNNING"
    write_json(ROOT / "FORMAL_STARTED.json", receipt)
    auditor_exit = invoke(command_auditor, results / "auditor.stdout.txt", results / "auditor.stderr.txt")
    receipt["auditor_exit"] = auditor_exit
    receipt["state"] = "COMPLETE" if auditor_exit == 0 else "FAIL_OR_STOP_AUDITOR"
    receipt["candidate_output_sha256"] = sha256(candidate_output)
    audit_path = audit_output / "audit.json"
    receipt["audit_sha256"] = sha256(audit_path) if audit_path.is_file() else None
    write_json(ROOT / "RUN_RECORD.json", receipt)
    write_json(ROOT / "FORMAL_STARTED.json", receipt)
    if auditor_exit != 0:
        raise SystemExit(receipt["state"])


if __name__ == "__main__":
    main()
