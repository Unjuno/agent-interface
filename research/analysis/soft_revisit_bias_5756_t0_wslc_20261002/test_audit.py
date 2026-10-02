import copy
import json
import unittest

from audit import audit_rows
from candidate import run
from fixtures import build_fixtures


class AuditContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = build_fixtures()
        cls.rows = run(cls.fixtures)

    def test_candidate_rows_reconcile_against_independent_oracle(self):
        report = audit_rows(self.fixtures, self.rows)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["rows"], 128)

    def test_comparison_reports_soft_tie_with_stateless_baseline(self):
        report = audit_rows(self.fixtures, self.rows)
        self.assertEqual(report["partial_revision_contrast"]["soft_minus_hard"], 16)
        self.assertEqual(report["partial_revision_contrast"]["soft_minus_stateless"], 0)
        self.assertEqual(report["partial_revision_contrast"]["soft_minus_exhaustive"], 16)
        self.assertIn("does not establish a soft-specific advantage", report["interpretation"])

    def test_auditor_rejects_missing_policy_fixture_pair(self):
        report = audit_rows(self.fixtures, self.rows[:-1])
        self.assertTrue(any("row count" in error for error in report["errors"]))

    def test_auditor_rejects_duplicate_policy_fixture_pair(self):
        mutated = copy.deepcopy(self.rows)
        mutated[-1] = copy.deepcopy(mutated[0])
        report = audit_rows(self.fixtures, mutated)
        self.assertTrue(any("duplicate" in error for error in report["errors"]))

    def test_auditor_rejects_false_target_claim(self):
        mutated = copy.deepcopy(self.rows)
        mutated[0]["claimed_target"] = "hidden-target"
        report = audit_rows(self.fixtures, mutated)
        self.assertTrue(any("claim" in error for error in report["errors"]))

    def test_auditor_rejects_forbidden_edge_traversal(self):
        mutated = copy.deepcopy(self.rows)
        row = next(r for r in mutated if r["fixture_id"] == "unsafe-00")
        row["events"].append({"type": "navigate", "edge_id": "alpha"})
        report = audit_rows(self.fixtures, mutated)
        self.assertTrue(any("forbidden" in error for error in report["errors"]))

    def test_auditor_rejects_epoch_memory_carryover(self):
        mutated = copy.deepcopy(self.rows)
        row = next(r for r in mutated if r["fixture_id"] == "partial-00")
        row["events"].append({"type": "epoch_change", "from": 1, "to": 2})
        row["events"].append({"type": "memory_reused", "source_epoch": 1})
        report = audit_rows(self.fixtures, mutated)
        self.assertTrue(any("epoch" in error for error in report["errors"]))

    def test_auditor_rejects_unrecognized_output_fields(self):
        mutated = copy.deepcopy(self.rows)
        mutated[0]["unregistered_metadata"] = "must not be silently accepted"
        report = audit_rows(self.fixtures, mutated)
        self.assertTrue(any("schema" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
