import unittest

import audit_power
import power_model


class OrdinalPowerModelTests(unittest.TestCase):
    def test_proportional_odds_shift_preserves_probability_mass_and_stochastic_order(self):
        baseline = [0.10, 0.15, 0.25, 0.30, 0.20]
        shifted = power_model.shift_distribution(baseline, odds_ratio=1.5)

        self.assertAlmostEqual(sum(shifted), 1.0)
        for cut in range(1, len(baseline)):
            self.assertGreaterEqual(sum(shifted[cut:]), sum(baseline[cut:]))

    def test_calibration_hits_requested_standardized_mean_difference(self):
        baseline = [0.10, 0.15, 0.25, 0.30, 0.20]
        odds_ratio, shifted, achieved = power_model.calibrate_effect(baseline, 0.35)

        self.assertGreater(odds_ratio, 1.0)
        self.assertAlmostEqual(achieved, 0.35, places=6)
        self.assertAlmostEqual(sum(shifted), 1.0)

    def test_rank_statistic_keeps_ties_and_scores_higher_ordinals_as_better(self):
        self.assertEqual(power_model.rank_sum_u([0, 0, 0, 0, 4], [0, 0, 4, 0, 0]), 16.0)
        self.assertEqual(power_model.rank_sum_u([0, 0, 4, 0, 0], [0, 0, 0, 0, 4]), 0.0)

    def test_seeded_power_cell_is_reproducible_and_null_control_is_near_alpha(self):
        distribution = [0.10, 0.15, 0.25, 0.30, 0.20]
        first = power_model.simulate_rank_power(distribution, distribution, n=120, reps=12000, seed=811)
        second = power_model.simulate_rank_power(distribution, distribution, n=120, reps=12000, seed=811)

        self.assertEqual(first, second)
        self.assertLessEqual(abs(first["power"] - 0.0125), 0.004)

    def test_independent_raw_reconstruction_matches_small_seeded_cell(self):
        baseline = [0.10, 0.15, 0.25, 0.30, 0.20]
        _, alternative, _ = power_model.calibrate_effect(baseline, 0.35)
        candidate = power_model.simulate_rank_power(baseline, alternative, n=24, reps=600, seed=8032026)
        rejected, digest = audit_power.reconstruct(baseline, alternative, 24, 600, 8032026, 2.498)

        self.assertEqual(candidate["rejections"], rejected)
        self.assertEqual(candidate["pooled_category_counts_sha256"], digest)


if __name__ == "__main__":
    unittest.main()
