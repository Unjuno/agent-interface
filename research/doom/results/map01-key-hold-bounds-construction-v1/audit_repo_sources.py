"""Bind the frozen source-copy hashes to this repository checkout."""
import hashlib
import json
import sys
from pathlib import Path


result_dir = Path(__file__).resolve().parent
repo_root = result_dir.parents[3]
freeze = json.loads((result_dir / "PRE-RUN.json").read_text(encoding="utf-8"))
checks = {}
for name, expected in freeze["source_sha256"].items():
    if not name.startswith("research/live_control/"):
        continue
    tracked = repo_root / name
    frozen_copy = result_dir / name
    tracked_hash = hashlib.sha256(tracked.read_bytes()).hexdigest() if tracked.is_file() else None
    copy_hash = hashlib.sha256(frozen_copy.read_bytes()).hexdigest() if frozen_copy.is_file() else None
    checks[name] = {
        "expected_sha256": expected,
        "tracked_sha256": tracked_hash,
        "frozen_copy_sha256": copy_hash,
        "pass": tracked_hash == expected and copy_hash == expected,
    }

out = {
    "freeze_pr_head": freeze["pr_head"],
    "freeze_base_commit": freeze["base_commit"],
    "repository_source_checks": checks,
    "passed": bool(checks) and all(item["pass"] for item in checks.values()),
}
(result_dir / "REPO-SOURCE-AUDIT.json").write_text(
    json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
print(json.dumps(out, sort_keys=True))
sys.exit(0 if out["passed"] else 1)
