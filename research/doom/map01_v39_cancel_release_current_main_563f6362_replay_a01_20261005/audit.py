#!/usr/bin/env python3
"""Independently check the retained replay outputs without executing tests."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
freeze = json.loads((HERE / "FREEZE.json").read_text())
run = json.loads((HERE / "RUN.json").read_text())
assert subprocess.check_output(["git", "rev-parse", freeze["integration_tree_commit"] + "^1"], cwd=ROOT, text=True).strip() == freeze["candidate_commit"]
assert subprocess.check_output(["git", "rev-parse", freeze["integration_tree_commit"] + "^2"], cwd=ROOT, text=True).strip() == freeze["base_main_commit"]
for path, blob in freeze["source_blobs"].items():
    assert subprocess.check_output(["git", "rev-parse", freeze["integration_tree_commit"] + ":" + path], cwd=ROOT, text=True).strip() == blob, path
for name, spec in freeze["suites"].items():
    log_path, exit_path = HERE / "raw" / f"{name}.log", HERE / "raw" / f"{name}.exit"
    assert log_path.is_file() and exit_path.is_file(), name
    assert exit_path.read_text().strip() == "0", name
    log = log_path.read_text()
    if name == "source_audit":
        assert "AUDIT_PASS_SOURCE_LOCK_AND_28_PRIMARY_TESTS_PLUS_13_OPTIMIZED_REPEAT_AND_91_PACKAGE_FILES" in log
        continue
    assert "OK" in log, name
    assert f"Ran {spec['count']} tests" in log, (name, log[-300:])
checksums = {}
for path in sorted(HERE.rglob("*")):
    if (path.is_file() and path.name not in {"SHA256SUMS.txt", "audit-success.log"}
            and "__pycache__" not in path.parts):
        checksums[path.relative_to(HERE).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
expected = {}
for line in (HERE / "SHA256SUMS.txt").read_text().splitlines():
    digest, rel = line.split("  ", 1)
    expected[rel] = digest
assert checksums == expected, {"actual": sorted(checksums), "expected": sorted(expected)}
print(json.dumps({"audit": "PASS_RAW_ONLY_CURRENT_MAIN_REPLAY", "main": freeze["base_main_commit"], "integration_tree": freeze["integration_tree_commit"], "suites": len(freeze["suites"]), "package_files": len(checksums)}, sort_keys=True))
