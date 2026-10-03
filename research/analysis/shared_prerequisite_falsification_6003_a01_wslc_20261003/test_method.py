"""Construction tests for the frozen #6003 A01 method and independent oracle."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import unittest

import audit
import candidate


ROOT = Path(__file__).resolve().parent
FIXTURE = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
FREEZE = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))


class SharedPrerequisiteTests(unittest.TestCase):
    def test_expected_four_selector_disagreement(self):
        result = candidate.compute_core(FIXTURE)
        self.assertEqual(result["selectors"]["cheapest_first"], "E-cheapest-inert")
        self.assertEqual(result["selectors"]["raw_node_degree"], "E-degree-decoy")
        self.assertEqual(result["selectors"]["legacy_robust_reversal"], "E-verify-unique")
        self.assertEqual(result["selectors"]["graph_aware"], "E-shared-prerequisite")

    def test_shared_failure_changes_two_top_decisions(self):
        result = candidate.compute_core(FIXTURE)
        row = result["graph_audit"]["trial_details"]["E-shared-prerequisite"]
        self.assertEqual(row["eligible_before"], ["CAPTURE", "VERIFY"])
        self.assertEqual(row["outcomes"]["FAIL"]["eligible_after"], [])
        self.assertEqual(row["outcomes"]["FAIL"]["changed_top_claims"], ["CAPTURE", "VERIFY"])
        self.assertEqual(row["outcomes"]["STOP"]["eligible_after"], ["CAPTURE", "VERIFY"])

    def test_unique_premise_changes_one_decision(self):
        result = candidate.compute_core(FIXTURE)
        row = result["graph_audit"]["trial_details"]["E-verify-unique"]
        self.assertEqual(row["outcomes"]["FAIL"]["eligible_after"], ["CAPTURE"])
        self.assertEqual(row["max_changed_top_claims"], 1)

    def test_correlated_source_members_change_together(self):
        graph = FIXTURE["graph"]
        experiment = next(x for x in FIXTURE["experiments"] if x["id"] == "E-capture-correlated-source")
        initial = {name: value["truth"] for name, value in graph["premises"].items()}
        updated = candidate.apply_test(graph, experiment, initial, "FAIL")
        self.assertFalse(updated["P_CAPTURE_B"])
        self.assertFalse(updated["P_CAPTURE_B_DUP"])
        self.assertTrue(updated["P_CAPTURE_A"])
        self.assertTrue(updated["P_CAPTURE_C"])

    def test_redundant_alternative_support_prevents_false_leverage(self):
        result = candidate.compute_core(FIXTURE)
        self.assertEqual(
            result["score_tables"]["graph_max_changed_top_claims"]["E-capture-correlated-source"], 0
        )

    def test_unvalidated_edge_is_reported_and_not_top_leverage(self):
        result = candidate.compute_core(FIXTURE)
        self.assertEqual(result["graph_audit"]["unvalidated_edges_ignored"], ["e-false-verify"])
        self.assertEqual(result["score_tables"]["graph_max_changed_top_claims"]["E-unvalidated-edge"], 0)

    def test_high_degree_only_wins_naive_comparator(self):
        result = candidate.compute_core(FIXTURE)
        scores = result["score_tables"]
        self.assertEqual(scores["raw_declared_outdegree"]["E-degree-decoy"], 12)
        self.assertEqual(scores["graph_max_changed_top_claims"]["E-degree-decoy"], 0)

    def test_null_and_unknown_coverage_abstain(self):
        result = candidate.compute_core(FIXTURE)
        self.assertEqual(result["controls"]["null_graph_aware"], "UNRANKABLE")
        self.assertEqual(result["controls"]["null_max_changed_top_claims"], 0)
        unknown = copy.deepcopy(FIXTURE)
        unknown["graph"]["coverage_complete"] = False
        unknown_result = candidate.compute_core(unknown)
        self.assertEqual(unknown_result["selectors"]["graph_aware"], "UNRANKABLE")
        self.assertEqual(unknown_result["controls"]["unknown_coverage_graph_aware"], "UNRANKABLE")
        self.assertEqual(audit.oracle_core(unknown), unknown_result)

    def test_disjoint_portfolio_has_no_two_claim_shared_effect(self):
        controls = candidate.compute_core(FIXTURE)["controls"]
        self.assertEqual(controls["disjoint_graph_aware"], "E-verify-unique")
        self.assertEqual(controls["disjoint_max_changed_top_claims"], 1)
        shared = controls["disjoint_trial_details"]["E-shared-prerequisite"]
        self.assertEqual(shared["outcomes"]["FAIL"]["eligible_after"], ["VERIFY"])
        self.assertEqual(shared["outcomes"]["FAIL"]["changed_top_claims"], ["CAPTURE"])

    def test_sentinel_cost_is_reserved_for_all_feasible_tests(self):
        result = candidate.compute_core(FIXTURE)
        self.assertTrue(result["sentinel"]["mandatory"])
        self.assertTrue(result["sentinel"]["all_feasible_tests_retain_sentinel"])
        self.assertEqual(result["sentinel"]["experiment_cost_cap"], 3)

    def test_auditor_input_and_output_mounts_are_separate(self):
        command = FREEZE["commands"]["auditor"]
        mounts = [command[i + 1] for i, value in enumerate(command) if value == "--volume"]
        self.assertIn(FREEZE["host_paths"]["package"] + ":/src:ro", mounts)
        self.assertIn(FREEZE["host_paths"]["candidate"] + ":/input:ro", mounts)
        self.assertIn(FREEZE["host_paths"]["auditor"] + ":/out", mounts)
        self.assertNotIn(FREEZE["host_paths"]["auditor"] + ":/out:ro", mounts)
        self.assertEqual(command[command.index("--candidate-result") + 1], "/input/candidate_result.json")
        self.assertEqual(command[command.index("--output") + 1], "/out/independent_audit.json")

    def test_independent_oracle_agrees_on_constructed_core(self):
        core = candidate.compute_core(FIXTURE)
        self.assertEqual(core, audit.oracle_core(FIXTURE))

    def test_independent_oracle_rejects_effective_corruptions(self):
        core = candidate.compute_core(FIXTURE)
        result = {
            "allocation_id": FREEZE["allocation_id"],
            "issue": FREEZE["issue"],
            "main_sha": FREEZE["base_main_sha"],
            "freeze_sha256": "f" * 64,
            "fixture_sha256": hashlib.sha256((ROOT / "fixture.json").read_bytes()).hexdigest(),
            "candidate_sha256": hashlib.sha256((ROOT / "candidate.py").read_bytes()).hexdigest(),
            "status": "SYNTHETIC_METHOD_CONSTRUCTION_ONLY",
            "scientific_support_events": 0,
            **core,
        }
        controls = audit.corruption_controls(
            FIXTURE, result, "f" * 64, result["fixture_sha256"], result["candidate_sha256"], FREEZE
        )
        self.assertEqual(len(controls), 8)
        self.assertTrue(all(item["rejected"] for item in controls))


if __name__ == "__main__":
    unittest.main(verbosity=2)
