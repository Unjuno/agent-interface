"""Corruption controls for the seeded-context comparative auditor."""
import copy
import json
from pathlib import Path
import unittest

from audit_v4 import audit

ROOT = Path(__file__).parent


class AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
        cls.raw = json.loads((ROOT / "raw_v4.json").read_text(encoding="utf-8"))

    def test_frozen_raw_passes(self):
        self.assertEqual(audit(copy.deepcopy(self.raw), self.freeze)[0], [])

    def test_rejects_wrong_prior_observation(self):
        bad = copy.deepcopy(self.raw)
        bad["cases"]["current_main"]["latest_at_accept_return"] = None
        self.assertTrue(audit(bad, self.freeze)[0])

    def test_rejects_hard_event_seen_before_accept(self):
        bad = copy.deepcopy(self.raw)
        bad["cases"]["pr_7589"]["monitor_sequences_at_accept_return"] = [8, 9]
        self.assertTrue(audit(bad, self.freeze)[0])

    def test_rejects_missing_planner_start(self):
        bad = copy.deepcopy(self.raw)
        bad["cases"]["pr_7589"]["planner_started_before_invalidation_observed"] = False
        self.assertTrue(audit(bad, self.freeze)[0])

    def test_rejects_reordered_events(self):
        bad = copy.deepcopy(self.raw)
        bad["events"].reverse()
        self.assertTrue(audit(bad, self.freeze)[0])


if __name__ == "__main__":
    unittest.main()
