"""T12 construction tests for incomplete scope and strict schema auditing."""
import unittest
import json

from audit_raw import check, mutation_manifest, mutate, reference, valid_input, valid_output
from candidate import evaluate
from run_experiment import ACTIONS, CASES, CONTRACTS, TOLERANCES, build_rows


class ScopeAndSchemaTests(unittest.TestCase):
    def test_incomplete_output_has_no_full_cover_certificate(self):
        relations, complete = CASES["missing_context"]
        output = evaluate({"relations": relations, "complete": complete, "tolerance_ticks": 4,
                           "contract": CONTRACTS[0], "action": ACTIONS[0]})
        self.assertEqual(output["observed_subgraph_minimax_residual_ticks"], 0)
        self.assertEqual(output["residual_scope"], "observed_subgraph_only")
        self.assertIsNone(output["minimax_residual_ticks"])
        self.assertEqual(output["optimal_witnesses"], [])
        self.assertEqual(output["optimal_witness_count"], 0)
        self.assertEqual(output["status"], "UNKNOWN")
        self.assertIs(output["admitted"], False)

    def test_complete_case_minimax_and_contract_boundaries(self):
        expected = {"exact_cycle": 0, "near_cycle": 2, "far_cycle": 4}
        for case, residual in expected.items():
            relations, complete = CASES[case]
            for tolerance in TOLERANCES:
                result = evaluate({"relations": relations, "complete": complete,
                                   "tolerance_ticks": tolerance, "contract": CONTRACTS[0],
                                   "action": "reversible"})
                self.assertEqual(result["minimax_residual_ticks"], residual)
                self.assertEqual(result["observed_subgraph_minimax_residual_ticks"], residual)
                self.assertEqual(result["residual_scope"], "full_cover")
        near, complete = CASES["near_cycle"]
        self.assertFalse(evaluate({"relations": near, "complete": complete, "tolerance_ticks": 1,
                                   "contract": CONTRACTS[2], "action": "irreversible"})["admitted"])
        self.assertTrue(evaluate({"relations": near, "complete": complete, "tolerance_ticks": 2,
                                  "contract": CONTRACTS[1], "action": "compensable"})["admitted"])
        self.assertFalse(evaluate({"relations": near, "complete": complete, "tolerance_ticks": 2,
                                   "contract": CONTRACTS[1], "action": "irreversible"})["admitted"])
        self.assertTrue(evaluate({"relations": near, "complete": complete, "tolerance_ticks": 2,
                                  "contract": CONTRACTS[2], "action": "irreversible"})["admitted"])

    def test_144_rows_match_independent_oracle_and_strict_schema(self):
        rows = build_rows()
        self.assertEqual(len(rows), len(CASES) * len(TOLERANCES) * len(CONTRACTS) * len(ACTIONS))
        self.assertEqual(len(rows), 144)
        self.assertEqual(check(rows), [])
        for row in rows:
            self.assertTrue(valid_input(row["decision_input"]))
            self.assertTrue(valid_output(row["decision_output"],
                                         len(row["decision_input"]["relations"])))
            self.assertEqual(row["decision_output"], reference(row["decision_input"]))

    def test_all_15_mutations_are_nonidentity_and_rejected(self):
        rows = build_rows()
        controls = mutation_manifest(rows)
        self.assertEqual(len(controls), 15)
        for name, *rest in controls:
            with self.subTest(mutation=name):
                changed = mutate(rows, name, (name, *rest))
                before = json.dumps(rows, sort_keys=True, separators=(",", ":"), allow_nan=False)
                after = json.dumps(changed, sort_keys=True, separators=(",", ":"), allow_nan=False)
                self.assertNotEqual(after, before)
                self.assertTrue(check(changed))

    def test_strict_validator_rejects_bool_as_integer(self):
        row = build_rows()[0]
        source = row["decision_input"].copy()
        source["tolerance_ticks"] = False
        self.assertFalse(valid_input(source))
        output = row["decision_output"].copy()
        output["admitted"] = 0
        self.assertFalse(valid_output(output, len(row["decision_input"]["relations"])))


if __name__ == "__main__":
    unittest.main()
