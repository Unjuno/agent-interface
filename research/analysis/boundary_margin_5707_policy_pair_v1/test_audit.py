#!/usr/bin/env python3
"""Preflight controls for the independent Issue #5715 raw-only auditor."""
import copy
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import audit
import runner


class PairedPolicyAuditTests(unittest.TestCase):
    def setUp(self):
        self.rows = list(runner.rows())

    def test_frozen_pair_and_controls_pass(self):
        self.assertEqual(audit.audit(self.rows), [])

    def test_policy_timestamp_mutation_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["arms"][1]["opportunities"][0]["admission_ms"] = 89
        self.assertIn("late:policy_margin_or_external_event:opp-01", audit.audit(rows))

    def test_opportunity_identity_mutation_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["arms"][0]["opportunities"][0]["id"] = "foreign"
        self.assertIn("early:opportunity_identity", audit.audit(rows))

    def test_external_event_mutation_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["arms"][0]["opportunities"][0]["event_id"] = "other-event"
        self.assertIn("early:policy_margin_or_external_event:opp-01", audit.audit(rows))

    def test_crossing_sign_mutation_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[1]["margin_ms"] = 3
        self.assertIn("crossing_control", audit.audit(rows))

    def test_missing_timestamp_mutation_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["arms"][0]["opportunities"][1]["admission_ms"] = None
        self.assertIn("early:policy_margin_or_external_event:opp-02", audit.audit(rows))


if __name__ == "__main__":
    unittest.main(verbosity=2)
