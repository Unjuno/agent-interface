"""Create the immutable current-main source pin file for A01."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
BASE_COMMIT = "02953aa83d62e69a787de7732bf172f3f8ef8e1c"
SOURCE_PATHS = [
    "runtime/guarded_x11_v1/frames.py",
    "runtime/guarded_x11_v1/handles_base.py",
    "runtime/guarded_x11_v1/handles_texture.py",
    "runtime/guarded_x11_v1/handles.py",
]


def main():
    records = {}
    for relative in SOURCE_PATHS:
        blob = subprocess.check_output(
            ["git", "rev-parse", f"{BASE_COMMIT}:{relative}"], cwd=REPO, text=True).strip()
        git_content = subprocess.check_output(
            ["git", "show", f"{BASE_COMMIT}:{relative}"], cwd=REPO)
        worktree_content = (REPO / relative).read_bytes()
        records[relative] = {
            "git_blob": blob,
            "git_blob_sha256": hashlib.sha256(git_content).hexdigest(),
            "git_blob_bytes": len(git_content),
            "worktree_sha256": hashlib.sha256(worktree_content).hexdigest(),
            "worktree_bytes": len(worktree_content),
        }
    result = {"schema": "coordinate-grounding-a01-freeze-v1",
              "repository": "Unjuno/agent-interface", "source_commit": BASE_COMMIT,
              "sources": records,
              "scope": "runtime target-handle source only; synthetic construction; no model/gui/input"}
    (PACKAGE / "FREEZE.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                        encoding="utf-8", newline="\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
