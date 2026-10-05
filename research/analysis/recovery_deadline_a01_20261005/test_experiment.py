import unittest

from experiment import Episode, audit, conformal_deadline, decide, freeze_fixture
from audit import recompute


class RecoveryDeadlineTests(unittest.TestCase):
    def test_exchangeable_finite_fixture_uses_split_conformal_rank(self):
        calibration, evaluation = freeze_fixture()
        result = audit(calibration, evaluation, .2)
        self.assertEqual(result["rank"], 9)
        self.assertEqual(result["deadline"], 9)
        self.assertTrue(result["coverage_pass"])
        self.assertEqual(result["coverage"], 1.0)
        self.assertEqual(result["hard_delayed"], [])
        self.assertGreater(result["recoverable_retained"],
                           result["immediate_latch_retained"])
        self.assertEqual(result["recoverable_retained"],
                         result["fixed_timeout_9_retained"])
        self.assertGreater(result["hysteresis_2_retained"], 0)

    def test_small_calibration_is_uncertified(self):
        calibration = [Episode(str(i), "calibration", "recoverable", i)
                       for i in range(1, 4)]
        self.assertIsNone(conformal_deadline(calibration, .1))
        self.assertEqual(decide(Episode("x", "evaluation", "recoverable", 1), None),
                         "uncertified_yield")

    def test_right_censored_calibration_cannot_claim_finite_deadline(self):
        calibration, _ = freeze_fixture()
        calibration[0] = Episode("c0", "calibration", "recoverable", None,
                                 censor_at=5)
        self.assertIsNone(conformal_deadline(calibration, .2))

    def test_hard_identity_focus_lease_bypass_deadline(self):
        for kind in ("identity_loss", "focus_loss", "lease_loss"):
            self.assertEqual(decide(Episode(kind, "evaluation", kind, None,
                                            hard_event=True), 999), "immediate_yield")

    def test_distribution_shift_is_not_certified_by_exchangeable_quantile(self):
        calibration, _ = freeze_fixture()
        shifted = [Episode(f"s{i}", "evaluation", "recoverable", d,
                           stratum="shift")
                   for i, d in enumerate((11, 12, 13, 14, 15))]
        deadline = conformal_deadline(calibration, .2)
        self.assertEqual(deadline, 9)
        self.assertTrue(all(decide(e, deadline) == "uncertified_yield" for e in shifted))

    def test_nonrecovering_and_censored_evaluation_fall_back_at_deadline(self):
        self.assertEqual(decide(Episode("d", "evaluation", "diverging", None,
                                        censor_at=20), 9), "deadline_yield")

    def test_independent_oracle_reconstructs_every_finite_row(self):
        calibration, evaluation = freeze_fixture()
        result = audit(calibration, evaluation, .2)
        oracle = recompute(calibration, evaluation, .2)
        self.assertTrue(oracle["accepted"])
        self.assertEqual(oracle["deadline"], result["deadline"])
        self.assertEqual(oracle["coverage"], result["coverage"])
        self.assertEqual(oracle["hard_delayed"], result["hard_delayed"])
        self.assertEqual(oracle["evaluation_n"], 19)
        self.assertEqual(oracle["right_censored_n"], 1)
        self.assertEqual(len(oracle["shift_uncertified"]), 5)

    def test_mutation_evaluation_leakage_is_rejected(self):
        calibration, evaluation = freeze_fixture()
        leaked = calibration + [evaluation.pop()]
        oracle = recompute(leaked, evaluation, .2)
        self.assertFalse(oracle["accepted"])
        self.assertIn(oracle["reason"], {
            "duplicate_or_leaked_episode_id", "evaluation_outcome_leaked_into_calibration"})

    def test_mutation_hard_event_relabelled_soft_is_rejected(self):
        calibration, evaluation = freeze_fixture()
        mutated = list(evaluation)
        mutated = [Episode("hard-lease", "evaluation", "recoverable", 1,
                           hard_event=True) if row.episode_id == "hard-lease" else row
                   for row in mutated]
        result = recompute(calibration, mutated, .2)
        self.assertFalse(result["accepted"])
        self.assertEqual(result["reason"], "oracle_label_mutation")

    def test_mutation_dropping_censored_row_changes_expected_partition_size(self):
        calibration, evaluation = freeze_fixture()
        expected_ids = {row.episode_id for row in evaluation}
        dropped = [row for row in evaluation if row.kind != "right_censored"]
        result = recompute(calibration, dropped, .2)
        self.assertNotEqual({row.episode_id for row in dropped}, expected_ids)
        self.assertFalse(result["accepted"])
        self.assertEqual(result["reason"], "evaluation_partition_manifest_mismatch")

    def test_mutation_continuation_after_deadline_is_detected_by_oracle_row(self):
        calibration, evaluation = freeze_fixture()
        result = recompute(calibration, evaluation, .2)
        self.assertIn(("diverge-0", "diverging", "deadline_yield"), result["rows"])
        self.assertIn(("censored-0", "right_censored", "deadline_yield"), result["rows"])
        self.assertEqual(decide(Episode("c", "evaluation", "right_censored", None,
                                        censor_at=20), 9), "deadline_yield")


if __name__ == "__main__":
    unittest.main()
