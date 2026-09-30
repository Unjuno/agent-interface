import unittest

from audit_raw import check, mutate, mutation_manifest
from candidate import evaluate
from run_experiment import ACTIONS, CASES, CONTRACTS, TOLERANCES, build_rows


class T10ContractAndCoverageTests(unittest.TestCase):
    def test_matrix_is_complete_and_oracle_consistent(self):
        rows = build_rows()
        self.assertEqual(len(rows), 180)
        self.assertEqual(check(rows), [])

    def test_true_beyond_tolerance_case_exists_and_refuses_all(self):
        contexts = CASES["beyond_tolerance"]["contexts"]
        spread = max(c["spread"] for c in contexts)
        self.assertGreater(spread, 0.25)
        for contract in CONTRACTS:
            for action in ACTIONS:
                result = evaluate({"contexts": contexts, "complete": True, "tolerance": 0.25,
                                   "contract": contract, "action": action})
                self.assertEqual(result["status"], "NO_GLOBAL_SECTION")
                self.assertFalse(result["admitted"])

    def test_exact_only_rejects_approximation_for_every_action(self):
        contexts = CASES["within_tolerance"]["contexts"]
        for action in ACTIONS:
            result = evaluate({"contexts": contexts, "complete": True, "tolerance": 0.5,
                               "contract": "exact_only", "action": action})
            self.assertEqual(result["status"], "APPROXIMATE_SECTION")
            self.assertFalse(result["admitted"])

    def test_reversible_and_explicit_contracts_are_distinct(self):
        contexts = CASES["within_tolerance"]["contexts"]
        for action in ("reversible", "compensable"):
            self.assertTrue(evaluate({"contexts": contexts, "complete": True, "tolerance": 0.5,
                                      "contract": "reversible_approximate", "action": action})["admitted"])
        self.assertFalse(evaluate({"contexts": contexts, "complete": True, "tolerance": 0.5,
                                   "contract": "reversible_approximate", "action": "irreversible"})["admitted"])
        self.assertTrue(evaluate({"contexts": contexts, "complete": True, "tolerance": 0.5,
                                  "contract": "explicit_allow_approximate_irreversible",
                                  "action": "irreversible"})["admitted"])

    def test_every_frozen_mutation_is_nonidentity_and_rejected(self):
        rows = build_rows()
        manifest = mutation_manifest(rows)
        self.assertEqual(len(manifest), 6)
        for name, *rest in manifest:
            with self.subTest(name=name):
                changed = mutate(rows, name, (name, *rest))
                self.assertNotEqual(changed, rows)
                self.assertTrue(check(changed))

    def test_no_section_and_unknown_never_admit_even_with_explicit_contract(self):
        for case in ("no_global_section", "missing_context"):
            fixture = CASES[case]
            for action in ACTIONS:
                result = evaluate({"contexts": fixture["contexts"], "complete": fixture["complete"],
                                   "tolerance": 1.0,
                                   "contract": "explicit_allow_approximate_irreversible",
                                   "action": action})
                self.assertIn(result["status"], ("UNKNOWN", "NO_GLOBAL_SECTION"))
                self.assertFalse(result["admitted"])


if __name__ == "__main__":
    unittest.main()
