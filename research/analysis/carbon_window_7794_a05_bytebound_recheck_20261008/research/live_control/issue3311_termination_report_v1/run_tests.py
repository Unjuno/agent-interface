"""Verify frozen sources, run the one-shot local suite, and retain raw outputs."""

from __future__ import annotations

import hashlib
import io
import json
import os
import platform
import subprocess
import sys
import time
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
FREEZE_PATH = HERE / "FREEZE.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_freeze(freeze: dict) -> None:
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                          capture_output=True, text=True, check=True).stdout.strip()
    ancestry = subprocess.run(["git", "merge-base", "--is-ancestor",
                               freeze["base_main"], "HEAD"], cwd=REPO,
                              check=False)
    if ancestry.returncode != 0:
        raise RuntimeError("checkout does not descend from frozen main")
    for name, row in freeze["sources"].items():
        path = REPO / row["path"]
        if sha256(path) != row["sha256"]:
            raise RuntimeError("frozen source SHA-256 mismatch: " + name)
        if row.get("git_blob"):
            blob = subprocess.run(["git", "hash-object", str(path)], cwd=REPO,
                                  capture_output=True, text=True, check=True).stdout.strip()
            if blob != row["git_blob"]:
                raise RuntimeError("frozen Git blob mismatch: " + name)


def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def main() -> int:
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    verify_freeze(freeze)
    output = HERE / "results" / "local-01"
    output.mkdir(parents=True, exist_ok=False)
    os.environ["ISSUE3311_TERMINATION_ARTIFACT_DIR"] = str(output)

    suite = unittest.defaultTestLoader.discover(str(HERE), pattern="test_*.py")
    test_names = [test.id() for test in flatten(suite)]
    stream = io.StringIO()
    started = time.monotonic_ns()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    elapsed = time.monotonic_ns() - started
    stdout = stream.getvalue()
    (output / "test.stdout.txt").write_text(stdout, encoding="utf-8", newline="\n")
    (output / "test.stderr.txt").write_text("", encoding="utf-8", newline="\n")
    summary = {
        "schema": "issue3311_termination_contract_test_result_v1",
        "allocation_id": freeze["allocation_id"],
        "disposition": "PASS_TERMINATION_HOLD_CONTRACT_SCOPED" if result.wasSuccessful()
                       else "FAIL_TERMINATION_CONTRACT",
        "base_main": freeze["base_main"],
        "source_sha256": {name: row["sha256"]
                          for name, row in freeze["sources"].items()},
        "runtime": {"python": sys.version, "platform": platform.platform(),
                    "container": "not_used_shared_slot_not_assigned"},
        "test_count": result.testsRun,
        "test_names": test_names,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "elapsed_monotonic_ns": elapsed,
        "stdout_sha256": hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
        "stdout_path": "test.stdout.txt",
        "stderr_path": "test.stderr.txt",
    }
    (output / "RESULT.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n",
                                        encoding="utf-8", newline="\n")
    print(stdout, end="")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
