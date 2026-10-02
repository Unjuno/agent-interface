import copy
import json
import tempfile
import unittest
from pathlib import Path
from fractions import Fraction
from functools import lru_cache

import audit
import simulate


class BeliefSchedulingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "raw.jsonl"
            simulate.main(str(path))
            cls.rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        cls.independent_audit = audit.result(cls.rows)

    @staticmethod
    @lru_cache(maxsize=None)
    def audit_json(raw_json):
        return audit.result(json.loads(raw_json))

    def test_independent_raw_audit_passes(self):
        self.assertEqual(self.independent_audit["disposition"], "PASS_METHOD_SCOPED")

    def test_heldout_belief_selector_beats_three_baselines_with_caps(self):
        case = next(r for r in self.rows if r["case_id"] == "independent_heldout")
        policies = {p["declared_policy"]: p for p in case["policies"]}
        selected = policies["belief_value"]
        for baseline in ("cyclic", "aoi", "entropy"):
            self.assertLess(Fraction(selected["expected_weighted_misses"]), Fraction(policies[baseline]["expected_weighted_misses"]))
        self.assertLessEqual(selected["max_starvation"], 3)
        self.assertLessEqual(Fraction(selected["expected_false_confidence"]), Fraction(3, 2))

    def test_age_is_not_monotonic_uncertainty_rank(self):
        control = self.rows[0]["analytic_entropy_control"]
        self.assertEqual(control["beliefs"], ["9/10", "63/100", "711/1000"])
        self.assertTrue(control["age2_gt_age3"])

    def test_unsupported_controls_fall_back_identically_to_cyclic(self):
        for case_id in ("coupled_common_cause", "mode_switch", "unknown_transition"):
            policies = {p["declared_policy"]: p for p in next(r for r in self.rows if r["case_id"] == case_id)["policies"]}
            self.assertEqual({k: v for k, v in policies["belief_value"].items() if k != "declared_policy"}, {k: v for k, v in policies["cyclic"].items() if k != "declared_policy"})
            self.assertFalse(policies["belief_value"]["index_claim"])

    def test_auditor_rejects_omitted_world_case(self):
        mutated = copy.deepcopy(self.rows[:-1])
        self.assertTrue(self.audit_json(json.dumps(mutated, sort_keys=True))["errors"])

    def test_auditor_rejects_metric_mutation(self):
        mutated = copy.deepcopy(self.rows)
        row = next(r for r in mutated if r["case_id"] == "independent_heldout")
        next(p for p in row["policies"] if p["declared_policy"] == "belief_value")["expected_weighted_misses"] = "0"
        self.assertTrue(self.audit_json(json.dumps(mutated, sort_keys=True))["errors"])

    def test_auditor_rejects_truth_leak_and_opportunity_label_change(self):
        for field, value in (("oracle_truth_scope", "candidate_visible"), ("opportunity_definition", "delivered_frame_only")):
            mutated = copy.deepcopy(self.rows)
            mutated[0][field] = value
            self.assertTrue(self.audit_json(json.dumps(mutated, sort_keys=True))["errors"])

    def test_auditor_rejects_unsupported_index_claim(self):
        mutated = copy.deepcopy(self.rows)
        control = next(r for r in mutated if r["case_id"] == "coupled_common_cause")
        next(p for p in control["policies"] if p["declared_policy"] == "belief_value")["index_claim"] = True
        self.assertTrue(self.audit_json(json.dumps(mutated, sort_keys=True))["errors"])


if __name__ == "__main__":
    unittest.main()
