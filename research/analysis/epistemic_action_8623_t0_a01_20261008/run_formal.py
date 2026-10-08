#!/usr/bin/env python3
"""One-shot candidate/auditor runner with exact raw-byte custody."""

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def execute(command, stdin=None):
    start = time.perf_counter_ns()
    proc = subprocess.run(command, cwd=ROOT, input=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return proc, time.perf_counter_ns() - start


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    output = Path(args.output_dir).resolve()
    if output.exists():
        print("OUTPUT_DIR_EXISTS", file=sys.stderr)
        return 2

    output.mkdir(parents=True)
    started_utc = datetime.now(timezone.utc).isoformat()
    fixture = ROOT / "fixture.json"
    oracle = ROOT / "oracle.json"
    py = sys.executable
    candidate_command = [py, str(ROOT / "candidate.py"), "--fixture", str(fixture)]
    candidate, candidate_elapsed = execute(candidate_command)
    (output / "raw_candidate.json").write_bytes(candidate.stdout)
    (output / "candidate.stderr").write_bytes(candidate.stderr)

    record = {
        "schema": "epistemic-action-run-v1",
        "allocation": "EPISTEMIC-ACTION-8623-T0-A01-20261008",
        "started_utc": started_utc,
        "python": sys.version,
        "platform": platform.platform(),
        "candidate_command": ["<sys.executable>", "candidate.py", "--fixture", "fixture.json"],
        "candidate_invocations": 1,
        "candidate_exit_code": candidate.returncode,
        "candidate_elapsed_ns": candidate_elapsed,
        "candidate_stdout_bytes": len(candidate.stdout),
        "candidate_stdout_sha256": digest(candidate.stdout),
        "candidate_stderr_bytes": len(candidate.stderr),
        "candidate_stderr_sha256": digest(candidate.stderr),
        "auditor_invocations": 0,
        "retries": 0,
    }

    if candidate.returncode != 0:
        record["formal_disposition"] = "STOP_CANDIDATE_EXIT_NONZERO"
        (output / "RUN.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(record, sort_keys=True, separators=(",", ":")))
        return 1

    auditor_command = [py, str(ROOT / "auditor.py"), "--fixture", str(fixture), "--oracle", str(oracle)]
    auditor, auditor_elapsed = execute(auditor_command, stdin=candidate.stdout)
    (output / "raw_audit.json").write_bytes(auditor.stdout)
    (output / "auditor.stderr").write_bytes(auditor.stderr)
    audit_payload = None
    try:
        audit_payload = json.loads(auditor.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        pass
    audit_valid = isinstance(audit_payload, dict) and audit_payload.get("schema") == "epistemic-action-audit-v1" and audit_payload.get("rows_reconstructed") == 18
    record.update({
        "auditor_command": ["<sys.executable>", "auditor.py", "--fixture", "fixture.json", "--oracle", "oracle.json", "<raw_candidate.json on stdin>"],
        "auditor_invocations": 1,
        "auditor_exit_code": auditor.returncode,
        "auditor_elapsed_ns": auditor_elapsed,
        "auditor_stdout_bytes": len(auditor.stdout),
        "auditor_stdout_sha256": digest(auditor.stdout),
        "auditor_stderr_bytes": len(auditor.stderr),
        "auditor_stderr_sha256": digest(auditor.stderr),
        "auditor_output_valid": audit_valid,
        "hypothesis_disposition": audit_payload.get("hypothesis_disposition") if audit_valid else None,
        "formal_disposition": "PASS_METHOD_SCOPED" if auditor.returncode == 0 and not auditor.stderr and audit_valid else "HOLD_AUDITOR_FAILURE",
    })
    (output / "RUN.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(record, sort_keys=True, separators=(",", ":")))
    return 0 if record["formal_disposition"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
