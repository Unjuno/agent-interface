"""Run construction/parity unit tests and retain a machine-readable receipt."""

from __future__ import annotations

import contextlib
import io
import json
import os
import platform
import sys
import time
import unittest
from pathlib import Path


def main() -> int:
    out = Path(os.environ["OUT_DIR"])
    out.mkdir(parents=True, exist_ok=True)
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(Path(__file__).parent), pattern="test_lifecycle.py")
    started = time.perf_counter_ns()
    with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    receipt = {
        "status": "CONSTRUCTION_PASS" if result.wasSuccessful() else "STOP_CONSTRUCTION_PARITY_OR_TEST",
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "details": stream.getvalue(),
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "elapsed_ns": time.perf_counter_ns() - started,
    }
    (out / "construction.json").write_text(json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{receipt['status']} tests={receipt['tests_run']} failures={receipt['failures']} errors={receipt['errors']}")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
