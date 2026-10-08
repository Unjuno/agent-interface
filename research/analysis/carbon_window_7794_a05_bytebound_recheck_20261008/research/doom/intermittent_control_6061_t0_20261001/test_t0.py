import unittest

from candidate import POLICIES, run_case
from make_fixture import build


class FixtureTests(unittest.TestCase):
    def test_nine_cases_and_hidden_truth_separation(self):
        visible, truth = build()
        self.assertEqual(len(visible["cases"]), 9)
        self.assertEqual(len(truth["cases"]), 9)
        self.assertEqual({c["case_id"] for c in visible["cases"]},
                         {c["case_id"] for c in truth["cases"]})
        self.assertNotIn("target_x", visible["cases"][0]["observations"][0])

    def test_every_policy_respects_the_common_occupancy_cap(self):
        visible, _ = build()
        for case in visible["cases"]:
            for policy in POLICIES:
                row = run_case(case, policy)
                self.assertLessEqual(row["occupancy_ticks"], 40)

    def test_all_policies_release_on_each_invalidity_boundary(self):
        visible, _ = build()
        for case in visible["cases"]:
            for policy in POLICIES:
                row = run_case(case, policy)
                for tick, obs in enumerate(case["observations"]):
                    invalid = (obs["identity"] != case["intended_identity"]
                               or not obs["focus_valid"] or not obs["lease_valid"]
                               or obs["capture_x"] is None)
                    if invalid:
                        self.assertEqual(row["trace"][tick]["command"], 0)

    def test_fixed_arm_samples_at_declared_period(self):
        visible, _ = build()
        case = next(c for c in visible["cases"] if c["case_id"] == "steady_drift")
        row = run_case(case, "fixed_period")
        self.assertEqual([x["tick"] for x in row["trace"] if x["capture"]], list(range(0, 40, 4)))

    def test_prediction_trigger_observes_tracker_error_but_not_truth(self):
        visible, _ = build()
        perfect = next(c for c in visible["cases"] if c["case_id"] == "perfect_tracker_positive")
        stale = next(c for c in visible["cases"] if c["case_id"] == "stale_tracker_negative")
        perfect_row = run_case(perfect, "prediction_triggered")
        stale_row = run_case(stale, "prediction_triggered")
        self.assertLess(perfect_row["capture_count"], 10)
        self.assertGreater(stale_row["capture_count"], perfect_row["capture_count"])


if __name__ == "__main__":
    unittest.main()
