"""Pre-freeze construction checks; these are not formal role invocations."""
import json
import pathlib
import unittest

import auditor
import candidate

ROOT = pathlib.Path(__file__).parent
PUBLIC = json.loads((ROOT / "public_cases.json").read_text(encoding="utf-8"))
ORACLE = json.loads((ROOT / "oracle_cases.json").read_text(encoding="utf-8"))


class ConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = candidate.run(PUBLIC)

    def test_expected_minimum_bounds(self):
        cases = self.raw["cases"]
        self.assertEqual(cases["safe_wait_cycle"]["bound"], 1)
        self.assertEqual(cases["bounded_async"]["bound"], 3)
        self.assertEqual(cases["unsafe_control_alternative"]["bound"], 1)

    def test_wait_is_removed_from_bounded_policy(self):
        layer = self.raw["cases"]["safe_wait_cycle"]["policy_layers"][0]
        self.assertEqual(layer["allowed_edges"]["s"], ["progress_s_g"])

    def test_uncontrollable_cycle_yields_without_completion(self):
        row = self.raw["cases"]["uncontrollable_cycle"]
        self.assertEqual(row["status"], "SAFE_YIELD")
        self.assertIs(row["completion_claim"], False)
        self.assertEqual(row["app_actions"], [])

    def test_absent_marker_evidence_yields(self):
        row = self.raw["cases"]["missing_marker_evidence"]
        self.assertEqual(row["status"], "SAFE_YIELD")
        self.assertIsNone(row["bound"])

    def test_contract_conflict_is_left_for_hidden_oracle(self):
        row = self.raw["cases"]["contract_disagreement"]
        self.assertEqual(row["status"], "POLICY_PROPOSED")
        self.assertIs(row["completion_claim"], False)

    def test_independent_graph_audit_and_mutations(self):
        result = auditor.full_audit(PUBLIC, ORACLE, self.raw)
        self.assertEqual(result["disposition"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["errors"], [])
        self.assertTrue(all(auditor.mutations_rejected(PUBLIC, ORACLE, self.raw).values()))

    def test_forbidden_action_is_not_selected(self):
        layer = self.raw["cases"]["unsafe_control_alternative"]["policy_layers"][0]
        self.assertEqual(layer["allowed_edges"]["p"], ["safe_finish"])


if __name__ == "__main__":
    unittest.main()
