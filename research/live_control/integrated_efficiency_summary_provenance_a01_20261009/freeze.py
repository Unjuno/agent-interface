#!/usr/bin/env python3
"""Freeze exact inputs and environment for provenance audit A01."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import platform
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FILES = [
    "audit.py",
    "verify.py",
    "manifest.py",
    "EXECUTION.json",
    "CONSTRUCTION_FAILURE_A01.md",
    "CONSTRUCTION_FAILURE_A00.md",
    "inputs/pr-2962.json",
    "inputs/pr-2962-files.json",
    "inputs/issue-2558-final-comment.json",
    "inputs/merge-commit-paths.txt",
    "research/live_control/results/integrated-efficiency-live-01-summary.json",
    "research/live_control/results/integrated-efficiency-live-01-summary-reconciliation-v1.json",
    "research/live_control/results/integrated-efficiency-live-01/trace.json",
    "research/live_control/results/integrated-efficiency-live-01/report.json",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    rows = []
    for name in FILES:
        path = HERE / name if name.startswith(("audit.py", "verify.py", "manifest.py", "EXECUTION.json", "CONSTRUCTION_FAILURE", "inputs/")) else ROOT / name
        rows.append({"path": name, "sha256": sha(path), "bytes": path.stat().st_size})
    output = {
        "schema": "integrated_efficiency_summary_provenance_a01_freeze_v1",
        "study": "integrated-efficiency-live-01-summary-provenance-a01",
        "repository_head": "743ae74ec5be2472ff27fa06fe13d5ecf8534de5",
        "source_main_commit": "9c9d7cf2bea50e47638c63effa72a5059fdb4e58",
        "provenance_commit": "13d0ccbf2559cc1f70aa2652497ae941ceb13eb7",
        "environment": {
            "os": platform.platform(),
            "python": sys.version,
            "execution": "native Ubuntu WSL2; no container boundary used",
            "wsl_package_version": "2.7.13.0",
            "wslc_available": False,
        },
        "inputs": rows,
    }
    (HERE / "FREEZE.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
