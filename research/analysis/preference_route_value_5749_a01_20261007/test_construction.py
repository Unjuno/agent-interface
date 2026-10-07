import json
import unittest
from pathlib import Path

import auditor
import candidate


ROOT = Path(__file__).parent


class RouteRegretConstruction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "fixture.json").read_text())
        cls.raw = candidate.run(cls.fixture)

    def rows(self):
        return {(r["case_id"], r["policy"]): r for r in self.raw["rows"]}

    def test_complete_independently_audited_matrix(self):
        result = auditor.audit(self.raw, self.fixture)
        self.assertEqual(result["rows"], 18)
        self.assertEqual(result["errors"], [])

    def test_same_uncertainty_signal_routes_differ_by_regret(self):
        rows = self.rows()
        self.assertEqual(rows[("low_regret_authorized_default", "source_router")]["route"], "CLARIFY")
        self.assertEqual(rows[("high_regret_authorized_default", "source_router")]["route"], "CLARIFY")
        self.assertEqual(rows[("low_regret_authorized_default", "regret_cost")]["route"], "ACT_PROPOSAL")
        self.assertEqual(rows[("high_regret_authorized_default", "regret_cost")]["route"], "CLARIFY")

    def test_equal_cost_uses_frozen_no_query_tie_rule(self):
        row = self.rows()[("regret_equals_query_cost", "regret_cost")]
        self.assertEqual(row["worst_case_regret"], 2)
        self.assertEqual(row["route"], "ACT_PROPOSAL")

    def test_authority_and_unknown_preferences_fail_closed(self):
        rows = self.rows()
        self.assertEqual(rows[("high_regret_no_authorized_default", "regret_cost")]["route"], "CLARIFY")
        self.assertEqual(rows[("low_regret_no_authorized_default", "regret_cost")]["route"], "YIELD_NO_AUTHORIZED_ACTION")
        self.assertEqual(rows[("unknown_preference_model", "regret_cost")]["route"], "YIELD_UNKNOWN_PREFERENCE_MODEL")
        self.assertTrue(all(not row["authority_granted"] for row in self.raw["rows"]))

    def test_world_uncertainty_is_verified_before_regret_scoring(self):
        rows = self.rows()
        for case_id in ("world_only_uncertainty", "mixed_world_and_preference_uncertainty"):
            self.assertEqual(rows[(case_id, "regret_cost")]["route"], "VERIFY")
            self.assertIsNone(rows[(case_id, "regret_cost")]["worst_case_regret"])

    def test_all_corruption_controls_rejected(self):
        results = auditor.mutations(self.raw, self.fixture)
        self.assertEqual(len(results), 6)
        self.assertTrue(all(x["rejected"] for x in results), results)


if __name__ == "__main__":
    unittest.main()
