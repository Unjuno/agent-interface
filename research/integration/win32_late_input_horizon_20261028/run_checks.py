"""Run focused Win32 supervisor checks and retain exact command receipts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE_COMMIT = "52df8e2d934bd8b20d4d36da8a7f17a524c49210"
TEST_MODULES = [
    "runtime.guarded_win32_v1.test_operation_owner",
    "runtime.guarded_win32_v1.test_process_cancellation",
    "runtime.cli_v1.test_owned_win32_session",
    "runtime.cli_v1.test_mcp_supervised_backend_composition",
    "runtime.cli_v1.test_mcp_supervised_win32",
    "runtime.cli_v1.test_win32_supervisor_helpers",
    "runtime.cli_v1.test_mcp_win32_composition",
]
SOURCE_FILES = [
    "runtime/guarded_win32_v1/operation_owner.py",
    "runtime/guarded_win32_v1/process_cancellation.py",
    "runtime/guarded_win32_v1/test_process_cancellation.py",
    "runtime/cli_v1/owned_win32_session.py",
    "runtime/cli_v1/mcp_server.py",
    "runtime/cli_v1/win32_supervisor_helpers.py",
    "runtime/cli_v1/test_owned_win32_session.py",
    "runtime/cli_v1/test_mcp_supervised_backend_composition.py",
]


def main() -> None:
    rows = []
    for optimized in (False, True):
        command = [sys.executable]
        if optimized:
            command.append("-O")
        command.extend(["-m", "unittest", *TEST_MODULES])
        started = time.perf_counter_ns()
        result = subprocess.run(command, cwd=ROOT, capture_output=True,
                                text=True, encoding="utf-8", errors="replace")
        rows.append({
            "mode": "optimized" if optimized else "normal",
            "argv": command,
            "exit_code": result.returncode,
            "elapsed_ns": time.perf_counter_ns() - started,
            "stdout": result.stdout,
            "stderr": result.stderr,
        })
    source_hashes = {}
    for relative in SOURCE_FILES:
        source_hashes[relative] = hashlib.sha256(
            (ROOT / relative).read_bytes()).hexdigest()
    output = {
        "schema": "win32-late-input-horizon-checks-v1",
        "source_commit": SOURCE_COMMIT,
        "python_version": sys.version,
        "platform": sys.platform,
        "test_modules": TEST_MODULES,
        "source_sha256": source_hashes,
        "runs": rows,
    }
    destination = HERE / "run_results.json"
    destination.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    for row in rows:
        print(f"{row['mode']}: exit={row['exit_code']} elapsed_ns={row['elapsed_ns']}")
    print(destination)
    if any(row["exit_code"] != 0 for row in rows):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
