"""Materialize only import-required parent files, preserving exact Git bytes."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


PARENT = "ef190e1037ff2f9df0cb2e941578a79a9fe0019b"
FILES = (
    "runtime/backends/win32_v1/backend.py",
    "runtime/backends/win32_v1/session.py",
    "runtime/core_v1/contract.py",
)


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: prepare_baseline.py REPO_ROOT OUTPUT_ROOT")
    repo = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    output.mkdir(parents=True, exist_ok=False)
    for relative in FILES:
        result = subprocess.run(
            ["git", "show", f"{PARENT}:{relative}"],
            cwd=repo,
            check=True,
            stdout=subprocess.PIPE,
        )
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(result.stdout)
    for relative in (
        "runtime/backends/win32_v1/fixture_app.py",
        "runtime/backends/win32_v1/test_focus_drift.py",
    ):
        shutil.copyfile(repo / relative, output / relative)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
