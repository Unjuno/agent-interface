"""Corruption controls for the current-main / PR comparative auditor."""
import copy
import json
from pathlib import Path
import unittest

from audit_v3 import audit

ROOT = Path(__file__).parent


class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
        cls.raw = json.loads((ROOT / "raw_v3.json").read_text(encoding="utf-8"))

    def test_frozen_raw_passes(self):
        self.assertEqual(audit(copy.deepcopy(self.raw), self.freeze)[0], [])

    def test_rejects_false_boundary_latest(self):
        bad = copy.deepcopy(self.raw)
        bad["cases"]["current_main"]["latest_at_accept_return"] = bad["events"][-1]
        self.assertTrue(audit(bad, self.freeze)[0])

    def test_rejects_event_seen_before_accept(self):
        bad = copy.deepcopy(self.raw)
        bad["cases"]["pr_7589"]["monitor_sequences_at_accept_return"] = [9]
        self.assertTrue(audit(bad, self.freeze)[0])

    def test_rejects_missing_planner_order(self):
        bad = copy.deepcopy(self.raw)
        bad["cases"]["pr_7589"]["planner_started_before_invalidation_observed"] = False
        self.assertTrue(audit(bad, self.freeze)[0])

    def test_rejects_reversed_fifo(self):
        bad = copy.deepcopy(self.raw)
        bad["events"].reverse()
        self.assertTrue(audit(bad, self.freeze)[0])


if __name__ == "__main__":
    unittest.main()
