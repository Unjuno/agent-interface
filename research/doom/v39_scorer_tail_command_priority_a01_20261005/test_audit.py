#!/usr/bin/env python3
"""Positive and corruption controls for the independent result audit."""
import copy
import json
import unittest

import audit


class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads((audit.ROOT / "RESULT.json").read_text(encoding="utf-8"))

    def test_unmodified_result_passes_audit(self):
        self.assertEqual(audit.audit(self.result)["disposition"], "PASS_AUDIT_FAIL_REPRODUCED")

    def test_mutated_tail_sample_count_is_rejected(self):
        result = copy.deepcopy(self.result)
        result["scenarios"][1]["scorer_rows"] = 1
        self.assertFalse(audit.audit(result)["checks"]["exact_result_reconstruction"])

    def test_mutated_readiness_poll_count_is_rejected(self):
        result = copy.deepcopy(self.result)
        result["scenarios"][2]["readiness_checks"] = 1
        self.assertFalse(audit.audit(result)["checks"]["exact_result_reconstruction"])

    def test_mutated_disposition_is_rejected(self):
        result = copy.deepcopy(self.result)
        result["disposition"] = "PASS_COMMAND_PRIORITY"
        self.assertFalse(audit.audit(result)["checks"]["exact_result_reconstruction"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
