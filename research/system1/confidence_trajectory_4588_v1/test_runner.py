import random
import unittest

import runner
import audit


class CorpusContractTests(unittest.TestCase):
    def test_exact_ten_seed_schedule(self):
        self.assertEqual(runner.SEEDS, list(range(2026100100, 2026101001, 100)))
        self.assertEqual(len(runner.SEEDS), 10)

    def test_alias_pair_current_and_velocity_identical_acceleration_differs(self):
        rows = [runner.example(random.Random(1), 2026100100, "test", "alias_accel", i)
                for i in range(2)]
        a, b = rows
        for i in (0, 1, 2, 3, 6, 7, 8):
            self.assertEqual(a["features"][i], b["features"][i])
        self.assertNotEqual(a["features"][4], b["features"][4])
        self.assertEqual(a["label"], 0)
        self.assertEqual(b["label"], 2)

    def test_all_history_variants_fail_closed_target_yield(self):
        rows = [runner.example(random.Random(i), 2026100100, "train", "stale_yield", i)
                for i in range(90)]
        self.assertEqual({r["history_status"] for r in rows}, {"stale", "missing", "epoch_mismatch"})
        self.assertTrue(all(r["label"] == 3 and r["features"][7] == 0.0 for r in rows))

    def test_four_arms_use_fixed_equal_width_head_masks(self):
        self.assertEqual(set(runner.ARMS), {"CURRENT_ONLY", "LEVEL_VELOCITY",
                                           "LEVEL_VELOCITY_ACCEL", "CAUSAL_SMOOTHED"})
        self.assertTrue(all(set(mask) <= set(range(9)) for mask in runner.ARMS.values()))
        self.assertNotIn(4, runner.ARMS["LEVEL_VELOCITY"])
        self.assertIn(4, runner.ARMS["LEVEL_VELOCITY_ACCEL"])
        self.assertEqual(len(runner.ARMS["LEVEL_VELOCITY_ACCEL"]), 9)

    def test_separate_action_noop_yield_classes(self):
        self.assertEqual(runner.CLASS_NAMES, ["ACTION_A", "ACTION_B", "NO_OP", "YIELD"])

    def test_independent_auditor_regenerates_identical_rows_without_runner_import(self):
        for split in ("train", "test"):
            self.assertEqual(runner.dataset(2026100100, split), audit.regen(2026100100, split))


if __name__ == "__main__":
    unittest.main()

