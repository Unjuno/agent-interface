#!/usr/bin/env python3
"""Read-only freeze verifier; exits nonzero on any frozen-input drift."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "research/analysis/chromium_temporal_focus_payload_1998_t0_a10_20261009"


def main():
    freeze = json.loads((PACKAGE / "FREEZE.json").read_text())
    errors = []
    for relative, expected in freeze["frozen_inputs_sha256"].items():
        path = ROOT / relative
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if actual != expected:
            errors.append({"path": relative, "expected": expected, "actual": actual})
    if (PACKAGE / "results").exists():
        errors.append({"path": "results/", "error": "exists before formal run"})
    recorded = freeze["source_anchor_before_freeze"]
    current = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", recorded, current], cwd=ROOT, check=False).returncode == 0
    if not ancestor:
        errors.append({"path": "HEAD", "error": "freeze source anchor is not an ancestor of current HEAD"})
    report = {"status": "PASS" if not errors else "FAIL", "checked_files": len(freeze["frozen_inputs_sha256"]), "errors": errors}
    print(json.dumps(report, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
