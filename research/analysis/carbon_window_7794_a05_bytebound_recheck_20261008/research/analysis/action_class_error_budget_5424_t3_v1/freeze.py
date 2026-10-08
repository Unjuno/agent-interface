#!/usr/bin/env python3
"""Write the pre-candidate source/input freeze manifest."""
import hashlib
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILES = ("PLAN.md", "fixtures.json", "candidate.py", "audit.py", "freeze.py")


def main():
    manifest = {
        "schema": "action-class-error-budget-selective-labels-freeze-v1",
        "allocation": "error-budget-selective-labels-5424-t3-20261001-01",
        "repo": "Unjuno/agent-interface",
        "publication_base": "49db21e330768800e8b3486203b70306f4e402f6",
        "branch": "research/5424-selective-labels-t3-20261001",
        "path": "research/analysis/action_class_error_budget_5424_t3_v1/",
        "execution": "host-only; deterministic; Python standard library; no Docker/runtime/model/GUI/input",
        "python": sys.version,
        "platform": platform.platform(),
        "files": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES},
        "candidate_invocations_before_freeze": 0,
        "auditor_invocations_before_freeze": 0,
        "candidate_invocation_limit": 1,
        "auditor_invocation_limit": 1,
        "retries": 0,
    }
    (ROOT / "FREEZE.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
