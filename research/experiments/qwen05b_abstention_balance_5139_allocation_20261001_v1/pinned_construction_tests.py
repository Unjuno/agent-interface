"""Run allocation tests plus current-main protocol/sampler tests, excluding stale freeze tests."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ALLOCATION_DIR = Path(__file__).resolve().parent
EXPERIMENTS_DIR = ALLOCATION_DIR.parent
CURRENT_MAIN_DIR = EXPERIMENTS_DIR / "qwen05b_abstention_balance_5139_v1"
sys.path.insert(0, str(CURRENT_MAIN_DIR))


def main() -> int:
    loader = unittest.defaultTestLoader
    allocation_suite = loader.discover(str(ALLOCATION_DIR), pattern="test_*.py")
    current_suite = loader.loadTestsFromNames(["test_protocol", "test_sampler"])
    combined = unittest.TestSuite((allocation_suite, current_suite))
    result = unittest.TextTestRunner(verbosity=2).run(combined)
    report = {"schema": "qwen5139-pinned-cpu-construction-v1",
              "tests_run": result.testsRun, "failures": len(result.failures),
              "errors": len(result.errors), "passed": result.wasSuccessful()}
    print(json.dumps(report, sort_keys=True))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
