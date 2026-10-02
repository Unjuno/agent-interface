#!/usr/bin/env python3
"""Run the stdlib audit-contract suite and verify unprivileged output binding."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: construction_check.py /construction/write_probe.txt", file=sys.stderr)
        return 2
    source = Path(__file__).resolve().parent
    sys.path.insert(0, str(source))
    suite = unittest.defaultTestLoader.discover(str(source), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    Path(sys.argv[1]).write_text("WSLc unprivileged output bind writable\n", encoding="utf-8")
    print(f"construction_tests={result.testsRun} output_probe=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
