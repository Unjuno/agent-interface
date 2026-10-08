"""Verify a frozen dependency tree remains exact in a later checkout."""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def verify_frozen_sources(root: Path, freeze: dict) -> tuple[dict, list[str]]:
    """Check commit ancestry and exact source blobs/bytes without requiring HEAD equality."""
    problems = []
    source_commit = freeze["main_commit"]
    try:
        _git(root, "rev-parse", "--verify", f"{source_commit}^{{commit}}")
    except subprocess.CalledProcessError:
        return {}, ["frozen source commit is unavailable"]

    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", source_commit, "HEAD"],
        cwd=root,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode != 0:
        problems.append("frozen source commit is not an ancestor of checkout")

    source_check = {}
    for relpath, identity in freeze["source_files"].items():
        frozen_blob = _git(root, "rev-parse", f"{source_commit}:{relpath}")
        try:
            checkout_blob = _git(root, "rev-parse", f"HEAD:{relpath}")
        except subprocess.CalledProcessError:
            checkout_blob = None
        path = root / relpath
        worktree_sha = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        source_check[relpath] = {
            "frozen_git_blob": frozen_blob,
            "checkout_git_blob": checkout_blob,
            "worktree_sha256": worktree_sha,
        }
        if (
            frozen_blob != identity["git_blob"]
            or checkout_blob != identity["git_blob"]
            or worktree_sha != identity["sha256"]
        ):
            problems.append(f"source identity mismatch: {relpath}")
    return source_check, problems
