"""Construction checks for Issue #57's paired all-attempt ledger."""
import importlib.util
import json
import pathlib
import copy
import unittest


ROOT = pathlib.Path(__file__).parent
spec = importlib.util.spec_from_file_location("candidate", ROOT / "candidate.py")
candidate = importlib.util.module_from_spec(spec) if spec and (ROOT / "candidate.py").is_file() else None
if candidate is not None:
    spec.loader.exec_module(candidate)
audit_spec = importlib.util.spec_from_file_location("audit", ROOT / "audit.py")
auditor = importlib.util.module_from_spec(audit_spec) if audit_spec else None
if auditor is not None:
    audit_spec.loader.exec_module(auditor)
FIXTURE = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))


class PairedRouteLedgerTests(unittest.TestCase):
    def test_true_null_is_zero_pair_difference(self):
        self.assertIsNotNone(candidate, "candidate analyzer is not implemented")
        result = candidate.analyze(FIXTURE)
        row = result["scenarios"]["true_null"]["paired"]["summary"]
        self.assertEqual(row["assigned_pairs"], 2)
        self.assertEqual(row["complete_pairs_tokens"], 2)
        self.assertEqual(row["mean_delta_tokens_integrated_minus_baseline"], 0)
        self.assertEqual(row["mean_delta_elapsed_ms_integrated_minus_baseline"], 0)

    def test_planted_route_benefit_uses_same_pair_ids(self):
        result = candidate.analyze(FIXTURE)
        scenario = result["scenarios"]["planted_benefit"]
        self.assertEqual(scenario["paired"]["summary"]["assigned_pairs"], 2)
        self.assertEqual(scenario["paired"]["summary"]["mean_delta_tokens_integrated_minus_baseline"], -20)
        self.assertEqual(scenario["paired"]["summary"]["mean_delta_elapsed_ms_integrated_minus_baseline"], -200)
        self.assertEqual({p["pair_id"] for p in scenario["paired"]["rows"]}, {"benefit-1", "benefit-2"})

    def test_failed_and_unknown_attempts_stay_in_denominator(self):
        result = candidate.analyze(FIXTURE)["scenarios"]["route_dependent_failure"]
        self.assertEqual(result["assigned_attempts"], 6)
        self.assertEqual(result["assigned_pairs"], 3)
        self.assertEqual(result["paired"]["summary"]["complete_pairs_tokens"], 1)
        self.assertEqual(len(result["paired"]["rows"]), 3)
        self.assertEqual(result["arms"]["integrated"]["attempt_count"], 3)
        self.assertEqual(result["arms"]["integrated"]["outcomes"], ["FAIL", "COMPLETE", "COMPLETE"])
        self.assertFalse(result["safety_gate"]["pass"])

    def test_no_pair_is_dropped_when_one_arm_lacks_endpoint(self):
        result = candidate.analyze(FIXTURE)["scenarios"]["route_dependent_failure"]["paired"]
        failed = next(row for row in result["rows"] if row["pair_id"] == "failure-1")
        unknown = next(row for row in result["rows"] if row["pair_id"] == "failure-2")
        self.assertIsNone(failed["delta_tokens_integrated_minus_baseline"])
        self.assertIsNone(unknown["delta_tokens_integrated_minus_baseline"])

    def test_post_treatment_repair_count_cannot_be_adjustment_covariate(self):
        with self.assertRaisesRegex(ValueError, "pre-treatment"):
            candidate.analyze(FIXTURE, adjustment_covariate="repair_count")

    def test_independent_auditor_reconstructs_complete_ledger(self):
        raw = candidate.analyze(FIXTURE)
        result = auditor.audit(FIXTURE, raw)
        self.assertEqual(result["status"], "METHOD_PASS_SCOPED")
        self.assertEqual(result["attempts_retained"], 14)

    def test_mutation_dropping_failed_pair_is_rejected(self):
        raw = candidate.analyze(FIXTURE)
        raw["scenarios"]["route_dependent_failure"]["paired"]["rows"].pop(0)
        with self.assertRaises(AssertionError):
            auditor.audit(FIXTURE, raw)

    def test_mutation_cross_pair_success_matching_is_rejected(self):
        raw = candidate.analyze(FIXTURE)
        rows = raw["scenarios"]["planted_benefit"]["paired"]["rows"]
        rows[0]["baseline_attempt_id"], rows[1]["baseline_attempt_id"] = rows[1]["baseline_attempt_id"], rows[0]["baseline_attempt_id"]
        with self.assertRaises(AssertionError):
            auditor.audit(FIXTURE, raw)

    def test_mutation_adjusting_for_post_treatment_repair_is_rejected(self):
        raw = candidate.analyze(FIXTURE)
        raw["adjustment"] = {"covariate": "repair_count", "status": "APPLIED"}
        with self.assertRaises(AssertionError):
            auditor.audit(FIXTURE, raw)

    def test_mutation_labeling_repair_count_as_pre_treatment_is_rejected(self):
        ledger = copy.deepcopy(FIXTURE)
        ledger["pairs"][0]["pre_treatment"]["repair_count"] = 1
        with self.assertRaisesRegex(ValueError, "post-treatment"):
            candidate.analyze(ledger)

    def test_mutation_reusing_reset_copy_across_arms_is_rejected(self):
        ledger = copy.deepcopy(FIXTURE)
        ledger["pairs"][0]["attempts"][1]["reset_id"] = ledger["pairs"][0]["attempts"][0]["reset_id"]
        with self.assertRaisesRegex(ValueError, "independent reset"):
            candidate.analyze(ledger)

    def test_mutation_retroactive_covariate_capture_is_rejected(self):
        ledger = copy.deepcopy(FIXTURE)
        ledger["pairs"][0]["pre_treatment"]["captured_at"] = 25
        with self.assertRaisesRegex(ValueError, "precede assignment"):
            candidate.analyze(ledger)

    def test_independent_auditor_rejects_reused_reset_copy(self):
        ledger = copy.deepcopy(FIXTURE)
        ledger["pairs"][0]["attempts"][1]["reset_id"] = ledger["pairs"][0]["attempts"][0]["reset_id"]
        with self.assertRaises(AssertionError):
            auditor.audit(ledger, candidate.analyze(FIXTURE))

    def test_independent_auditor_rejects_retroactive_covariate_capture(self):
        ledger = copy.deepcopy(FIXTURE)
        ledger["pairs"][0]["pre_treatment"]["captured_at"] = 25
        with self.assertRaises(AssertionError):
            auditor.audit(ledger, candidate.analyze(FIXTURE))

    def test_mutation_corrupting_unpaired_sensitivity_is_rejected(self):
        raw = candidate.analyze(FIXTURE)
        raw["scenarios"]["planted_benefit"]["unpaired_sensitivity"]["tokens"]["mean_delta_integrated_minus_baseline"] = 0
        with self.assertRaises(AssertionError):
            auditor.audit(FIXTURE, raw)


if __name__ == "__main__":
    unittest.main()
