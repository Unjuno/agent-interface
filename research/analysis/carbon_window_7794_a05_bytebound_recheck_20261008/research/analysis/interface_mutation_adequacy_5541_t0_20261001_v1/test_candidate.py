import unittest

from candidate import MUTANTS, all_states, decide, mutated_decide


class MutationAdequacyCandidateTests(unittest.TestCase):
    def setUp(self):
        self.nominal = {
            "evidence_present": True,
            "evidence_fresh": True,
            "authority_matches": True,
            "outcome_known": True,
            "terminal_failure": False,
        }

    def test_only_complete_fresh_known_authorized_nonterminal_state_commits(self):
        self.assertTrue(decide(self.nominal))
        for field, invalid in (
            ("evidence_present", False), ("evidence_fresh", False),
            ("authority_matches", False), ("outcome_known", False),
            ("terminal_failure", True),
        ):
            with self.subTest(field=field):
                self.assertFalse(decide({**self.nominal, field: invalid}))

    def test_five_single_gate_mutants_have_declared_witnesses(self):
        witnesses = {
            "drop_provenance": {"evidence_present": False},
            "accept_stale": {"evidence_fresh": False},
            "ignore_authority": {"authority_matches": False},
            "commit_unknown": {"outcome_known": False},
            "reactivate_terminal": {"terminal_failure": True},
        }
        for operator, change in witnesses.items():
            with self.subTest(operator=operator):
                state = {**self.nominal, **change}
                self.assertFalse(decide(state))
                self.assertTrue(mutated_decide(state, operator))

    def test_compound_interaction_mutant_has_nontrivial_counterexample(self):
        state = {**self.nominal, "evidence_present": False,
                 "authority_matches": False, "terminal_failure": True}
        self.assertFalse(decide(state))
        self.assertTrue(mutated_decide(
            state, "compound_provenance_authority_terminal"))

    def test_enumeration_is_complete_and_unique(self):
        states = [tuple(s[k] for k in (
            "evidence_present", "evidence_fresh", "authority_matches",
            "outcome_known", "terminal_failure")) for s in all_states()]
        self.assertEqual(len(states), 32)
        self.assertEqual(len(set(states)), 32)

    def test_every_declared_mutant_is_non_equivalent_over_the_domain(self):
        for operator in MUTANTS:
            with self.subTest(operator=operator):
                self.assertTrue(any(
                    mutated_decide(state, operator) != decide(state)
                    for state in all_states()
                ))


if __name__ == "__main__":
    unittest.main()
