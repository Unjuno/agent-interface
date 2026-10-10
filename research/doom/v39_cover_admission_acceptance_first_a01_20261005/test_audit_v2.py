"""Corruption controls for the independent A01 raw/source auditor."""
import copy
import json
from pathlib import Path
import unittest

from audit_v2 import audit

ROOT = Path(__file__).parent


class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
        cls.raw = json.loads((ROOT / "raw_v2.json").read_text(encoding="utf-8"))

    def test_frozen_raw_passes(self):
        self.assertEqual(audit(copy.deepcopy(self.raw), self.freeze), [])

    def test_rejects_late_latest_snapshot(self):
        bad = copy.deepcopy(self.raw)
        bad["latest_observation_at_accept_return"] = bad["events"][-1]
        self.assertTrue(any("incorrectly claims" in e for e in audit(bad, self.freeze)))

    def test_rejects_monitor_seen_before_accept(self):
        bad = copy.deepcopy(self.raw)
        bad["monitor_sequences_at_accept_return"] = [9]
        self.assertTrue(any("unexpectedly consumed" in e for e in audit(bad, self.freeze)))

    def test_rejects_missing_planner_before_invalidation(self):
        bad = copy.deepcopy(self.raw)
        bad["planner_started_before_hard_invalidation_observed"] = False
        self.assertTrue(any("planner-start ordering" in e for e in audit(bad, self.freeze)))

    def test_rejects_fifo_reordering(self):
        bad = copy.deepcopy(self.raw)
        bad["events"].reverse()
        self.assertTrue(any("accept-then-observation FIFO" in e for e in audit(bad, self.freeze)))


if __name__ == "__main__":
    unittest.main()
