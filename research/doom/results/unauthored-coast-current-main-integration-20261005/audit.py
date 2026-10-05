#!/usr/bin/env python3
"""Verify source identities for the current-main V40 construction package."""
import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    freeze = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))
    candidate = ROOT / freeze["candidate_controller_path"]
    monitor = ROOT / freeze["monitor_path"]
    tests = freeze["tests"]
    checks = {
        "base_head_matches": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
            text=True, check=True).stdout.strip() == freeze["base_main_commit"],
        "base_controller_blob_matches": subprocess.run(
            ["git", "rev-parse", f"HEAD:{freeze['base_controller_path']}"],
            cwd=ROOT, capture_output=True, text=True,
            check=True).stdout.strip() == freeze["base_controller_git_blob"],
        "candidate_controller_sha256_matches": sha(candidate) ==
            freeze["controller_sha256"].lower(),
        "monitor_sha256_matches": sha(monitor) == freeze["monitor_sha256"].lower(),
        "candidate_controller_test_sha256_matches": sha(ROOT / tests[
            "candidate_controller"]) == tests["candidate_controller_sha256"].lower(),
        "monitor_test_sha256_matches": sha(ROOT / tests["monitor"]) ==
            tests["monitor_sha256"].lower(),
    }
    result = {"schema": "issue59-unauthored-coast-current-main-audit-v1",
              "checks": checks, "pass": all(checks.values())}
    (PACKAGE / "AUDIT.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
