#!/usr/bin/env python3
"""Write the one-shot A03 pre-candidate source/environment freeze."""
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
FROZEN_FILES = (
    "PLAN.md", "README.md", "ENVIRONMENT.md", "CONSTRUCTION.md", "PREFLIGHT.json",
    "candidate_input.json", "oracle_truth.json", "run_candidate.py", "audit_result.py",
    "test_construction.py", "seal_freeze.py",
)
SOURCE_DOCS = (
    "docs/CURRENT_GOAL.md", "docs/WORKER_QUICKSTART.md", "docs/RESEARCH_METHOD.md",
    "docs/ISSUE_FAILURE_CLASSIFICATION.md", "docs/RESEARCH_ISSUE_INDEX.md",
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def main():
    path = ROOT / "FREEZE.json"
    if path.exists():
        raise SystemExit("FREEZE.json already exists; refusing overwrite")
    docs = {
        name: digest(subprocess.check_output(["git", "show", f"HEAD:{name}"], cwd=REPO))
        for name in SOURCE_DOCS
    }
    freeze = {
        "study": "issue-5865-negative-delivery-t0a-a03",
        "phase": "pre_candidate_freeze",
        "repository_head": git("rev-parse", "HEAD"),
        "repository_tree": git("rev-parse", "HEAD^{tree}"),
        "latest_origin_main": git("rev-parse", "origin/main"),
        "source_document_sha256": docs,
        "experiment_file_sha256": {
            name: digest((ROOT / name).read_bytes()) for name in FROZEN_FILES
        },
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "container": "not used; CPU-only standard-library finite simulator",
        },
        "candidate_invocations": 1,
        "auditor_invocations": 1,
    }
    path.write_text(json.dumps(freeze, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
