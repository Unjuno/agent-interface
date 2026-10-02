import json
import unittest
from pathlib import Path

import auditor
import candidate


ROOT = Path(__file__).parent


class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
        cls.rows = candidate.run(cls.fixture)

    def test_all_declared_opportunities_remain_in_denominator(self):
        self.assertEqual(9, len(self.rows))
        self.assertEqual(9, len({(r["case_id"], r["opportunity_id"]) for r in self.rows}))

    def test_phase_control_localizes_capture_boundary(self):
        by_case = {r["case_id"]: r for r in self.rows}
        self.assertEqual("eligible_effect", by_case["phase_hit"]["boundary"])
        self.assertEqual("not_acquired", by_case["phase_miss"]["boundary"])

    def test_planner_stall_is_after_delivery(self):
        by_case = {r["case_id"]: r for r in self.rows}
        self.assertEqual("eligible_effect", by_case["phase_hit"]["boundary"])
        self.assertEqual("delivered_no_decision", by_case["planner_stall"]["boundary"])

    def test_earlier_failed_boundaries_are_distinct(self):
        by_case = {r["case_id"]: r for r in self.rows}
        self.assertEqual("acquired_not_delivered", by_case["delivery_after_expiry"]["boundary"])
        self.assertEqual("decision_no_eligible_effect", by_case["decision_no_effect"]["boundary"])

    def test_safe_stop_clock_unknown_and_censoring_are_not_misses(self):
        by_case = {r["case_id"]: r for r in self.rows}
        self.assertEqual(("decision_no_eligible_effect", "safe_stop"), (by_case["safe_stop"]["boundary"], by_case["safe_stop"]["detail"]))
        self.assertEqual(("UNKNOWN", "clock_unsynced"), (by_case["clock_unknown"]["boundary"], by_case["clock_unknown"]["detail"]))
        self.assertEqual(("UNKNOWN", "right_censored"), (by_case["right_censored"]["boundary"], by_case["right_censored"]["detail"]))
        self.assertIsNone(by_case["right_censored"]["event_id"])

    def test_absent_exogenous_clock_is_not_applicable(self):
        by_case = {r["case_id"]: r for r in self.rows}
        self.assertEqual("NOT_APPLICABLE", by_case["no_exogenous_opportunity"]["boundary"])

    def test_independent_replay_uses_scorer_oracle_for_effect(self):
        expected = auditor.replay(self.fixture)
        self.assertEqual("eligible_effect", expected[0]["boundary"])
        self.assertEqual("effect_receipt_observed", expected[0]["detail"])

    def test_candidate_and_independent_replay_match_on_frozen_rows(self):
        self.assertEqual(self.rows, auditor.replay(self.fixture))


if __name__ == "__main__":
    unittest.main()
