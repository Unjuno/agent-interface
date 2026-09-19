"""One finite launcher-contract comparison, retaining baseline failure and repair."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import platform
from pathlib import Path
import re
import subprocess
import sys
import unittest

from preflight import FILES, SCRIPTS, git_blob
from test_launchers import Fixture, LauncherTests, ROOT

BASE = "ff2bbb5e200e2bf8ee2295ad97ca9dd0f158a371"
EXPECTED = dict(zip(FILES, (
    "58f336f7010652503dad098c533dd42a80044d36",
    "ef489bbd68e3f80fac060b179fe90da2cce8d209",
    "26db03b8400b03fbe5272bd4ae5ad9c3a82d31a2",
    "4e46e2677aada41b5bf7433db18e1059592997f7",
)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="New result directory only.")
    parser.add_argument("--source-commit", required=True, help="Declared frozen source commit; source hashes are retained independently.")
    args = parser.parse_args()
    if not re.fullmatch("[0-9a-f]{40}", args.source_commit):
        parser.error("--source-commit requires a full immutable Git SHA")
    try:
        args.out.mkdir(parents=True, exist_ok=False)
    except OSError as error:
        parser.exit(2, f"Cannot create new result directory: {error}\n")
    report = {
        "schema": "agent_interface_first_run_experiment_v1",
        "base_commit": BASE,
        "declared_source_commit": args.source_commit,
        "source_materialization": "Exact MCP-fetched file bytes and Git modes, not a full repository clone.",
        "status": "STARTED",
        "environment": {"platform": platform.platform(), "machine": platform.machine(), "python": sys.version, "logical_cpu_count": os.cpu_count(), "clock_policy": "Uncontrolled; no timing or throughput claim.", "batch": "One serial finite matrix; no model batches."},
        "scope": "Real POSIX exec/bash; Python, venv, pip and runtime dispatch use a fail-closed test double. No installs, GUI, model, network or performance benchmark.",
        "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.iterdir() if p.name in ("preflight.py", "test_launchers.py", "experiment.py", "PLAN.md")},
        "inputs": [], "cases": [],
    }
    (args.out / "started.json").write_text(json.dumps(report, indent=2) + "\n")
    try:
        for name, expected in EXPECTED.items():
            actual = git_blob((ROOT / name).read_bytes())
            report["inputs"].append({"path": name, "expected_blob": expected, "actual_blob": actual, "matched": actual == expected})
        if not all(item["matched"] for item in report["inputs"]):
            raise ValueError("Pinned input changed: do not reuse this experiment plan.")
        for arm, mode in (("retained_baseline", 0o644), ("metadata_repair", 0o755)):
            for script in SCRIPTS:
                fixture = Fixture(mode)
                try:
                    tail = () if script == SCRIPTS[0] else ("doctor",)
                    direct = fixture.call(script, *tail)
                    shell_status = None
                    if arm == "retained_baseline":
                        shell = subprocess.run(["bash", "-c", 'exec "$@"', "smoke", str(fixture.root / script), *tail], env=fixture.env, cwd=fixture.temp.name, capture_output=True, text=True, timeout=5)
                        shell_status = shell.returncode
                        expected = direct.get("errno") == 13 and shell_status == 126 and not fixture.calls()
                    else:
                        expected = direct["returncode"] == 0 and fixture.calls()[-1]["argv"][-1] == "doctor"
                    report["cases"].append({"arm": arm, "path": script, "mode": oct(mode), "direct_exec": direct, "bash_exit_code": shell_status, "dispatch": fixture.calls(), "expectation_met": expected})
                finally:
                    fixture.close()
        log = io.StringIO()
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(LauncherTests)
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
        (args.out / "unittest.txt").write_text(log.getvalue(), encoding="utf-8")
        report["tests"] = {"run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped)}
        passed = all(case["expectation_met"] for case in report["cases"]) and result.wasSuccessful() and result.testsRun == 21 and not result.skipped
        report["status"] = "PASS_SCOPED_LAUNCHER_REPAIR" if passed else "FAIL_RETAIN_FIRST_OUTCOME"
    except Exception as error:
        report["status"] = "FAIL_RETAIN_FIRST_OUTCOME"
        report["error"] = f"{type(error).__name__}: {error}"
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(args.out / "report.json")}, indent=2))
    return 0 if report["status"] == "PASS_SCOPED_LAUNCHER_REPAIR" else 1


if __name__ == "__main__":
    sys.exit(main())
