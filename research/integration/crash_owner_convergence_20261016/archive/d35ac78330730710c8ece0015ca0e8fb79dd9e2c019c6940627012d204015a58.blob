"""Fail-closed pre-execution gate for frozen Python research candidates.

This validator never imports or runs a candidate. It checks the manifest,
harness, runner, candidate source hash, and the candidate's literal embedded
allocation_id before a separate runner may start any experiment process.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def allocation_ids(candidate: Path) -> list[str]:
    tree = ast.parse(candidate.read_text(encoding="utf-8"), filename=str(candidate))
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key, value in zip(node.keys, node.values):
            if (isinstance(key, ast.Constant) and key.value == "allocation_id"
                    and isinstance(value, ast.Constant) and isinstance(value.value, str)):
                found.append(value.value)
    return found


def validate(freeze_path: Path, harness_path: Path,
             candidate_path: Path, runner_path: Path) -> dict:
    errors: list[str] = []
    freeze = json.loads(freeze_path.read_text(encoding="utf-8-sig"))
    harness = json.loads(harness_path.read_text(encoding="utf-8-sig"))
    allocation = freeze.get("allocation_id")
    if not isinstance(allocation, str) or not allocation:
        errors.append("freeze allocation_id missing")
    if harness.get("allocation_id") != allocation:
        errors.append("harness/freeze allocation_id mismatch")

    freeze_files = freeze.get("files")
    if not isinstance(freeze_files, list) or not freeze_files:
        errors.append("freeze files missing")
        freeze_files = []
    normalized_candidate = candidate_path.as_posix()
    candidate_entry_found = False
    for entry in freeze_files:
        if not isinstance(entry, dict):
            errors.append("invalid freeze file entry")
            continue
        relative = entry.get("path")
        expected = entry.get("sha256")
        if not isinstance(relative, str) or not isinstance(expected, str):
            errors.append("freeze path/hash missing")
            continue
        source = Path(relative)
        if source.as_posix() == normalized_candidate:
            candidate_entry_found = True
        if not source.is_file():
            errors.append(f"frozen file missing: {relative}")
        elif sha256(source) != expected:
            errors.append(f"frozen file hash mismatch: {relative}")
    if not candidate_entry_found:
        errors.append("candidate is not listed in freeze manifest")

    expected_freeze_hash = harness.get("freeze_sha256")
    if not isinstance(expected_freeze_hash, str) or sha256(freeze_path) != expected_freeze_hash:
        errors.append("freeze manifest hash mismatch")
    expected_runner = harness.get("runner_path")
    expected_runner_hash = harness.get("runner_sha256")
    if expected_runner != runner_path.as_posix():
        errors.append("harness/runner path mismatch")
    if not isinstance(expected_runner_hash, str) or sha256(runner_path) != expected_runner_hash:
        errors.append("runner hash mismatch")

    try:
        ids = allocation_ids(candidate_path)
    except (OSError, SyntaxError, UnicodeError) as exc:
        ids = []
        errors.append(f"candidate parse failed: {type(exc).__name__}: {exc}")
    if len(ids) != 1:
        errors.append(f"candidate must contain exactly one literal allocation_id; found {len(ids)}")
    elif ids[0] != allocation:
        errors.append(f"candidate/freeze allocation_id mismatch: {ids[0]} != {allocation}")

    return {
        "schema": "frozen-candidate-gate-v1",
        "status": "PASS" if not errors else "STOP",
        "allocation_id": allocation,
        "candidate_allocation_ids": ids,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", required=True, type=Path)
    parser.add_argument("--harness", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--runner", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = validate(args.freeze, args.harness, args.candidate, args.runner)
    except (OSError, json.JSONDecodeError) as exc:
        result = {"schema": "frozen-candidate-gate-v1", "status": "STOP",
                  "errors": [f"manifest read failed: {type(exc).__name__}: {exc}"]}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
