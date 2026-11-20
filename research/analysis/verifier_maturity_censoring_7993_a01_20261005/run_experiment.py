#!/usr/bin/env python3
"""One frozen candidate execution followed by one separate raw-only audit."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
PROTOCOL = "issue-7993-t0-a01-v1"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_check(frozen: dict) -> list[str]:
    errors = []
    for rel, expected in frozen["source_sha256"].items():
        got = digest((ROOT / rel).read_bytes())
        if got != expected:
            errors.append(f"{rel}:expected={expected}:actual={got}")
    return errors


def run_one(name: str, command: list[str], out_dir: Path) -> dict:
    proc = subprocess.run(command, cwd=ROOT, capture_output=True, check=False)
    stdout_path, stderr_path = out_dir / f"{name}.stdout.txt", out_dir / f"{name}.stderr.txt"
    stdout_path.write_bytes(proc.stdout)
    stderr_path.write_bytes(proc.stderr)
    return {
        "command": command,
        "exit_code": proc.returncode,
        "stdout": {"path": stdout_path.name, "bytes": len(proc.stdout), "sha256": digest(proc.stdout)},
        "stderr": {"path": stderr_path.name, "bytes": len(proc.stderr), "sha256": digest(proc.stderr)},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    frozen = json.loads((ROOT / "FROZEN.json").read_text(encoding="utf-8"))
    if frozen.get("protocol") != PROTOCOL:
        raise SystemExit("FROZEN protocol mismatch")
    source_errors = source_check(frozen)
    if source_errors:
        (out_dir / "source-check-errors.json").write_text(
            json.dumps(source_errors, indent=2) + "\n", encoding="utf-8")
        return 2

    py = sys.executable
    candidate_output = out_dir / "candidate.raw.json"
    audit_output = out_dir / "audit.raw.json"
    candidate_run = run_one("candidate", [
        py, "-B", "candidate.py", "--input", str(ROOT / "candidate_input.json"),
        "--output", str(candidate_output),
    ], out_dir)
    audit_run = None
    if candidate_run["exit_code"] == 0:
        audit_run = run_one("auditor", [
            py, "-B", "audit.py", "--candidate", str(candidate_output),
            "--output", str(audit_output), "--candidate-input", str(ROOT / "candidate_input.json"),
            "--oracle-input", str(ROOT / "oracle_input.json"),
        ], out_dir)

    receipt = {
        "protocol": PROTOCOL,
        "command": "python -B run_experiment.py --output-dir /out",
        "image": frozen["environment"]["image"],
        "python": platform.python_version(),
        "platform": platform.platform(),
        "source_sha256": frozen["source_sha256"],
        "source_hash_check": "PASS",
        "candidate": candidate_run,
        "auditor": audit_run,
        "output_sha256": {
            path.name: digest(path.read_bytes())
            for path in (candidate_output, audit_output) if path.exists()
        },
    }
    receipt_path = out_dir / "run_receipt.json"
    receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    ok = candidate_run["exit_code"] == 0 and audit_run is not None and audit_run["exit_code"] == 0
    print(json.dumps({"protocol": PROTOCOL, "pass": ok, "receipt": receipt_path.name,
                      "candidate_exit": candidate_run["exit_code"],
                      "auditor_exit": None if audit_run is None else audit_run["exit_code"]}, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
