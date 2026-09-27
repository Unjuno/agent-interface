"""Construction-only controls for the independent #4649 ledger auditor."""

import copy
import unittest
from pathlib import Path

from audit_ledger import INPUTS, audit, derive_input_ledger


INPUT_DIR = Path(__file__).resolve().parent / "inputs"


class ResultLedgerAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger, cls.input_errors = derive_input_ledger(INPUT_DIR)
        cls.valid = {"input_sha256": copy.deepcopy(cls.ledger)}

    def test_frozen_inputs_reconcile_and_valid_report_passes(self):
        self.assertEqual(len(INPUTS), 10)
        self.assertEqual(self.input_errors, [])
        self.assertEqual(audit(INPUT_DIR, self.valid)["decision"], "PASS_RESULT_LEDGER_BINDING_SCOPED")

    def test_dropped_role_is_rejected(self):
        altered = copy.deepcopy(self.valid)
        altered["input_sha256"].pop("accepted")
        result = audit(INPUT_DIR, altered)
        self.assertEqual(result["decision"], "FAIL_RESULT_LEDGER_BINDING")
        self.assertIn("RESULT_INPUT_LEDGER_ROLE_SET_MISMATCH", result["errors"])

    def test_changed_digest_is_rejected(self):
        altered = copy.deepcopy(self.valid)
        altered["input_sha256"]["accepted"]["sha256"] = "0" * 64
        result = audit(INPUT_DIR, altered)
        self.assertEqual(result["decision"], "FAIL_RESULT_LEDGER_BINDING")
        self.assertIn("RESULT_INPUT_LEDGER_SHA256_MISMATCH:accepted", result["errors"])

    def test_wrong_path_and_malformed_ledger_are_rejected(self):
        wrong_path = copy.deepcopy(self.valid)
        wrong_path["input_sha256"]["audit_plan"]["path"] = "PLAN.md"
        self.assertIn("RESULT_INPUT_LEDGER_PATH_MISMATCH:audit_plan", audit(INPUT_DIR, wrong_path)["errors"])
        self.assertIn("RESULT_INPUT_LEDGER_NOT_OBJECT", audit(INPUT_DIR, {"input_sha256": []})["errors"])


if __name__ == "__main__":
    unittest.main()
