#!/usr/bin/env python3
"""Capture exact stdout/stderr and a receipt for the stdlib raw-only audit."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if len(sys.argv) != 3:
    raise SystemExit("usage: run_capture.py RETAINED_ARTIFACT_ROOT OUTPUT_DIR")

artifact_root = Path(sys.argv[1]).resolve()
output_dir = Path(sys.argv[2]).resolve()
output_dir.mkdir(parents=True, exist_ok=True)
result_path = output_dir / "READONLY_AUDIT.json"
stdout_path = output_dir / "audit.stdout.bin"
stderr_path = output_dir / "audit.stderr.bin"
capture_path = Path(__file__).resolve().parent
auditor_path = capture_path / "audit_raw_stdlib.py"
argv = [sys.executable, "-B", str(auditor_path), str(artifact_root), str(result_path)]
started = datetime.now(timezone.utc).isoformat()
completed = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
ended = datetime.now(timezone.utc).isoformat()
stdout_path.write_bytes(completed.stdout)
stderr_path.write_bytes(completed.stderr)
receipt = {
    "schema": "issue4895-readonly-stdlib-run-v1",
    "allocation": "needle-online-lora-role-rehearsal-20260927-v1",
    "audit_kind": "posthoc raw-only integrity and recorded-prediction recomputation",
    "host_platform": platform.platform(),
    "python": sys.version,
    "started_utc": started,
    "completed_utc": ended,
    "command_argv": argv,
    "exit_code": completed.returncode,
    "formal_seed_runs": 0,
    "model_loads": 0,
    "optimizer_fits": 0,
    "gpu_invocations": 0,
    "docker_invocations": 0,
    "predecessor_bytes_modified": False,
    "artifacts": {
        "auditor_sha256": sha(auditor_path),
        "result_sha256": sha(result_path),
        "stdout_bytes": len(completed.stdout),
        "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderr_bytes": len(completed.stderr),
        "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
    },
}
(output_dir / "RUN.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
print(json.dumps({"exit_code": completed.returncode,
                  "result_sha256": receipt["artifacts"]["result_sha256"],
                  "stdout_sha256": receipt["artifacts"]["stdout_sha256"],
                  "stderr_sha256": receipt["artifacts"]["stderr_sha256"]}, sort_keys=True))
raise SystemExit(completed.returncode)
