#!/usr/bin/env python3
"""Mutation controls for the independently implemented raw-only auditor."""
import copy
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import audit
import runner


class AuditMutationTests(unittest.TestCase):
    def setUp(self):
        self.rows = [runner.row(name) for name in runner.CASES]

    def test_frozen_baseline_passes(self):
        self.assertEqual(audit.audit(self.rows), [])

    def test_missing_timestamp_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[4]["policy_a"]["margins_ms"][1] = 17
        self.assertIn("missing_time_not_unknown", audit.audit(rows))

    def test_opportunity_identity_corruption_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["opportunity_ids"][0] = "foreign"
        self.assertIn("comfortable:opportunities", audit.audit(rows))

    def test_crossing_sign_corruption_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[2]["policy_a"]["margins_ms"][2] = 3
        self.assertIn("crossing_not_reconstructed", audit.audit(rows))


if __name__ == "__main__":
    unittest.main(verbosity=2)
