import copy
import json
import unittest
from pathlib import Path

import candidate

FIXTURE = json.loads((Path(__file__).parent / "fixture.json").read_text(encoding="utf-8"))


class ConstructionTests(unittest.TestCase):
    def test_d_baseline_blocks_new_intent_across_handoff(self):
        result = candidate.run(FIXTURE["cases"][0])
        self.assertEqual(result["retry_plus_obligation_ledger"]["admitted"], ["op-A"])
        self.assertEqual(result["visible_state_only"]["admitted"], ["op-A", "op-B"])

    def test_partial_effect_preserves_pending_obligation(self):
        result = candidate.run(FIXTURE["cases"][1])
        self.assertEqual(result["retry_plus_obligation_ledger"]["admitted"], ["op-A"])
        self.assertEqual(result["retry_plus_obligation_ledger"]["unresolved_at_end"], ["op-A"])

    def test_unknown_footprint_yields_hold(self):
        result = candidate.run(FIXTURE["cases"][3])
        self.assertEqual(result["retry_plus_obligation_ledger"]["admitted"], ["op-A"])
        self.assertIn("HOLD_UNKNOWN_FOOTPRINT", [x["status"] for x in result["retry_plus_obligation_ledger"]["decisions"]])

    def test_goal_change_and_safety_release_bypass(self):
        result = candidate.run(FIXTURE["cases"][4])
        self.assertIn("SAFETY_RELEASE_BYPASS", [x["status"] for x in result["retry_plus_obligation_ledger"]["decisions"]])

    def test_alias_is_canonicalized_before_admission(self):
        result = candidate.run(FIXTURE["cases"][5])
        self.assertEqual(result["retry_plus_obligation_ledger"]["admitted"], ["op-A"])

    def test_mutated_d_output_is_rejected(self):
        result = candidate.run(FIXTURE["cases"][0])
        corrupted = copy.deepcopy(result)
        corrupted["retry_plus_obligation_ledger"]["admitted"].append("op-B")
        self.assertNotEqual(corrupted, result)


if __name__ == "__main__":
    unittest.main()
