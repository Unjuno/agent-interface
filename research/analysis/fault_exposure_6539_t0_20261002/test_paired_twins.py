import unittest

from paired_twins import exhaustive_policy_table, paired_twins, score


class PairedTwinIdentifiabilityTests(unittest.TestCase):
    def test_policy_inputs_are_identical_but_hidden_authority_differs(self):
        authorized, unauthorized = paired_twins()
        self.assertEqual(authorized.visible, unauthorized.visible)
        self.assertTrue(authorized.authorized)
        self.assertFalse(unauthorized.authorized)

    def test_non_yield_cannot_complete_authorized_twin_and_remain_safe(self):
        authorized, unauthorized = paired_twins()
        self.assertTrue(score(authorized, "CONTINUE")["authorized_completion"])
        for proposal in ("CONTINUE", "RECOVER"):
            self.assertTrue(score(unauthorized, proposal)["unsafe_proposal"])
        self.assertFalse(score(authorized, "RECOVER")["authorized_completion"])

    def test_yield_is_safe_but_not_recovery_on_authorized_twin(self):
        authorized, unauthorized = paired_twins()
        self.assertTrue(score(unauthorized, "YIELD")["unsafe_proposal"] is False)
        self.assertFalse(score(authorized, "YIELD")["authorized_completion"])
        self.assertTrue(score(authorized, "YIELD")["unnecessary_yield"])

    def test_table_has_no_policy_choice_that_meets_both_goals(self):
        for row in exhaustive_policy_table():
            safe = not row["unauthorized"]["unsafe_proposal"]
            completes = row["authorized"]["authorized_completion"]
            self.assertFalse(safe and completes, row)


if __name__ == "__main__":
    unittest.main()
