"""TDD contract for a distinct five-frame log-scale regression estimator."""

import unittest

try:
    from regression_estimator import estimate_ttc
except ModuleNotFoundError:
    estimate_ttc = None


class RegressionEstimatorTests(unittest.TestCase):
    def test_linear_radius_growth_recovers_hand_computed_contact_time(self):
        self.assertTrue(callable(estimate_ttc), "five-frame estimator must exist")
        # r(t)=5+2t; at t=4, remaining contact time is r/r'=13/2=6.5s.
        result = estimate_ttc((0, 1, 2, 3, 4), (5, 7, 9, 11, 13))
        self.assertAlmostEqual(result, 6.5)

    def test_nonmonotonic_or_duplicate_timestamps_are_rejected(self):
        self.assertTrue(callable(estimate_ttc), "five-frame estimator must exist")
        with self.assertRaisesRegex(ValueError, "strictly_increasing_times"):
            estimate_ttc((0, 1, 1, 3, 4), (5, 7, 9, 11, 13))

    def test_nonpositive_growth_has_no_contact_estimate(self):
        self.assertTrue(callable(estimate_ttc), "five-frame estimator must exist")
        self.assertIsNone(estimate_ttc((0, 1, 2, 3, 4), (7, 7, 7, 7, 7)))


if __name__ == "__main__":
    unittest.main()
