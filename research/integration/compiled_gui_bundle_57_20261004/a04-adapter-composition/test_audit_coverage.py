"""Ensure the independent A04 auditor rejects warm-path attempt corruption."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
AUDIT_PATH = ROOT / "audit.py"
RUN_PATH = ROOT / "RUN.json"


def load_audit():
    if not AUDIT_PATH.is_file():
        raise AssertionError("candidate independent auditor must exist")
    spec = importlib.util.spec_from_file_location("a04_audit_under_test", AUDIT_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("candidate auditor must be importable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AuditCoverageTests(unittest.TestCase):
    def test_auditor_accepts_raw_and_rejects_attempts_in_every_warm_route(self):
        audit = load_audit()
        raw = json.loads(RUN_PATH.read_text())
        self.assertEqual(audit.validate_data(raw)["status"],
                         "PASS_SCOPED_TEST_DOUBLE_ADAPTER_COMPOSITION")
        for case_name in ("positive", "changed", "outer_effect_unavailable"):
            mutated = copy.deepcopy(raw)
            result = mutated["cases"][case_name]["result"]
            result["accounting"]["attempted_calls"] = 1
            result["attempt_ledger"] = [{"mutation": "attempted"}]
            with self.subTest(case=case_name):
                with self.assertRaises(AssertionError):
                    audit.validate_data(mutated)


if __name__ == "__main__":
    unittest.main()
