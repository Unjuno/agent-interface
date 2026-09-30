import math
import unittest

import run


class ConstructionTests(unittest.TestCase):
    def test_finite_sample_rank(self):
        self.assertEqual(math.ceil(5 * 0.9), 5)
        self.assertEqual(math.ceil(11 * 0.9), 10)

    def test_unattainable_rank_is_full_set_not_clipped(self):
        self.assertEqual(run.threshold([0.1, 0.2, 0.3, 0.4], 5), math.inf)
        self.assertEqual(run.prediction_set(math.inf, 0.99, 0.98), ["PASS", "FAIL"])

    def test_shift_flag_suppresses_singleton(self):
        result = run.prediction_set(0.99, 0.1, 0.995, shift_detected=True)
        self.assertEqual(result, ["FAIL", "PASS"])
        self.assertEqual(run.metrics(result)["singleton"], False)

    def test_wrong_singleton_is_not_counted_as_true_coverage(self):
        result = run.metrics(["FAIL"])
        self.assertFalse(result["true_included"])
        self.assertTrue(result["wrong_singleton"])


if __name__ == "__main__":
    unittest.main()
