"""Mutation tests for the independent raw-only audit boundary."""
import copy
import json
import unittest
from pathlib import Path

import oracle
from experiment import POLICIES, execute_proposals
from run_formal import materialize
from audit import audit_document


HERE = Path(__file__).resolve().parent
WORKLOAD = json.loads((HERE / "workload.json").read_text(encoding="utf-8"))


def valid_raw():
    cases = []
    for case in WORKLOAD["cases"]:
        proposals = materialize(WORKLOAD, case)
        cases.append({
            "case_id": case["case_id"],
            "proposals": proposals,
            "expected": case["expected"],
            "observed": {policy: execute_proposals(proposals, policy) for policy in POLICIES},
        })
    return {
        "schema": "action-effect-coalescing-raw-v1",
        "issue": 5265,
        "allocation": "synthetic-test-only",
        "base_sha": "0" * 40,
        "workload_sha256": "test-fixture",
        "source_sha256": {},
        "policies": list(POLICIES),
        "case_count": len(cases),
        "cases": cases,
        "resource_scope": {"runtime": "host-cpython", "network": "none-required",
                           "model": False, "gui_or_input": False,
                           "authority_or_effect_claim": False},
    }


class IndependentAuditTests(unittest.TestCase):
    def test_independent_oracle_accepts_candidate_matrix_and_reconstructs_all_rows(self):
        raw = valid_raw()
        report = audit_document(raw, WORKLOAD)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["case_count"], 10)
        self.assertEqual(report["equivalent_duplicate_effects_control"], 2)
        self.assertEqual(report["equivalent_duplicate_effects_coalesced"], 1)

    def test_rejects_reordered_cases(self):
        raw = valid_raw()
        raw["cases"].reverse()
        self.assertTrue(audit_document(raw, WORKLOAD)["errors"])

    def test_rejects_observed_effect_count_mutation(self):
        raw = valid_raw()
        raw["cases"][0]["observed"]["SEMANTIC_EFFECT_COALESCING"]["effects"] = 2
        self.assertTrue(audit_document(raw, WORKLOAD)["errors"])

    def test_rejects_target_incarnation_mutation_even_when_both_consumers_agree(self):
        raw = valid_raw()
        raw["cases"][0]["proposals"][1]["target_incarnation"] = "window-4/widget-8"
        self.assertTrue(audit_document(raw, WORKLOAD)["errors"])

    def test_rejects_changed_preregistered_expected_values(self):
        raw = valid_raw()
        raw["cases"][0]["expected"]["SEMANTIC_EFFECT_COALESCING"]["effects"] = 2
        self.assertTrue(audit_document(raw, WORKLOAD)["errors"])

    def test_rejects_authority_or_effect_truth_claim(self):
        raw = valid_raw()
        raw["resource_scope"]["authority_or_effect_claim"] = True
        self.assertTrue(audit_document(raw, WORKLOAD)["errors"])

    def test_rejects_unexpected_or_duplicate_case(self):
        raw = valid_raw()
        raw["cases"].append(copy.deepcopy(raw["cases"][0]))
        self.assertTrue(audit_document(raw, WORKLOAD)["errors"])


if __name__ == "__main__":
    unittest.main()
