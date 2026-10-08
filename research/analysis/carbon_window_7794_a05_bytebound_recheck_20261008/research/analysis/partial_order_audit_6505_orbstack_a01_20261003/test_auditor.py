import hashlib
import unittest

import auditor


class AuditConstruction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.states = auditor.enumerate_reachable()
        cls.relation = {left: {right: auditor.pair_is_independent(left, right, cls.states)
                               for right in auditor.FROZEN_EVENTS} for left in auditor.FROZEN_EVENTS}

    def test_git_blob_identity_uses_git_header(self):
        self.assertEqual(auditor.git_blob_id(b"test\n"), "9daeafb9864cf43055ae93beb0afd6c7d144bfa4")

    def test_declared_event_universe_is_finite(self):
        self.assertEqual(len(self.states), 2025)
        self.assertIn(auditor.ORIGIN, self.states)

    def test_pair_commutativity_checks_stable_occurrence_results(self):
        self.assertTrue(self.relation["TOOL0"]["OPEN"])
        self.assertFalse(self.relation["OPEN"]["CLOSE"])

    def test_topological_control_exposes_two_orders(self):
        self.assertEqual(set(auditor.all_linearizations(2, [])), {(0, 1), (1, 0)})
        self.assertEqual(auditor.all_linearizations(2, [(0, 1)]), [(0, 1)])

    def test_linearizations_mutation_changes_value_and_fails_row_oracle(self):
        expected = auditor.expected_record(("OPEN", "CLOSE"), self.relation)
        mutated = auditor.mutations_for(expected)["linearizations"]
        self.assertEqual(expected["linearizations"], 1)
        self.assertEqual(mutated["linearizations"], 0)
        self.assertNotEqual(mutated["linearizations"], expected["linearizations"])
        self.assertNotEqual(mutated, expected)

    def test_all_eight_mutations_are_effective_on_discriminator_row(self):
        expected = auditor.expected_record(("OPEN", "CLOSE"), self.relation)
        controls = auditor.mutations_for(expected)
        self.assertEqual(len(controls), 8)
        self.assertTrue(all(record != expected and record[name] != expected[name]
                            for name, record in controls.items()))

    def test_archive_declaration_is_pinned(self):
        self.assertEqual(hashlib.sha256(b"abc").hexdigest(), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
        self.assertEqual(auditor.RAW_BYTES, 3241590)
        self.assertEqual(auditor.WORDS, 11111)
        self.assertEqual(auditor.RAW_SHA256, "a25bc4a9e6cf845fb5b446b1d2d5071bd26909679efcc535372fdf77b58b4eb8")


if __name__ == "__main__":
    unittest.main()
