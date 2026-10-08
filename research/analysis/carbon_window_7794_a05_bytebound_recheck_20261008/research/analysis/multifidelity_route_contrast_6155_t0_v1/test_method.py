import unittest
from copy import deepcopy

import audit
import candidate


class RouteContrastMethodTests(unittest.TestCase):
    def test_seeded_raw_block_reconstructs_exact_budget(self):
        for case in candidate.CASES:
            for k in candidate.KS:
                result = audit.reconstruct(candidate.one_block(case, k, 7))
                expected = 6464 + 2100 * k
                self.assertEqual(expected, (64 + 20 * k) * 101 + 80 * k)
                self.assertEqual(expected, (21 * k + 64) * 100 + 64)
                self.assertTrue(-1.0 <= result["delta_r"] <= 1.0)
                self.assertTrue(-1.0 <= result["level_r"] <= 1.0)

    def test_signed_predictive_differences_have_signed_covariance(self):
        pos = candidate.one_block("delta_positive", 20, 11)["pilot"]
        neg = candidate.one_block("delta_negative", 20, 11)["pilot"]
        self.assertGreater(audit.corr([r[0] for r in pos], [r[1] for r in pos]), 0.45)
        self.assertLess(audit.corr([r[0] for r in neg], [r[1] for r in neg]), -0.45)

    def test_shared_level_control_is_not_used_to_fit_difference_beta(self):
        raw = candidate.one_block("shared_level_only", 20, 19)
        self.assertGreater(audit.corr([r[4] for r in raw["scored"]], [r[5] for r in raw["scored"]]), 0.90)
        self.assertLess(abs(audit.corr([r[0] for r in raw["pilot"]], [r[1] for r in raw["pilot"]])), 0.45)

    def test_auditor_rejects_arm_difference_corruption(self):
        raw = deepcopy(candidate.one_block("delta_positive", 5, 23))
        raw["scored"][0][4] += 1.0
        with self.assertRaisesRegex(ValueError, "inconsistent arm/difference"):
            audit.reconstruct(raw)

    def test_auditor_rejects_unequal_total_cost(self):
        raw = candidate.one_block("delta_negative", 1, 29)
        raw["budget_x"].pop()
        with self.assertRaisesRegex(ValueError, "cost-control sample count"):
            audit.reconstruct(raw)


if __name__ == "__main__":
    unittest.main()
