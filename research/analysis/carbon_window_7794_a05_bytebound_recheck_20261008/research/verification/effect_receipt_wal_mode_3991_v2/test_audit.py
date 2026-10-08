from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from audit import audit_result


class AuditControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads(Path("RESULT.json").read_text())

    def test_raw_result_passes(self):
        out = audit_result(self.result, Path("raw"))
        self.assertIn(out["decision"], ("PASS_CONSTRUCTION_AUDIT", "PASS_JOURNAL_MODE_TRANSACTION_SCOPE_SCOPED"))
        self.assertEqual(out["errors"], [])

    def _corrupt(self, mutate):
        result = copy.deepcopy(self.result)
        mutate(result)
        return audit_result(result, Path("raw"))

    def test_missing_row_rejected(self):
        out = self._corrupt(lambda r: r["formal_rows"].pop())
        self.assertIn("formal_matrix_incomplete_or_duplicate", out["errors"])

    def test_duplicate_row_rejected(self):
        out = self._corrupt(lambda r: r["formal_rows"].__setitem__(1, copy.deepcopy(r["formal_rows"][0])))
        self.assertIn("formal_matrix_incomplete_or_duplicate", out["errors"])

    def test_child_exit_mutation_rejected(self):
        out = self._corrupt(lambda r: r["formal_rows"][0].__setitem__("child_returncode", 0))
        self.assertTrue(any(e.startswith("child_returncode:") for e in out["errors"]))

    def test_query_authority_mutation_rejected(self):
        def mutate(r):
            raw = json.loads(r["formal_rows"][0]["status_stdout"])
            raw["effect_access"] = True
            r["formal_rows"][0]["status_stdout"] = json.dumps(raw)
        out = self._corrupt(mutate)
        self.assertTrue(any(e.startswith("receipt_only_status:") for e in out["errors"]))

    def test_retry_authority_mutation_rejected(self):
        out = self._corrupt(lambda r: r["formal_rows"][0].__setitem__("retry_count", 2))
        self.assertTrue(any(e.startswith("retry_policy:") for e in out["errors"]))

    def test_raw_count_mutation_rejected(self):
        out = self._corrupt(lambda r: r["formal_rows"][0].__setitem__("effect_count_after_retry", 99))
        self.assertTrue(any(e.startswith("recorded_counts:") for e in out["errors"]))

    def test_invalid_control_acceptance_rejected(self):
        out = self._corrupt(lambda r: r["control_rows"][0].__setitem__("accepted", True))
        self.assertTrue(any(e.startswith("identity_control_effect:") for e in out["errors"]))


if __name__ == "__main__":
    unittest.main()
