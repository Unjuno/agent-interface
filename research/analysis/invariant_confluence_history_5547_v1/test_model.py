import unittest

from model import COMMANDS, INITIAL, apply, enumerate_states, execute, join, violations


class HistoryClosureTests(unittest.TestCase):
    def test_root_only_does_not_certify_unenabled_commit(self):
        self.assertIsNone(apply(INITIAL, ("COMMIT", "dispatch-0", "effect-a")))
        self.assertEqual(execute()["root_only_commit_classification"], "NOT_PROVEN_PRECONDITION_FALSE")

    def test_authorization_makes_commit_reachable(self):
        authorized = apply(INITIAL, ("AUTHORIZE", "effect-a"))
        self.assertIsNotNone(authorized)
        self.assertIsNotNone(apply(authorized, ("COMMIT", "dispatch-0", "effect-a")))

    def test_independent_commit_branches_are_each_valid_but_join_is_not(self):
        base = apply(INITIAL, ("AUTHORIZE", "effect-a"))
        left = apply(base, ("COMMIT", "dispatch-0", "effect-a"))
        right = apply(base, ("COMMIT", "dispatch-1", "effect-a"))
        self.assertEqual(violations(left), [])
        self.assertEqual(violations(right), [])
        self.assertEqual(violations(join(left, right)), ["duplicate_semantic_effect"])

    def test_serial_baseline_rejects_second_commit(self):
        result = execute()
        self.assertTrue(result["serializable_all_orders_safe"])
        witness = next(x for x in result["counterexamples"]
                       if x["base"]["authorized"] == ["effect-a"]
                       and x["left_command"][0] == x["right_command"][0] == "COMMIT")
        self.assertTrue(all(order["second_outcome"] == "second_rejected" for order in witness["serial_orders"]))

    def test_unknown_commands_fail_closed(self):
        self.assertIsNone(apply(INITIAL, ("UNKNOWN", "x")))

    def test_finite_enumeration_contains_expected_history(self):
        self.assertIn(apply(INITIAL, ("AUTHORIZE", "effect-a")), enumerate_states(2))
        self.assertEqual(execute()["disposition"], "PASS_HISTORY_DEPENDENT_COUNTEREXAMPLE")


if __name__ == "__main__":
    unittest.main()
