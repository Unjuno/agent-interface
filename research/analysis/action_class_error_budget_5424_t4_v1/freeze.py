#!/usr/bin/env python3
"""Generate the pre-run T4 source/input freeze; no formal outputs are read."""
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BASE = "43f7cd88d91af05036fae2100ec4e155c59e105c"
BRANCH = "research/5424-ranking-inversion-t4-20261002"
ALLOCATION = "ACTION-ERROR-BUDGET-5424-T4-RANKING-INVERSION-HOSTCPU-20261003-01"
FILES = ["PLAN.md", "fixtures.json", "candidate.py", "audit.py", "test_contract.py", "freeze.py"]
OUTPUTS = ["raw/formal_01/candidate_result.json", "raw/formal_01/candidate_receipt.json", "raw/formal_01/audit_result.json"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def main():
    if subprocess.call(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", BASE, "HEAD"]) != 0:
        raise SystemExit("STOP_BASE_NOT_ANCESTOR")
    if git("branch", "--show-current") != BRANCH:
        raise SystemExit("STOP_BRANCH_MISMATCH")
    if (ROOT / "FREEZE.json").exists() or (ROOT / "raw/formal_01").exists():
        raise SystemExit("STOP_FREEZE_OR_OUTPUT_COLLISION")
    absent = [rel for rel in OUTPUTS if (ROOT / rel).exists()]
    if absent:
        raise SystemExit("STOP_OUTPUT_COLLISION:" + ",".join(absent))
    record = {
        "schema": "action-class-error-budget-t4-freeze-v1",
        "allocation_id": ALLOCATION,
        "issue": "https://github.com/Unjuno/agent-interface/issues/5424",
        "owner_thread": "01a0b990-3d17-72f1-a908-9a2072104ce5",
        "base_main_sha": BASE,
        "branch": BRANCH,
        "window_start_utc": "2026-10-02T16:00:00Z",
        "window_end_utc": "2026-10-02T16:30:00Z",
        "execution_scope": "Windows host CPU; standard-library Python; no GPU/CUDA/model/GUI/WSL/WSLc/Docker/network",
        "python": sys.version,
        "platform": platform.platform(),
        "frozen_sha256": {rel: sha(ROOT / rel) for rel in FILES},
        "candidate_command": "python -B candidate.py --fixture fixtures.json --out raw/formal_01",
        "auditor_command": "python -B audit.py",
        "candidate_invocation_limit": 1,
        "auditor_invocation_limit": 1,
        "retry_limit": 0,
        "formal_output_paths_absent_at_freeze": OUTPUTS,
    }
    (ROOT / "FREEZE.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
