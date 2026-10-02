"""Synthetic controls for separating finite allocation from generalization."""
import copy
import importlib.util
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).parent
def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    if not (ROOT / f"{name}.py").is_file():
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


candidate = load("candidate")
auditor = load("audit")
FIXTURE = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))


class DecisionScopeTests(unittest.TestCase):
    def test_historical_retain_is_immutable_but_claim_is_not_generalized(self):
        self.assertIsNotNone(candidate, "prospective decision-scope evaluator is not implemented")
        result = candidate.evaluate(FIXTURE)
        self.assertEqual(result["historical_allocation"]["disposition"], "RETAIN")
        self.assertTrue(result["historical_allocation"]["unchanged"])
        self.assertEqual(result["generalization_scope"], "HOLD_NOT_ESTABLISHED")

    def test_single_finite_sequence_can_retain_only_its_declared_schedule(self):
        result = candidate.evaluate(FIXTURE)
        case = result["prospective_cases"]["prospective_finite_pass_one_sequence"]
        self.assertEqual(case["finite_allocation_disposition"], "RETAIN")
        self.assertEqual(case["claim_scope"], "FINITE_SCHEDULE_ONLY")
        self.assertEqual(result["generalization_scope"], "HOLD_NOT_ESTABLISHED")

    def test_missing_accounting_or_invalidating_discovery_holds_finite_rule(self):
        cases = candidate.evaluate(FIXTURE)["prospective_cases"]
        self.assertEqual(cases["prospective_incomplete_accounting"]["finite_allocation_disposition"], "HOLD")
        self.assertEqual(cases["prospective_invalidating_discovery"]["finite_allocation_disposition"], "HOLD")

    def test_correctness_or_frozen_threshold_failure_rejects_finite_candidate(self):
        cases = candidate.evaluate(FIXTURE)["prospective_cases"]
        self.assertEqual(cases["prospective_correctness_failure"]["finite_allocation_disposition"], "REJECT")
        self.assertEqual(cases["prospective_frozen_threshold_failure"]["finite_allocation_disposition"], "REJECT")

    def test_independent_auditor_accepts_separated_axes(self):
        result = auditor.audit(FIXTURE, candidate.evaluate(FIXTURE))
        self.assertEqual(result["status"], "METHOD_PASS_SCOPED")
        self.assertEqual(result["cases_reconstructed"], 5)
        self.assertEqual(result["mutation_controls"], 8)

    def test_mutation_retroactively_relabels_historical_retain_is_rejected(self):
        result = candidate.evaluate(FIXTURE)
        result["historical_allocation"]["disposition"] = "HOLD"
        with self.assertRaises(AssertionError):
            auditor.audit(FIXTURE, result)

    def test_mutation_promoting_finite_result_to_generalization_is_rejected(self):
        result = candidate.evaluate(FIXTURE)
        result["generalization_scope"] = "SUPPORTED"
        with self.assertRaises(AssertionError):
            auditor.audit(FIXTURE, result)

    def test_mutation_ignoring_incomplete_accounting_is_rejected(self):
        result = candidate.evaluate(FIXTURE)
        result["prospective_cases"]["prospective_incomplete_accounting"]["finite_allocation_disposition"] = "RETAIN"
        with self.assertRaises(AssertionError):
            auditor.audit(FIXTURE, result)

    def test_mutation_ignoring_invalidating_discovery_is_rejected(self):
        result = candidate.evaluate(FIXTURE)
        result["prospective_cases"]["prospective_invalidating_discovery"]["finite_allocation_disposition"] = "RETAIN"
        with self.assertRaises(AssertionError):
            auditor.audit(FIXTURE, result)

    def test_mutation_ignoring_correctness_failure_is_rejected(self):
        result = candidate.evaluate(FIXTURE)
        result["prospective_cases"]["prospective_correctness_failure"]["finite_allocation_disposition"] = "RETAIN"
        with self.assertRaises(AssertionError):
            auditor.audit(FIXTURE, result)

    def test_mutation_ignoring_frozen_threshold_failure_is_rejected(self):
        result = candidate.evaluate(FIXTURE)
        result["prospective_cases"]["prospective_frozen_threshold_failure"]["finite_allocation_disposition"] = "RETAIN"
        with self.assertRaises(AssertionError):
            auditor.audit(FIXTURE, result)

    def test_scope_mismatch_is_not_silently_hidden(self):
        altered = copy.deepcopy(FIXTURE)
        altered["scope_mismatch"]["frozen_hold_clause_mentions_insufficient"] = True
        with self.assertRaises(AssertionError):
            auditor.audit(altered, candidate.evaluate(altered))

    def test_mutation_rebinding_historical_source_hash_is_rejected(self):
        altered = copy.deepcopy(FIXTURE)
        altered["source_sha256"]["plan"] = "0" * 64
        with self.assertRaises(AssertionError):
            auditor.audit(altered, candidate.evaluate(altered))


if __name__ == "__main__":
    unittest.main()
