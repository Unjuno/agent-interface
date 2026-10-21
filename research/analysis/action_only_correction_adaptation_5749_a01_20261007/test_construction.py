import json
import unittest
from pathlib import Path

import auditor
import candidate


ROOT = Path(__file__).parent


class ActionOnlyConstruction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "fixture.json").read_text())
        cls.raw = candidate.run(cls.fixture)
        cls.rows = {(r["episode_id"], r["tick"], r["policy"]): r for r in cls.raw["rows"]}

    def test_independent_matrix_exact(self):
        result = auditor.audit(self.raw, self.fixture)
        self.assertEqual(result, {"disposition": "PASS_METHOD_SCOPED", "errors": [], "rows": 78, "expected_rows": 78})

    def test_stable_repeated_action_has_scoped_value(self):
        adaptive = [self.rows[("stable_B", i, "action_only_adaptive")] for i in range(6)]
        static = [self.rows[("stable_B", i, "static_default")] for i in range(6)]
        clarify = [self.rows[("stable_B", i, "clarify_each_turn")] for i in range(6)]
        self.assertEqual(adaptive[0]["learned_after"], None)
        self.assertEqual(adaptive[1]["learned_after"], "B")
        self.assertLess(sum(r["wrong_proposal"] for r in adaptive), sum(r["wrong_proposal"] for r in static))
        self.assertLess(sum(r["query_count"] for r in adaptive), sum(r["query_count"] for r in clarify))

    def test_one_off_and_missing_action_do_not_learn(self):
        for tick in range(4):
            self.assertIsNone(self.rows[("one_off_conflict", tick, "action_only_adaptive")]["learned_after"])

    def test_preference_change_suspends_old_choice_before_proposal(self):
        row = self.rows[("preference_change", 3, "action_only_adaptive")]
        self.assertEqual(row["proposal"], "A")
        next_row = self.rows[("preference_change", 4, "action_only_adaptive")]
        self.assertIsNone(next_row["proposal"])
        self.assertEqual(next_row["route"], "YIELD_PENDING_CONFIRMATION")
        self.assertEqual(self.rows[("preference_change", 5, "action_only_adaptive")]["proposal"], "B")

    def test_scope_and_consent_clear_adaptation(self):
        changed_scope = self.rows[("scope_change", 3, "action_only_adaptive")]
        revoked = self.rows[("consent_revoked", 3, "action_only_adaptive")]
        self.assertEqual(changed_scope["proposal"], "A")
        self.assertIsNone(changed_scope["learned_after"])
        self.assertEqual(revoked["route"], "DEFAULT_NO_ADAPT_CONSENT")
        self.assertIsNone(revoked["learned_after"])

    def test_clarification_is_turn_scoped_and_all_policies_non_authoritative(self):
        self.assertTrue(all(r["query_count"] == 1 and r["learned_after"] is None for r in self.raw["rows"] if r["policy"] == "clarify_each_turn"))
        self.assertTrue(all(r["authority_granted"] is False for r in self.raw["rows"]))

    def test_all_frozen_corruptions_rejected(self):
        controls = auditor.mutations(self.raw, self.fixture)
        self.assertEqual(len(controls), 7)
        self.assertTrue(all(x["rejected"] for x in controls), controls)


if __name__ == "__main__":
    unittest.main()
