"""One-shot Docker entrypoint for the frozen Issue #3311 contract suite."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import unittest
from pathlib import Path


ROOT = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
LIVE = ROOT / "research" / "live_control"
PKG = LIVE / "issue3311_termination_report_v2"
SELF = LIVE / "issue3311_termination_report_docker_successor_v1"
FREEZE = json.loads((SELF / "FREEZE.json").read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if OUT.exists() and any(OUT.iterdir()):
        raise RuntimeError("output directory is not empty")
    OUT.mkdir(parents=True, exist_ok=True)
    for name, row in FREEZE["sources"].items():
        path = ROOT / row["path"]
        if sha(path) != row["sha256"]:
            raise RuntimeError(f"frozen source digest mismatch: {name}")

    os.environ["ISSUE3311_TERMINATION_ARTIFACT_DIR"] = str(OUT)
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.path.insert(0, str(PKG))
    sys.path.insert(0, str(LIVE))
    suite = unittest.defaultTestLoader.discover(
        str(PKG), pattern="test_supervisor.py", top_level_dir=str(LIVE))
    names = []

    def collect(current):
        for test in current:
            if isinstance(test, unittest.TestSuite):
                collect(test)
            else:
                names.append(test.id())

    collect(suite)
    if names != FREEZE["expected_tests"]:
        raise RuntimeError(f"test inventory differs from freeze: {names}")
    stream_path = OUT / "test.stdout.txt"
    started = time.monotonic_ns()
    with stream_path.open("w", encoding="utf-8", newline="\n") as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    elapsed = time.monotonic_ns() - started
    summary = {
        "schema": "issue3311-termination-docker-successor-result-v1",
        "allocation_id": FREEZE["allocation_id"],
        "status": "PASS_TERMINATION_HOLD_CONTRACT_DOCKER_SCOPED"
        if result.wasSuccessful() else "FAIL_TERMINATION_CONTRACT",
        "base_main": FREEZE["base_main"],
        "candidate_source_commit": FREEZE["candidate_source_commit"],
        "python": sys.version,
        "platform": platform.platform(),
        "test_count": result.testsRun,
        "test_names": names,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "elapsed_monotonic_ns": elapsed,
        "stdout_sha256": sha(stream_path),
        "case_directories": sorted(p.name for p in (OUT / "cases").iterdir())
        if (OUT / "cases").exists() else [],
    }
    result_path = OUT / "RESULT.json"
    result_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    audit = subprocess.run(
        [sys.executable, str(SELF / "audit_result.py"), str(ROOT), str(OUT)],
        capture_output=True, text=True, check=False)
    (OUT / "auditor.stdout.txt").write_text(audit.stdout, encoding="utf-8")
    (OUT / "auditor.stderr.txt").write_text(audit.stderr, encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(audit.stdout, end="")
    if audit.stderr:
        print(audit.stderr, file=sys.stderr, end="")
    return 0 if result.wasSuccessful() and audit.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
