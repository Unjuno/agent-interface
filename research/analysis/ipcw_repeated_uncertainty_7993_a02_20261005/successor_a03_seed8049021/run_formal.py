#!/usr/bin/env python3
"""Single-shot A03 OrbStack candidate and raw-only audit with valid mounts."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
PARENT = ROOT.parent
BASE = "0db00a564daff64e47fd6931954ace0f71ab8f2b"
IMAGE = "python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def common():
    return ["docker", "run", "--pull=never", "--rm", "--network=none", "--read-only",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m", "--cap-drop=ALL",
            "--security-opt=no-new-privileges", "--cpus=1", "--memory=1g"]


def ro_mount(source, target):
    return ["--mount", f"type=bind,src={source},dst={target},readonly"]


def rw_mount(source, target):
    # Bind mounts are writable by default. Never append a bare `rw` field.
    return ["--mount", f"type=bind,src={source},dst={target}"]


def invoke(command, stdout, stderr):
    result = subprocess.run(command, text=True, capture_output=True, timeout=900)
    stdout.write_text(result.stdout)
    stderr.write_text(result.stderr)
    return result.returncode


def main():
    frozen = json.loads((ROOT / "FROZEN.json").read_text())
    latest = subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=ROOT, text=True).strip()
    merge_base = subprocess.check_output(["git", "merge-base", "HEAD", "origin/main"], cwd=ROOT, text=True).strip()
    if frozen.get("base_commit") != BASE or latest != BASE or merge_base != BASE:
        raise SystemExit(f"STOP_MAIN_CHANGED frozen={frozen.get('base_commit')} latest={latest} merge_base={merge_base}")
    for relative, expected in frozen["source_sha256"].items():
        if sha(ROOT / relative) != expected:
            raise SystemExit("STOP_FROZEN_SOURCE_CHANGED:" + relative)
    for name, item in frozen["source_references"].items():
        if sha(PARENT / item["path"].split("../")[-1]) != item["sha256"]:
            raise SystemExit("STOP_PARENT_SOURCE_CHANGED:" + name)
    results = ROOT / "results"
    if results.exists() and any(p.is_file() for p in results.rglob("*")):
        raise SystemExit("STOP_RESULTS_NOT_EMPTY")
    candidate_out = results / "candidate-out"
    audit_out = results / "audit-out"
    candidate_out.mkdir(parents=True, exist_ok=True)
    audit_out.mkdir(parents=True, exist_ok=True)
    candidate_path = candidate_out / "candidate_output.json"
    candidate_cmd = (common() + ro_mount(PARENT / "candidate.py", "/work/candidate.py")
                     + ro_mount(ROOT / "public_input.json", "/work/public_input.json")
                     + rw_mount(candidate_out, "/out")
                     + ["-w", "/work", IMAGE, "python", "-B", "/work/candidate.py",
                        "--input", "/work/public_input.json", "--output", "/out/candidate_output.json"])
    receipt = {"allocation": frozen["allocation"], "started_at_utc": datetime.now(timezone.utc).isoformat(),
               "candidate_docker_run_attempts": 1, "candidate_process_invocations": 1,
               "auditor_process_invocations": 0, "retries": 0,
               "candidate_command": candidate_cmd, "auditor_command": None,
               "candidate_exit": None, "auditor_exit": None, "state": "CANDIDATE_RUNNING"}
    write_json(ROOT / "FORMAL_STARTED.json", receipt)
    candidate_exit = invoke(candidate_cmd, results / "candidate.stdout.txt", results / "candidate.stderr.txt")
    receipt["candidate_exit"] = candidate_exit
    receipt["state"] = "CANDIDATE_COMPLETE" if candidate_exit == 0 else "STOP_CANDIDATE_EXIT_NONZERO"
    write_json(ROOT / "FORMAL_STARTED.json", receipt)
    if candidate_exit != 0 or not candidate_path.is_file():
        write_json(ROOT / "RUN_RECORD.json", receipt)
        raise SystemExit(receipt["state"])

    audit_cmd = (common() + ro_mount(PARENT / "auditor.py", "/work/auditor.py")
                 + ro_mount(ROOT / "public_input.json", "/work/public_input.json")
                 + ro_mount(ROOT / "oracle_input.json", "/work/oracle_input.json")
                 + ro_mount(candidate_path, "/work/candidate_output.json")
                 + rw_mount(audit_out, "/out")
                 + ["-w", "/work", IMAGE, "python", "-B", "/work/auditor.py",
                    "--public", "/work/public_input.json", "--oracle", "/work/oracle_input.json",
                    "--candidate", "/work/candidate_output.json", "--output", "/out/audit.json"])
    receipt["auditor_command"] = audit_cmd
    receipt["auditor_process_invocations"] = 1
    receipt["state"] = "AUDITOR_RUNNING"
    write_json(ROOT / "FORMAL_STARTED.json", receipt)
    auditor_exit = invoke(audit_cmd, results / "auditor.stdout.txt", results / "auditor.stderr.txt")
    receipt["auditor_exit"] = auditor_exit
    receipt["state"] = "COMPLETE" if auditor_exit == 0 else "FAIL_OR_STOP_AUDITOR"
    receipt["candidate_output_sha256"] = sha(candidate_path)
    audit_path = audit_out / "audit.json"
    receipt["audit_sha256"] = sha(audit_path) if audit_path.is_file() else None
    write_json(ROOT / "RUN_RECORD.json", receipt)
    write_json(ROOT / "FORMAL_STARTED.json", receipt)
    if auditor_exit != 0:
        raise SystemExit(receipt["state"])


if __name__ == "__main__":
    main()
