import unittest

from trials import make_trials


class TrialPlanTests(unittest.TestCase):
    def test_formal_plan_is_reproducible_and_balanced(self):
        first = make_trials()
        self.assertEqual(first, make_trials())
        self.assertEqual(len(first), 180)
        self.assertEqual(len({row["trial_id"] for row in first}), 180)
        for block in range(1, 31):
            rows = [row for row in first if row["block"] == block]
            self.assertEqual(len(rows), 6)
            self.assertEqual({row["arm"] for row in rows}, {"MINIMAL", "SCREENSHOT", "SHAM"})
            self.assertEqual({row["schedule"] for row in rows}, {"SENSITIVE", "STABLE"})

    def test_seed_changes_randomized_order_not_frozen_conditions(self):
        a = make_trials(seed=652604, blocks=2)
        b = make_trials(seed=652605, blocks=2)
        self.assertNotEqual([x["trial_id"] for x in a], [x["trial_id"] for x in b])
        self.assertEqual(sorted((x["block"], x["schedule"], x["arm"]) for x in a),
                         sorted((x["block"], x["schedule"], x["arm"]) for x in b))


if __name__ == "__main__":
    unittest.main(verbosity=2)
