from __future__ import annotations

import io
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research/doom"))
import test_map01_feedback_release_contract_v1 as tests

stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
    unittest.defaultTestLoader.loadTestsFromModule(tests))
payload = {
    "schema": "map01-release-error-censor-oracle-test-result-v1",
    "status": "PASS" if result.wasSuccessful() else "FAIL",
    "tests": result.testsRun,
    "failures": len(result.failures),
    "errors": len(result.errors),
    "output": stream.getvalue(),
}
(HERE / "ORACLE_TEST.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: value for key, value in payload.items() if key != "output"}, indent=2))
if not result.wasSuccessful():
    raise SystemExit(1)
