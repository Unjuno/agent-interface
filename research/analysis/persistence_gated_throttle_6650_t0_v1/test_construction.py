from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from research.analysis.persistence_gated_throttle_6650_t0_v1.auditor import audit
from research.analysis.persistence_gated_throttle_6650_t0_v1.candidate import run


ROOT = Path(__file__).parent


class ConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "fixture.json").read_text())
        cls.raw = run(cls.fixture)

    def test_raw_accounting_audits_clean(self):
        self.assertEqual([], audit(self.fixture, self.raw))

    def test_burst_does_not_trigger_age_policy(self):
        row = self.raw["traces"]["transient_burst"]["persistence"]
        self.assertEqual([], row["transitions"])
        self.assertEqual(0, row["summary"]["suppressed_optional"])

    def test_blackout_triggers_without_completed_sojourn_sample(self):
        row = self.raw["traces"]["zero_dequeue_blackout"]["persistence"]
        at_trigger = next(t["at"] for t in row["transitions"] if t["to"] > t["from"])
        state = next(s for s in row["states"] if s["at"] == at_trigger and s["session"] == "S")
        self.assertEqual(0, state["completed_sojourn_samples"])
        self.assertGreaterEqual(state["oldest_pending_age"], self.fixture["parameters"]["age_target"])

    def test_all_mandatory_terminals_equal_baseline(self):
        for trace_id, policies in self.raw["traces"].items():
            fixed = {x["id"]: x["outcome"] for x in policies["fixed"]["services"]
                     if x["kind"] == "mandatory"}
            for policy in ("queue_length", "persistence", "oracle"):
                observed = {x["id"]: x["outcome"] for x in policies[policy]["services"]
                            if x["kind"] == "mandatory"}
                self.assertEqual(fixed, observed, f"{trace_id}/{policy}")

    def test_malformed_freshness_label_rejected(self):
        corrupt = copy.deepcopy(self.raw)
        row = corrupt["traces"]["sustained_overload"]["fixed"]["services"][0]
        row["outcome"] = "SERVICED_WITHIN_FRESHNESS" if row["outcome"] != "SERVICED_WITHIN_FRESHNESS" else "STALE_AT_SERVICE_START"
        self.assertTrue(audit(self.fixture, corrupt))

    def test_missing_offered_id_rejected(self):
        corrupt = copy.deepcopy(self.raw)
        corrupt["traces"]["transient_burst"]["persistence"]["requests"].pop()
        self.assertTrue(audit(self.fixture, corrupt))

    def test_mandatory_suppression_rejected(self):
        corrupt = copy.deepcopy(self.raw)
        row = next(r for r in corrupt["traces"]["mandatory_flood"]["persistence"]["requests"]
                   if r["kind"] == "mandatory")
        row["status"] = "SUPPRESSED"
        row["suppression_receipt"] = "OPTIONAL_PRODUCER_THROTTLE"
        self.assertTrue(audit(self.fixture, corrupt))

    def test_cross_session_state_label_rejected(self):
        corrupt = copy.deepcopy(self.raw)
        row = corrupt["traces"]["session_isolation"]["persistence"]["states"][0]
        row["session"] = "NONEXISTENT"
        self.assertTrue(audit(self.fixture, corrupt))


if __name__ == "__main__":
    unittest.main()
