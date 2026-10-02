import unittest

import experiment


class ConstructionTests(unittest.TestCase):
    def test_immediate_commits_proposal_before_observation(self):
        row = experiment.run_one("informative_signal_1", 0, "IMMEDIATE")
        self.assertEqual(row["committed_target"], "A")
        self.assertEqual([e["op"] for e in row["events"]], ["commit"])

    def test_stage_one_uses_first_informative_signal(self):
        row = experiment.run_one("informative_signal_1", 0, "STAGE_1")
        self.assertEqual(row["committed_target"], "B")

    def test_stage_two_waits_for_second_signal(self):
        row = experiment.run_one("informative_signal_2", 0, "STAGE_2")
        self.assertEqual(row["committed_target"], "B")
        self.assertEqual(sum(e["op"] == "observe" for e in row["events"]), 2)

    def test_uninformative_control_does_not_change_target(self):
        row = experiment.run_one("uninformative", 0, "STAGE_2")
        self.assertEqual(row["committed_target"], "A")

    def test_missing_route_does_not_change_target(self):
        row = experiment.run_one("no_correction_route", 0, "STAGE_1")
        self.assertEqual(row["committed_target"], "A")

    def test_all_deadlines_allow_frozen_commit_times(self):
        for stratum in experiment.STRATA:
            for policy in experiment.POLICIES:
                self.assertFalse(experiment.run_one(stratum, 0, policy)["deadline_miss"])


if __name__ == "__main__":
    unittest.main()
