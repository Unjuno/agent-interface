"""Run one frozen fake-X owner cleanup regression and retain its raw trace."""
import io
import json
import os
import sys
import types
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

SOURCE = Path(os.environ.get("AI_RESEARCH_SOURCE", "/src/source"))
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(SOURCE / "research" / "live_control"))

# The selected owner module imports only these exception types from executor_v3.
# A narrow stub avoids pulling GUI/runtime dependencies into this fake-X test.
executor = types.ModuleType("executor_v3")
executor.Cancelled = type("Cancelled", (Exception,), {})
executor.DecisionRequired = type("DecisionRequired", (Exception,), {})
sys.modules["executor_v3"] = executor

from test_input_owner_v12_explicit_up_cancel import ExplicitKeyUpCancellationTests

OUTPUT = Path(os.environ.get("AI_RESEARCH_OUT", "/out"))
OUTPUT.mkdir(parents=True, exist_ok=True)
suite = unittest.TestSuite([
    ExplicitKeyUpCancellationTests(
        "test_terminal_cleanup_sample_failure_retains_unverified_receipt_and_retries")
])
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
stdout = stream.getvalue()
(OUTPUT / "candidate.stdout").write_text(stdout, encoding="utf-8")
result_record = {
    "schema": "v39-terminal-release-sample-error-candidate-result-v1",
    "tests_run": result.testsRun,
    "failures": len(result.failures),
    "errors": len(result.errors),
    "successful": result.wasSuccessful(),
    "exit_code": 0 if result.wasSuccessful() else 1,
}
(OUTPUT / "candidate.result.json").write_text(
    json.dumps(result_record, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(stdout, end="")
sys.exit(result_record["exit_code"])
