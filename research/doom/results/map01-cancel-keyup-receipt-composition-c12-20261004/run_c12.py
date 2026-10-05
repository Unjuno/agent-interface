"""Run and byte-preserve the frozen C12 unittest invocation."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COMPOSITION_MODULES = (
    "candidate.live_control.test_composed_cancel_keyup_boundary",
    "candidate.doom.test_release_backend_v3_composition",
    "candidate.doom.test_multikey_release_batch_v3",
)
CONTROL_MODULE = "candidate.live_control.test_executor_owner_cancel_cause_v1"


def main() -> int:
    runs = (
        ("composition", COMPOSITION_MODULES),
        ("publication-control", (CONTROL_MODULE,)),
    )
    overall = 0
    for label, modules in runs:
        command = [sys.executable, "-B", "-m", "unittest", *modules, "-v"]
        result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (ROOT / f"raw/{label}-output.txt").write_bytes(result.stdout)
        (ROOT / f"raw/{label}-exit.txt").write_text(str(result.returncode), encoding="utf-8")
        sys.stdout.write(f"=== {label} ===\n")
        sys.stdout.buffer.write(result.stdout)
        overall = overall or result.returncode
    return overall


if __name__ == "__main__":
    raise SystemExit(main())
