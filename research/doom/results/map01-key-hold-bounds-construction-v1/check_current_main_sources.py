"""Read-only compare current main source bytes with the historical freeze."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]


def check():
    freeze = json.loads((ROOT / "PRE-RUN.json").read_text(encoding="utf-8"))
    main_sha = subprocess.run(
        ["git", "rev-parse", "origin/main"], cwd=REPO, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    source_checks = {}
    for name, expected in freeze["source_sha256"].items():
        if not name.startswith("research/live_control/"):
            continue
        result = subprocess.run(
            ["git", "show", f"origin/main:{name}"], cwd=REPO,
            capture_output=True,
        )
        actual = hashlib.sha256(result.stdout).hexdigest() if result.returncode == 0 else None
        source_checks[name] = {
            "frozen_sha256": expected,
            "current_main_sha256": actual,
            "matches_frozen": actual == expected,
        }
    mismatches = [name for name, item in source_checks.items() if not item["matches_frozen"]]
    report = {
        "current_main": main_sha,
        "historical_frozen_base": freeze["base_commit"],
        "historical_frozen_pr_head": freeze["pr_head"],
        "source_count": len(source_checks),
        "matching_count": len(source_checks) - len(mismatches),
        "drifted_paths": mismatches,
        "read_only": True,
        "candidate_executed": False,
        "artifacts_written": False,
    }
    print(json.dumps(report, sort_keys=True))
    return report


if __name__ == "__main__":
    check()
