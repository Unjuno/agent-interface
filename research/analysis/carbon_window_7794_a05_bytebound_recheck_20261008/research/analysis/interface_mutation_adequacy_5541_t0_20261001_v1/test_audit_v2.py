import unittest

from audit_v2 import independent_mutation_semantics, specification


class IndependentAuditSemanticsTests(unittest.TestCase):
    def setUp(self):
        self.valid = {
            "evidence_present": True,
            "evidence_fresh": True,
            "authority_matches": True,
            "outcome_known": True,
            "terminal_failure": False,
        }

    def test_terminal_failure_is_false_in_base_and_true_in_degraded_case(self):
        degraded = {**self.valid, "terminal_failure": True}
        self.assertTrue(specification(self.valid))
        self.assertFalse(specification(degraded))
        self.assertFalse(independent_mutation_semantics(degraded, "drop_provenance"))
        self.assertFalse(independent_mutation_semantics(degraded, "accept_stale"))
        self.assertFalse(independent_mutation_semantics(degraded, "ignore_authority"))
        self.assertFalse(independent_mutation_semantics(degraded, "commit_unknown"))
        self.assertTrue(independent_mutation_semantics(degraded, "reactivate_terminal"))

    def test_compound_mutant_triggers_only_on_declared_three_way_interaction(self):
        interaction = {**self.valid, "evidence_present": False,
                       "authority_matches": False, "terminal_failure": True}
        self.assertFalse(specification(interaction))
        self.assertTrue(independent_mutation_semantics(
            interaction, "compound_provenance_authority_terminal"))
        one_condition_missing = {**interaction, "terminal_failure": False}
        self.assertFalse(independent_mutation_semantics(
            one_condition_missing, "compound_provenance_authority_terminal"))


if __name__ == "__main__":
    unittest.main()
