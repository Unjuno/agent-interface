import unittest

from build_inputs import ARMS, FAMILIES, build


class InputDeckTests(unittest.TestCase):
    def test_each_arm_has_matched_hidden_state_support_without_public_ids(self):
        public, private = build(614720261001)
        for arm in ARMS:
            self.assertEqual(len(public[arm]), 10)
            self.assertEqual(len(private[arm]), 10)
            self.assertTrue(all(set(row) == {"trial_index", "family"} for row in public[arm]))
            self.assertEqual(
                {(row["family"], row["state_id"]) for row in private[arm]},
                {(family, state) for family, states in FAMILIES.items() for state in states},
            )
            self.assertEqual(
                [row["family"] for row in public[arm]],
                [row["family"] for row in private[arm]],
            )

    def test_arm_decks_do_not_reuse_the_same_hidden_member_order(self):
        _, private = build(614720261001)
        orders = {
            arm: tuple(row["state_id"] for row in private[arm])
            for arm in ARMS
        }
        self.assertEqual(len(set(orders.values())), len(ARMS))


if __name__ == "__main__":
    unittest.main()
