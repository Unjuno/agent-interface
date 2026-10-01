import unittest

from run import GRID, ORDERS, PREDICATES, eval_order


class DriftProtocolTests(unittest.TestCase):
    def test_complete_four_predicate_truth_space(self):
        self.assertEqual(len({tuple(bool(mask & (1 << i)) for i in range(4)) for mask in range(16)}), 16)

    def test_orders_are_permutations(self):
        for order in ORDERS.values():
            self.assertEqual(set(order), set(PREDICATES))

    def test_frozen_grid_has_both_endpoints_and_uniform_steps(self):
        self.assertEqual((GRID[0], GRID[-1], len(GRID)), (0.0, 1.0, 21))
        self.assertTrue(all(round(GRID[i + 1] - GRID[i], 2) == 0.05 for i in range(20)))

    def test_both_orders_preserve_and_semantics_on_all_states(self):
        for mask in range(16):
            state = {name: bool(mask & (1 << bit)) for bit, name in enumerate(PREDICATES)}
            for order in ORDERS.values():
                decision, _, _ = eval_order(state, order)
                self.assertEqual(decision, all(state.values()))

    def test_naive_and_learned_have_declared_development_boundary(self):
        early_false = {"A": False, "B": True, "C": True, "D": True}
        all_true = {name: True for name in PREDICATES}
        learned_early = eval_order(early_false, ORDERS["FROZEN_COST_SELECTIVITY"])[1]
        naive_early = eval_order(early_false, ORDERS["NAIVE"])[1]
        self.assertLess(learned_early, naive_early)
        self.assertEqual(eval_order(all_true, ORDERS["NAIVE"])[1], eval_order(all_true, ORDERS["FROZEN_COST_SELECTIVITY"])[1])


if __name__ == "__main__":
    unittest.main(verbosity=2)

