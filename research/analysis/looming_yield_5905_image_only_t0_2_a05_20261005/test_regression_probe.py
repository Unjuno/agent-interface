"""Invalid tracker controls must not abort the regression screen."""

import unittest

try:
    from regression_probe import screen_estimate
except ImportError:
    screen_estimate = None


class RegressionProbeTests(unittest.TestCase):
    def test_untrackable_clock_is_abstained_without_fitting(self):
        self.assertTrue(callable(screen_estimate), "screen gate must exist")
        self.assertIsNone(screen_estimate("UNKNOWN", (0, 1, 1, 3, 4),
                                          (5, 7, 9, 11, 13)))

    def test_trackable_samples_use_all_five_observations(self):
        self.assertTrue(callable(screen_estimate), "screen gate must exist")
        self.assertAlmostEqual(screen_estimate("TRACKABLE", (0, 1, 2, 3, 4),
                                               (5, 7, 9, 11, 13)), 6.5)


if __name__ == "__main__":
    unittest.main()
