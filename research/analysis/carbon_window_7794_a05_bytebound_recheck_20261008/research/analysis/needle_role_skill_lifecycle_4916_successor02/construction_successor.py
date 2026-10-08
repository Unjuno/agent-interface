"""Combine immutable v1 parity construction with successor path/source preflight."""

from __future__ import annotations

import contextlib
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

ROOT = Path(__file__).parent
V1 = ROOT.parent / "needle_role_skill_lifecycle_4916_v2"


def main() -> int:
    out = Path(os.environ["OUT_DIR"])
    out.mkdir(parents=True, exist_ok=True)
    repo = Path("/repo")
    v1_result = out / "predecessor-construction.json"
    env = dict(os.environ)
    env["OUT_DIR"] = str(out)
    env["ROLE_SKILL_DATA_DIR"] = str(repo / "research/needle_role_skill_reload_3780_v1/formal/seed-3788/builder")
    started = time.perf_counter_ns()
    process = subprocess.run(
        [sys.executable, "-B", str(repo / "research/analysis/needle_role_skill_lifecycle_4916_v2/construction_runner.py")],
        env=env, text=True, capture_output=True, check=False,
    )
    predecessor = json.loads((out / "construction.json").read_bytes()) if (out / "construction.json").is_file() else {}
    v1_result.write_text(json.dumps({"exit_code": process.returncode, "stdout": process.stdout, "stderr": process.stderr, "receipt": predecessor}, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")

    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(ROOT), pattern="test_successor.py")
    with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    source_hashes = {}
    freeze_path = ROOT / "FREEZE.json"
    freeze = json.loads(freeze_path.read_bytes())
    for name, expected in freeze["sources"].items():
        actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        source_hashes[name] = actual
        if actual != expected:
            result.errors.append((None, f"source hash mismatch: {name}"))
    status = "CONSTRUCTION_PASS" if process.returncode == 0 and predecessor.get("status") == "CONSTRUCTION_PASS" and result.wasSuccessful() else "STOP_CONSTRUCTION_PARITY_OR_SOURCE"
    receipt = {
        "allocation": "needle-role-skill-lifecycle-4916-v3-20260928-02",
        "status": status,
        "predecessor_construction_exit": process.returncode,
        "predecessor_status": predecessor.get("status"),
        "successor_tests_run": result.testsRun,
        "successor_test_failures": len(result.failures),
        "successor_test_errors": len(result.errors),
        "successor_test_output": stream.getvalue(),
        "source_hashes": source_hashes,
        "environment": {"python": sys.version, "platform": platform.platform(), "machine": platform.machine()},
        "elapsed_ns": time.perf_counter_ns() - started,
    }
    (out / "construction-successor.json").write_text(json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{status} predecessor={predecessor.get('status')} successor_tests={result.testsRun} errors={len(result.errors)}")
    return 0 if status == "CONSTRUCTION_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
