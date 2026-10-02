import json
import unittest
from pathlib import Path

import audit
import candidate

ROOT = Path(__file__).resolve().parent


class ContractTests(unittest.TestCase):
    def test_frozen_rows_and_candidate_decisions(self):
        fixture = json.loads((ROOT / "fixture.json").read_text())
        for event in fixture["events"]:
            self.assertEqual(candidate.decide(fixture["source_sequence"], fixture["source_health"], event), event["expected"])

    def test_clock_uncertainty_precedes_freshness(self):
        fixture = json.loads((ROOT / "fixture.json").read_text())
        event = next(x for x in fixture["events"] if x["id"] == "capture_straddles_decision")
        event["observation_sequence"] = 999
        self.assertEqual(candidate.decide(fixture["source_sequence"], fixture["source_health"], event), "YIELD_CAPTURE_ORDER_UNKNOWN")

    def test_health_loss_yields_and_never_grants_authority(self):
        fixture = json.loads((ROOT / "fixture.json").read_text())
        event = next(x for x in fixture["events"] if x["id"] == "fresh_health_loss")
        verdict = candidate.decide(fixture["source_sequence"], fixture["source_health"], event)
        self.assertEqual(verdict, "YIELD_HEALTH_LOSS")
        self.assertTrue(verdict.startswith("YIELD_"))

    def test_auditor_is_independent_module(self):
        self.assertNotIn("candidate", audit.__dict__)


if __name__ == "__main__":
    unittest.main()
