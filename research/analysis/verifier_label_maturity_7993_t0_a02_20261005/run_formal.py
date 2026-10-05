"""Exclusive one-shot native-host driver for 7993-T0-A02."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ALLOCATION = "UNJUNO-7993-VERIFIER-LABEL-MATURITY-T0-A02-MACOS-HOST-20261005"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resource_snapshot() -> dict:
    stat = os.statvfs(ROOT)
    return {
        "cpu_count_logical": os.cpu_count(),
        "load_average_1_5_15": list(os.getloadavg()),
        "available_disk_bytes": stat.f_bavail * stat.f_frsize,
        "host": platform.platform(),
        "machine": platform.machine(),
        "python": sys.version,
        "network_enforcement": "none; not claimed",
        "container": "none; native host substitution",
    }


def verify_frozen_sources() -> dict:
    frozen = json.loads((ROOT / "FROZEN.json").read_text(encoding="utf-8"))
    mismatches = []
    for name, expected in frozen["files"].items():
        path = ROOT / name
        if not path.is_file() or sha256(path) != expected:
            mismatches.append(name)
    return {"frozen": frozen, "mismatches": mismatches}


def main() -> int:
    checked = verify_frozen_sources()
    if checked["mismatches"]:
        raise SystemExit(f"frozen source mismatch: {checked['mismatches']}")
    marker = ROOT / "formal_started.json"
    marker_data = {
        "allocation": ALLOCATION,
        "driver_invocations": 1,
        "started_at_utc": utc_now(),
        "formal_candidate_auditor_invocations_before": {"candidate": 0, "auditor": 0},
        "retry_policy": "zero retries; exclusive-create marker",
        "frozen_manifest_sha256": sha256(ROOT / "FROZEN.json"),
    }
    fd = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(marker_data, stream, indent=2, sort_keys=True)
        stream.write("\n")

    before = resource_snapshot()
    started = time.monotonic()
    candidate_command = [
        sys.executable,
        "-B",
        "candidate.py",
        "--input",
        "public_input.json",
        "--output",
        "formal_output.json",
    ]
    candidate = subprocess.run(
        candidate_command,
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    (ROOT / "candidate.stdout.txt").write_text(candidate.stdout, encoding="utf-8")
    (ROOT / "candidate.stderr.txt").write_text(candidate.stderr, encoding="utf-8")

    auditor_command = None
    auditor = None
    if candidate.returncode == 0:
        auditor_command = [
            sys.executable,
            "-B",
            "audit.py",
            "--input",
            "public_input.json",
            "--truth",
            "auditor_truth.json",
            "--candidate",
            "formal_output.json",
            "--output",
            "audit.json",
        ]
        auditor = subprocess.run(
            auditor_command,
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        (ROOT / "auditor.stdout.txt").write_text(auditor.stdout, encoding="utf-8")
        (ROOT / "auditor.stderr.txt").write_text(auditor.stderr, encoding="utf-8")
    else:
        (ROOT / "auditor.stdout.txt").write_text("NOT_INVOKED\n", encoding="utf-8")
        (ROOT / "auditor.stderr.txt").write_text("NOT_INVOKED\n", encoding="utf-8")

    disposition = "STOP_CANDIDATE_NONZERO"
    audit_disposition = "NOT_RUN"
    if auditor is not None and auditor.returncode == 0:
        audit_result = json.loads((ROOT / "audit.json").read_text(encoding="utf-8"))
        audit_disposition = audit_result["disposition"]
        disposition = audit_disposition
    after = resource_snapshot()
    outputs = [
        "formal_output.json",
        "audit.json",
        "candidate.stdout.txt",
        "candidate.stderr.txt",
        "auditor.stdout.txt",
        "auditor.stderr.txt",
    ]
    terminal = {
        "allocation": ALLOCATION,
        "disposition": disposition,
        "audit_disposition": audit_disposition,
        "started_at_utc": marker_data["started_at_utc"],
        "finished_at_utc": utc_now(),
        "elapsed_seconds": time.monotonic() - started,
        "driver_invocations": 1,
        "candidate_invocations": 1,
        "candidate_exit": candidate.returncode,
        "candidate_command": candidate_command,
        "auditor_invocations": 1 if auditor is not None else 0,
        "auditor_exit": auditor.returncode if auditor is not None else None,
        "auditor_command": auditor_command,
        "retries": 0,
        "container": "none; native host execution only",
        "network": "no network calls by candidate/auditor; not OS-isolated",
        "environment_before": before,
        "environment_after": after,
        "freeze_manifest_sha256": sha256(ROOT / "FROZEN.json"),
        "output_sha256": {name: sha256(ROOT / name) for name in outputs if (ROOT / name).is_file()},
    }
    (ROOT / "terminal.json").write_text(
        json.dumps(terminal, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(terminal, sort_keys=True))
    return 0 if disposition == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
