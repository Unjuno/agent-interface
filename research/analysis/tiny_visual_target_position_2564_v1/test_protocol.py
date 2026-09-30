from __future__ import annotations

import unittest

import numpy as np

from prepare import (CONSTRUCTION_SEED, EVAL_CENTERS, FORMAL_SEEDS, SUPPORT_CENTERS,
                     construction_summary, evaluation_data, training_data)
from train import gate_fixture


class ProtocolTests(unittest.TestCase):
    def test_pairing_balance_and_only_positive_positions_change(self):
        summary = construction_summary()
        self.assertEqual(summary["construction_seed"], CONSTRUCTION_SEED)
        self.assertEqual(summary["control_rows"], 160)
        self.assertEqual(summary["treatment_rows"], 160)
        self.assertEqual(summary["positive_rows_per_arm"], 80)
        self.assertEqual(summary["negative_rows_per_arm"], 80)
        x0, y0, _ = training_data(8962701, "control")
        x1, y1, _ = training_data(8962701, "treatment")
        self.assertTrue(np.array_equal(y0, y1))
        self.assertTrue(np.array_equal(x0[1::2], x1[1::2]))
        self.assertFalse(np.array_equal(x0[0::2], x1[0::2]))

    def test_holdout_positions_are_outside_treatment_support(self):
        support = set(SUPPORT_CENTERS)
        self.assertNotIn(EVAL_CENTERS["translation_a"], support)
        self.assertNotIn(EVAL_CENTERS["translation_b"], support)
        for index, (name, center) in enumerate(EVAL_CENTERS.items()):
            x, y, rows = evaluation_data(8962702 + index, name)
            self.assertEqual(x.shape, (80, 1200))
            self.assertEqual(int(y.sum()), 40)
            self.assertEqual({tuple(r["positive_center"]) for r in rows if r["label"]}, {center})

    def test_formal_seed_blocks_are_disjoint(self):
        self.assertEqual(len(FORMAL_SEEDS), len(set(FORMAL_SEEDS)))
        self.assertTrue(all(b - a == 100 for a, b in zip(FORMAL_SEEDS, FORMAL_SEEDS[1:])))
        for seed in FORMAL_SEEDS:
            self.assertFalse(8962700 <= seed <= 8962799)

    def test_receipt_gate_fails_closed_on_stale_or_mismatched_controls(self):
        decisions = {row["case_id"]: row["final_accept"] for row in gate_fixture()}
        self.assertEqual(decisions, {"current_matching_positive": True,
                                     "stale_high_positive": False,
                                     "digest_mismatch_high_positive": False,
                                     "current_negative": False})


if __name__ == "__main__":
    unittest.main(verbosity=2)

