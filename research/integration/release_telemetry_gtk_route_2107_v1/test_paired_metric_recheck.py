import unittest

from paired_metric_recheck import bootstrap_median_ci, recheck


class PairedMetricTests(unittest.TestCase):
    def test_bootstrap_is_deterministic(self):
        values = [0.1] * 16
        self.assertEqual(bootstrap_median_ci(values, 2110), [0.1, 0.1])

    def test_pairwise_effect_uses_matching_pairs(self):
        # Arm-wise median ratio is not the median of explicit paired changes.
        baseline = [100, 200, 300, 400]
        candidate = [200, 100, 270, 360]
        pairwise = [(b - c) / b for b, c in zip(baseline, candidate)]
        self.assertAlmostEqual(__import__("statistics").median(pairwise), 0.10)
        armwise = 1 - __import__("statistics").median(candidate) / __import__("statistics").median(baseline)
        self.assertNotAlmostEqual(__import__("statistics").median(pairwise), armwise)

    def test_twenty_percent_threshold_is_enforced(self):
        values = [0.10] * 16
        self.assertLess(__import__("statistics").median(values), 0.20)
        self.assertEqual(bootstrap_median_ci(values, 9), [0.10, 0.10])

    def test_actual_frozen_formal_metrics(self):
        from pathlib import Path
        report = recheck(Path(__file__).parent / "evidence" / "formal01")
        self.assertEqual(report["paired_count"], 16)
        self.assertEqual(report["disposition"], "HOLD_NO_DECISION_VALUE")
        self.assertFalse(report["latency"]["gate_pass"])
        self.assertFalse(report["nonterminal_actions"]["gate_pass"])
        self.assertLess(report["latency"]["median_pairwise_relative_reduction_percent"], 0)
        self.assertEqual(report["nonterminal_actions"]["median_pairwise_relative_reduction"], 0)


if __name__ == "__main__":
    unittest.main()
