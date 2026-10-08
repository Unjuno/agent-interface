import random
import unittest

from research.analysis.extreme_tail_eligibility_6576_construction_v1.tailid_equivalent import (
    fit_gpd_shape,
    quantile_type7,
    shape_interval,
    tailid_sensitive_upper,
)


class TailIDEquivalentConstructionTests(unittest.TestCase):
    def test_type7_quantile_interpolates(self):
        self.assertEqual(quantile_type7([0.0, 10.0], 0.25), 2.5)

    def test_shape_ci_uses_abs_shape_and_n(self):
        lower, upper = shape_interval(0.5, 100, 0.95)
        self.assertAlmostEqual(lower, 0.402, places=3)
        self.assertAlmostEqual(upper, 0.598, places=3)

    def test_gpd_mle_on_exponential_seed_is_near_zero_shape(self):
        rng = random.Random(657601)
        sample = [rng.expovariate(1.0) for _ in range(6000)]
        threshold = quantile_type7(sample, 0.90)
        excesses = [value - threshold for value in sample if value > threshold]
        self.assertLess(abs(fit_gpd_shape(excesses)), 0.35)

    def test_tailid_returns_frozen_candidate_cardinality(self):
        rng = random.Random(657602)
        sample = [rng.expovariate(1.0) for _ in range(4000)]
        result = tailid_sensitive_upper(sample)
        self.assertEqual(result["candidate_count"], 20)
        self.assertEqual(result["threshold"], quantile_type7(sample, 0.90))
        self.assertLessEqual(len(result["sensitive"]), 20)


if __name__ == "__main__":
    unittest.main()
