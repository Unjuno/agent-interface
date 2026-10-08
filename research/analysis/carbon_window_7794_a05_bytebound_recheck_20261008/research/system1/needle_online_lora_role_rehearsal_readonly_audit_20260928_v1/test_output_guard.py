#!/usr/bin/env python3
"""Verify run_capture refuses a non-empty output directory without changes."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


def tree_hashes(path: Path):
    return {
        str(file.relative_to(path)).replace("\\", "/"): hashlib.sha256(file.read_bytes()).hexdigest()
        for file in path.rglob("*") if file.is_file()
    }


if len(sys.argv) != 4:
    raise SystemExit("usage: test_output_guard.py RETAINED_ARTIFACT_ROOT NONEMPTY_OUTPUT_DIR RECEIPT_JSON")

artifact_root = Path(sys.argv[1]).resolve()
output_dir = Path(sys.argv[2]).resolve()
receipt_path = Path(sys.argv[3]).resolve()
if not output_dir.is_dir() or not any(output_dir.iterdir()):
    raise SystemExit("test_precondition_requires_nonempty_output_dir")
before = tree_hashes(output_dir)
completed = subprocess.run(
    [sys.executable, "-B", str(Path(__file__).with_name("run_capture.py")),
     str(artifact_root), str(output_dir)],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
)
after = tree_hashes(output_dir)
result = {
    "schema": "issue4895-readonly-output-guard-test-v1",
    "decision": "PASS_NONEMPTY_OUTPUT_REFUSED" if (
        completed.returncode != 0
        and completed.stdout == b""
        and completed.stderr.strip() == b"STOP_OUTPUT_NOT_EMPTY"
        and before == after
    ) else "FAIL_OUTPUT_GUARD",
    "nonempty_output_refused": completed.returncode != 0 and completed.stderr.strip() == b"STOP_OUTPUT_NOT_EMPTY",
    "preexisting_file_count": len(before),
    "all_existing_bytes_unchanged": before == after,
    "exit_code": completed.returncode,
    "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
    "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
}
receipt_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if result["decision"] == "PASS_NONEMPTY_OUTPUT_REFUSED" else 1)
