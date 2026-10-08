#!/usr/bin/env python3
"""Freeze source provenance and hash all retained construction evidence."""

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = "6ea1269defb6d48a607f13b08f1aa2d223ba06e9"
CONTROLLER = Path("research/doom/map01_overlap_controller_v39.py")
EXECUTOR = Path("research/live_control/executor_v12.py")
TEST = Path("research/doom/test_map01_completed_future_drain_v1.py")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    provenance = {
        "schema": "v39_completed_future_drain_source_provenance_v1",
        "repository": "Unjuno/agent-interface",
        "base_commit": BASE,
        "base_controller_git_blob": git("rev-parse", f"{BASE}:{CONTROLLER.as_posix()}"),
        "base_controller_sha256": "02a6289390837bb97198c98fe03c41c775d829bf6606fc4c11085630b3de0793",
        "base_executor_v12_git_blob": git("rev-parse", f"{BASE}:{EXECUTOR.as_posix()}"),
        "base_executor_v12_sha256": "e78440263866dd06eaf868e902ae50b08aa2b634f086bfbd412f6c338ccea2b2",
        "candidate_controller_sha256": sha(ROOT / CONTROLLER),
        "regression_test_sha256": sha(ROOT / TEST),
        "baseline_replay": "results/baseline-01/report.json",
        "postfix_checks": "results/postfix-01/report.json",
        "environment": {"python": sys.version, "platform": platform.platform()},
        "classification": "deterministic construction regression; no live allocation",
    }
    (HERE / "SOURCE_PROVENANCE.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    files = sorted(path for path in HERE.rglob("*") if path.is_file()
                   and path.name not in {"SHA256SUMS", "audit_result.json"}
                   and "__pycache__" not in path.parts and path.suffix != ".pyc")
    files.extend((ROOT / CONTROLLER, ROOT / TEST))
    rows = []
    for path in sorted(set(files), key=lambda p: str(p)):
        try:
            label = path.relative_to(HERE).as_posix()
        except ValueError:
            label = Path("../") / path.relative_to(HERE.parent)
            label = label.as_posix()
        rows.append(f"{sha(path)}  {label}")
    (HERE / "SHA256SUMS").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"provenance": provenance, "manifest_files": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
