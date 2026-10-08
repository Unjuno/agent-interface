"""Construction tests for the raw-only, independent truth auditor."""

import importlib.util
import copy
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).with_name("auditor.py")


def load_auditor():
    if not MODULE_PATH.is_file():
        return None
    spec = importlib.util.spec_from_file_location("auditor_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AuditorTruthReconstructionTests(unittest.TestCase):
    def test_auditor_rejects_candidate_that_omits_categorical_failure_control(self):
        auditor = load_auditor()
        builder_spec = importlib.util.spec_from_file_location("fixture_builder_missing_control", MODULE_PATH.with_name("build_fixture.py"))
        builder = importlib.util.module_from_spec(builder_spec)
        builder_spec.loader.exec_module(builder)
        candidate_spec = importlib.util.spec_from_file_location("candidate_missing_control", MODULE_PATH.with_name("candidate.py"))
        candidate = importlib.util.module_from_spec(candidate_spec)
        candidate_spec.loader.exec_module(candidate)
        public, truth = builder.build_fixture(repetitions=1)
        public["categorical_controls"].append({"control_id": "hard-safety-mutated", "kind": "hard_safety", "state": "PASS"})
        truth["categorical_controls"].append({"control_id": "hard-safety-mutated", "kind": "hard_safety", "state": "PASS"})
        raw = candidate.run(public)
        raw["input_sha256"] = "9" * 64
        raw["categorical_controls"] = []
        result = auditor.audit(public, truth, raw, "9" * 64)
        self.assertEqual(result["status"], "HOLD_AUDIT")
        self.assertTrue(any("categorical_control" in error for error in result["errors"]))

    def test_auditor_requires_the_frozen_hard_safety_and_missing_truth_classes(self):
        auditor = load_auditor()
        builder_spec = importlib.util.spec_from_file_location("fixture_builder_required_controls", MODULE_PATH.with_name("build_fixture.py"))
        builder = importlib.util.module_from_spec(builder_spec)
        builder_spec.loader.exec_module(builder)
        candidate_spec = importlib.util.spec_from_file_location("candidate_required_controls", MODULE_PATH.with_name("candidate.py"))
        candidate = importlib.util.module_from_spec(candidate_spec)
        candidate_spec.loader.exec_module(candidate)
        public, truth = builder.build_fixture(repetitions=1)
        public["categorical_controls"] = []
        truth["categorical_controls"] = []
        raw = candidate.run(public)
        raw["input_sha256"] = "8" * 64
        result = auditor.audit(public, truth, raw, "8" * 64)
        self.assertEqual(result["status"], "HOLD_AUDIT")
        self.assertTrue(any("required_categorical_control_missing" in error for error in result["errors"]))

    def test_independent_auditor_reconstructs_candidate_summary_from_public_records(self):
        auditor = load_auditor()
        self.assertIsNotNone(auditor, "independent auditor is not implemented yet")
        builder_spec = importlib.util.spec_from_file_location("fixture_builder_for_audit", MODULE_PATH.with_name("build_fixture.py"))
        builder = importlib.util.module_from_spec(builder_spec)
        builder_spec.loader.exec_module(builder)
        candidate_spec = importlib.util.spec_from_file_location("candidate_for_audit_test", MODULE_PATH.with_name("candidate.py"))
        candidate = importlib.util.module_from_spec(candidate_spec)
        candidate_spec.loader.exec_module(candidate)
        public, truth = builder.build_fixture(repetitions=2)
        raw = candidate.run(public)
        raw["input_sha256"] = "a" * 64
        result = auditor.audit(public, truth, raw, "a" * 64)
        self.assertEqual(result["status"], "FAIL_METHOD", result["errors"])
        self.assertEqual(result["audit_integrity"], "PASS")
        self.assertEqual(result["truth_cohorts_reconstructed"], 12)
        self.assertEqual(result["partial_tail_false_unique_n"], 0)

    def test_auditor_rejects_hash_mismatch(self):
        auditor = load_auditor()
        builder_spec = importlib.util.spec_from_file_location("fixture_builder_hash", MODULE_PATH.with_name("build_fixture.py"))
        builder = importlib.util.module_from_spec(builder_spec)
        builder_spec.loader.exec_module(builder)
        candidate_spec = importlib.util.spec_from_file_location("candidate_hash", MODULE_PATH.with_name("candidate.py"))
        candidate = importlib.util.module_from_spec(candidate_spec)
        candidate_spec.loader.exec_module(candidate)
        public, truth = builder.build_fixture(repetitions=1)
        raw = candidate.run(public)
        raw["input_sha256"] = "e" * 64
        result = auditor.audit(public, truth, raw, "f" * 64)
        self.assertEqual(result["status"], "HOLD_AUDIT")
        self.assertIn("candidate_input_sha_mismatch", result["errors"])

    def test_preregistered_full_fixture_decision_criteria(self):
        auditor = load_auditor()
        builder_spec = importlib.util.spec_from_file_location("fixture_builder_full_criteria", MODULE_PATH.with_name("build_fixture.py"))
        builder = importlib.util.module_from_spec(builder_spec)
        builder_spec.loader.exec_module(builder)
        candidate_spec = importlib.util.spec_from_file_location("candidate_full_criteria", MODULE_PATH.with_name("candidate.py"))
        candidate = importlib.util.module_from_spec(candidate_spec)
        candidate_spec.loader.exec_module(candidate)
        public, truth = builder.build_fixture(repetitions=128)
        raw = candidate.run(public)
        raw["input_sha256"] = "d" * 64
        result = auditor.audit(public, truth, raw, "d" * 64)
        self.assertEqual(result["status"], "FAIL_METHOD", result["errors"][:10])
        self.assertEqual(result["audit_integrity"], "PASS")
        self.assertFalse(result["decision_checks"]["recorded_covariate_ipcw_accuracy_at_least_80pct"])
        self.assertFalse(result["decision_checks"]["recorded_covariate_ipcw_strictly_beats_resolved_only"])
        self.assertEqual(result["truth_cohorts_reconstructed"], 768)
        self.assertEqual(result["partial_tail_contains_truth_n"], 768)
        self.assertEqual(result["partial_tail_false_unique_n"], 0)
        self.assertEqual(result["positivity_unsupported_tail_n"], 256)
        self.assertEqual(result["recorded_covariate_ipcw_correct_n"], 10)
        self.assertEqual(result["recorded_covariate_resolved_correct_n"], 20)
        self.assertEqual(result["latent_resolved_misrank_n"], 26)
        self.assertEqual(result["latent_partial_unknown_n"], 128)

    def test_auditor_rejects_numeric_candidate_output_mutation(self):
        auditor = load_auditor()
        builder_spec = importlib.util.spec_from_file_location("fixture_builder_for_mutation", MODULE_PATH.with_name("build_fixture.py"))
        builder = importlib.util.module_from_spec(builder_spec)
        builder_spec.loader.exec_module(builder)
        candidate_spec = importlib.util.spec_from_file_location("candidate_for_mutation", MODULE_PATH.with_name("candidate.py"))
        candidate = importlib.util.module_from_spec(candidate_spec)
        candidate_spec.loader.exec_module(candidate)
        public, truth = builder.build_fixture(repetitions=1)
        raw = candidate.run(public)
        raw["input_sha256"] = "b" * 64
        tampered = copy.deepcopy(raw)
        tampered["cohort_results"][0]["routes"]["A"]["macro_cvar_lower"] += 1
        result = auditor.audit(public, truth, tampered, "b" * 64)
        self.assertEqual(result["status"], "HOLD_AUDIT")
        self.assertTrue(any("candidate_value_mismatch" in error for error in result["errors"]))

    def test_auditor_rejects_omitted_categorical_control(self):
        auditor = load_auditor()
        builder_spec = importlib.util.spec_from_file_location("fixture_builder_for_control", MODULE_PATH.with_name("build_fixture.py"))
        builder = importlib.util.module_from_spec(builder_spec)
        builder_spec.loader.exec_module(builder)
        candidate_spec = importlib.util.spec_from_file_location("candidate_for_control", MODULE_PATH.with_name("candidate.py"))
        candidate = importlib.util.module_from_spec(candidate_spec)
        candidate_spec.loader.exec_module(candidate)
        public, truth = builder.build_fixture(repetitions=1)
        raw = candidate.run(public)
        raw["input_sha256"] = "c" * 64
        raw["categorical_controls"].pop()
        result = auditor.audit(public, truth, raw, "c" * 64)
        self.assertEqual(result["status"], "HOLD_AUDIT")
        self.assertTrue(any("categorical_control_denominator" in error for error in result["errors"]))

    def test_auditor_reconstructs_a_censored_prefix_without_using_candidate_code(self):
        auditor = load_auditor()
        self.assertIsNotNone(auditor, "independent auditor is not implemented yet")
        public = {
            "schema": "8598-observed-v1",
            "settings": {"horizon": 4, "max_regret_per_tick": 3, "cvar_alpha": 0.75, "minimum_completion_propensity": 0.05},
            "cohorts": [
                {"seed": 1, "arm": "independent_admin", "opportunities": [
                    {"opportunity_id": "a", "route": "A", "stratum": "s0", "resolved": False, "followup_ticks": 2, "observed_increments": [0, 2], "p_resolve_model": 0.7}
                ]}
            ],
            "categorical_controls": [
                {"control_id": "safety", "kind": "hard_safety", "state": "FAIL_HARD_SAFETY"},
                {"control_id": "unknown", "kind": "missing_truth", "state": "UNKNOWN"},
            ],
        }
        truth = {
            "schema": "8598-truth-v1",
            "opportunities": [
                {"opportunity_id": "a", "seed": 1, "arm": "independent_admin", "route": "A", "stratum": "s0", "increments": [0, 2, 1, 0]}
            ],
            "categorical_controls": [
                {"control_id": "safety", "kind": "hard_safety", "state": "FAIL_HARD_SAFETY"},
                {"control_id": "unknown", "kind": "missing_truth", "state": "UNKNOWN"},
            ],
        }
        self.assertEqual(auditor.audit_inputs(public, truth), [])

    def test_auditor_rejects_a_prefix_that_disagrees_with_frozen_truth(self):
        auditor = load_auditor()
        self.assertIsNotNone(auditor, "independent auditor is not implemented yet")
        public = {
            "schema": "8598-observed-v1",
            "settings": {"horizon": 4, "max_regret_per_tick": 3, "cvar_alpha": 0.75, "minimum_completion_propensity": 0.05},
            "cohorts": [
                {"seed": 1, "arm": "independent_admin", "opportunities": [
                    {"opportunity_id": "a", "route": "A", "stratum": "s0", "resolved": False, "followup_ticks": 2, "observed_increments": [3, 3], "p_resolve_model": 0.7}
                ]}
            ],
            "categorical_controls": [],
        }
        truth = {
            "schema": "8598-truth-v1",
            "opportunities": [
                {"opportunity_id": "a", "seed": 1, "arm": "independent_admin", "route": "A", "stratum": "s0", "increments": [0, 2, 1, 0]}
            ],
            "categorical_controls": [],
        }
        self.assertTrue(auditor.audit_inputs(public, truth))

    def test_auditor_rejects_candidate_output_that_omits_an_assigned_cohort(self):
        auditor = load_auditor()
        self.assertIsNotNone(auditor, "independent auditor is not implemented yet")
        public = {
            "schema": "8598-observed-v1",
            "settings": {"horizon": 1, "max_regret_per_tick": 1, "cvar_alpha": 0.5, "minimum_completion_propensity": 0.05},
            "cohorts": [{"seed": 1, "arm": "no_censor", "opportunities": [
                {"opportunity_id": "a", "route": "A", "stratum": "s0", "resolved": True, "followup_ticks": 1, "observed_increments": [1], "terminal_loss": 1, "p_resolve_model": 1.0}
            ]}],
            "categorical_controls": [],
        }
        truth = {
            "schema": "8598-truth-v1",
            "opportunities": [{"opportunity_id": "a", "seed": 1, "arm": "no_censor", "route": "A", "stratum": "s0", "increments": [1]}],
            "categorical_controls": [],
        }
        raw = {"schema": "8598-candidate-v1", "input_schema": public["schema"], "input_sha256": "a" * 64, "cohort_results": []}
        result = auditor.audit(public, truth, raw, "a" * 64)
        self.assertEqual(result["status"], "HOLD_AUDIT")
        self.assertIn("candidate_cohort_denominator_mismatch", result["errors"])


if __name__ == "__main__":
    unittest.main()
