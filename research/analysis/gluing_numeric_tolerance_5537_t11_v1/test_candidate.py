"""Pre-freeze construction tests for the T11 finite numeric boundary."""
import unittest

from audit_raw import check, mutation_manifest, mutate, reference
from candidate import evaluate
from run_experiment import CASES, TOLERANCES, CONTRACTS, ACTIONS, build_rows


class CandidateConstructionTests(unittest.TestCase):
    def test_minimax_values_and_unknown_context(self):
        expected = {"exact_cycle": (0, "GLOBAL_SECTION_CERTIFIED"),
                    "near_cycle": (2, "APPROXIMATE_SECTION"),
                    "far_cycle": (4, "APPROXIMATE_SECTION"),
                    "missing_context": (0, "UNKNOWN")}
        for case, (relations, complete) in CASES.items():
            with self.subTest(case=case):
                result = evaluate({"relations": relations, "complete": complete,
                                   "tolerance_ticks": 4, "contract": "exact_only",
                                   "action": "irreversible"})
                self.assertEqual((result["minimax_residual_ticks"], result["status"]),
                                 expected[case])
                if case == "missing_context":
                    self.assertFalse(result["admitted"])

    def test_tolerance_and_contract_boundaries(self):
        relations, complete = CASES["near_cycle"]
        def decide(tolerance, contract, action):
            return evaluate({"relations": relations, "complete": complete,
                             "tolerance_ticks": tolerance, "contract": contract,
                             "action": action})
        self.assertEqual(decide(1, "explicit_allow_approximate_irreversible", "irreversible")["status"],
                         "NO_GLOBAL_SECTION")
        self.assertFalse(decide(1, "explicit_allow_approximate_irreversible", "irreversible")["admitted"])
        self.assertTrue(decide(2, "reversible_approximate", "reversible")["admitted"])
        self.assertTrue(decide(2, "reversible_approximate", "compensable")["admitted"])
        self.assertFalse(decide(2, "reversible_approximate", "irreversible")["admitted"])
        self.assertFalse(decide(2, "exact_only", "reversible")["admitted"])
        self.assertTrue(decide(2, "explicit_allow_approximate_irreversible", "irreversible")["admitted"])

    def test_full_matrix_matches_fraction_oracle(self):
        rows = build_rows()
        self.assertEqual(len(rows), len(CASES) * len(TOLERANCES) * len(CONTRACTS) * len(ACTIONS))
        self.assertEqual(len(rows), 144)
        self.assertEqual(check(rows), [])
        for row in rows:
            self.assertEqual(row["decision_output"], reference(row["decision_input"]))

    def test_all_six_mutations_are_nonidentity_and_rejected(self):
        rows = build_rows()
        controls = mutation_manifest(rows)
        self.assertEqual(len(controls), 6)
        for name, *rest in controls:
            with self.subTest(mutation=name):
                altered = mutate(rows, name, (name, *rest))
                self.assertNotEqual(altered, rows)
                self.assertTrue(check(altered))


if __name__ == "__main__":
    unittest.main()
