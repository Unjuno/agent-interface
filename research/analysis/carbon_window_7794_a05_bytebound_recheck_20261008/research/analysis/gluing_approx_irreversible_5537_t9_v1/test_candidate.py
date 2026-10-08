import unittest

from audit_raw import check, mutate, mutation_manifest
from run_experiment import build_rows


class T9MutationPreconditions(unittest.TestCase):
    def setUp(self):
        self.rows = build_rows()

    def test_frozen_matrix_matches_independent_oracle(self):
        self.assertEqual(len(self.rows), 135)
        self.assertEqual(check(self.rows), [])

    def test_every_mutation_has_unique_selector_and_nonidentity(self):
        manifest = mutation_manifest(self.rows)
        self.assertEqual(len(manifest), 6)
        for name, *entry in manifest:
            with self.subTest(name=name):
                changed = mutate(self.rows, name, (name, *entry))
                self.assertNotEqual(changed, self.rows)
                self.assertTrue(check(changed), name)

    def test_false_admission_target_is_initially_refused(self):
        row = next(r for r in self.rows if r["decision_input"]["case"] == "within_tolerance"
                   and r["decision_input"]["tolerance"] == 0.5
                   and r["decision_input"]["contract"] == "reversible_approximate"
                   and r["decision_input"]["action"] == "irreversible")
        self.assertEqual(row["decision_output"]["status"], "APPROXIMATE_SECTION")
        self.assertIs(row["decision_output"]["admitted"], False)


if __name__ == "__main__":
    unittest.main()
