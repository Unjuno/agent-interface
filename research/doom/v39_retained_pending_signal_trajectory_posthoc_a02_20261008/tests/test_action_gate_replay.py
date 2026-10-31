import unittest
from action_gate_replay import compute


class RetainedActionGateReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=compute()
        cls.by_decision={d["decision"]:d for d in cls.result["decisions"]}

    def test_two_stale_answers_recompute_as_rejected(self):
        for number in (1,2):
            row=self.by_decision[number]
            self.assertTrue(row["reevaluation_matches_report"])
            self.assertEqual(row["admission"],"REJECTED_ACTION_NOT_CURRENT")
            self.assertIsNone(row["executor_admission"])
            self.assertEqual(row["effect_receipts"],0)
        first=self.by_decision[1]
        self.assertEqual((first["source_health"],first["current_health"],first["action_max_health_loss"]),(97,85,8))
        self.assertEqual(first["cover_hard_minimum"],85)
        self.assertEqual(first["action_minimum_health"],89)

    def test_soft_summary_reaches_following_turn_but_does_not_grant_effect(self):
        second=self.by_decision[2]
        self.assertEqual(second["prior_soft_event_summary"]["current_value"],85)
        self.assertEqual(second["prior_soft_event_summary"]["hard_minimum"],85)
        self.assertEqual((second["source_health"],second["current_health"],second["action_max_health_loss"]),(85,73,6))
        self.assertEqual(second["admission"],"REJECTED_ACTION_NOT_CURRENT")
        self.assertEqual(self.result["rejected_current_actions"],2)

    def test_admitted_replay_controls_match_report(self):
        for number in (0,3,4):
            row=self.by_decision[number]
            self.assertTrue(row["reevaluation_matches_report"])
            self.assertEqual(row["admission"],"INPUT_ADMITTED")
            self.assertIsNotNone(row["executor_admission"])


if __name__=="__main__":
    unittest.main()
