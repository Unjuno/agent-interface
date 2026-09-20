#!/usr/bin/env python3
"""Verify all original manifest paths and raw bytes in a Git commit tree."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
MANIFEST = "research/integration/issue_3370_stale_source_rejection_v1/evidence/manifest.json"


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(REPO), *args])


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: audit_git_tree.py COMMIT", file=sys.stderr)
        return 2
    commit = sys.argv[1]
    manifest = json.loads(git("show", f"{commit}:{MANIFEST}"))
    missing, mismatched = [], []
    for row in manifest["files"]:
        path = "research/integration/issue_3370_stale_source_rejection_v1/" + row["path"]
        try:
            payload = git("show", f"{commit}:{path}")
        except subprocess.CalledProcessError:
            missing.append(path)
            continue
        if len(payload) != row["bytes"] or hashlib.sha256(payload).hexdigest() != row["sha256"]:
            mismatched.append(path)
    result = {
        "schema": "agent-interface/issue-3370-publication-closure-audit-v1",
        "commit": git("rev-parse", commit).decode().strip(),
        "manifest_entries": len(manifest["files"]),
        "tree_entries_verified": len(manifest["files"]) - len(missing) - len(mismatched),
        "missing": missing,
        "mismatched": mismatched,
        "result": "PASS_PUBLICATION_CLOSED" if not missing and not mismatched else "HOLD_PUBLICATION_INCOMPLETE",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["result"] == "PASS_PUBLICATION_CLOSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
