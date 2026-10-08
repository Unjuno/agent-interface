"""Tests that the raw-only auditor rejects incorrect T0 evidence."""

import copy
import hashlib
import unittest

from auditor import audit
from candidate import run


class RawOnlyAuditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import json
        from pathlib import Path

        cls.fixtures = json.loads(Path("fixtures.json").read_text(encoding="utf-8"))
        cls.raw = run("fixtures.json")
        cls.fixture_sha256 = hashlib.sha256(Path("fixtures.json").read_bytes()).hexdigest()

    def assert_rejected_after(self, mutate):
        raw = copy.deepcopy(self.raw)
        mutate(raw)
        result = audit(raw, self.fixtures, self.fixture_sha256)
        self.assertEqual(result["status"], "FAIL_RAW_AUDIT")
        self.assertTrue(result["violations"])

    def test_accepts_exact_candidate_artifact(self):
        self.assertEqual(
            audit(self.raw, self.fixtures, self.fixture_sha256)["status"],
            "PASS_METHOD_SCOPED",
        )

    def test_rejects_missing_frozen_case(self):
        self.assert_rejected_after(lambda raw: raw["cases"].pop("restart_aba"))

    def test_rejects_wrong_scope_invocation_count(self):
        def change(raw):
            raw["cases"]["equivalent_overlap"]["scope_typed"]["verifier_invocations"] = 2
        self.assert_rejected_after(change)

    def test_rejects_wrong_caller_decision(self):
        def change(raw):
            raw["cases"]["generation_flip"]["scope_typed"]["per_caller"]["a"] = "ADMISSIBLE_TRUE"
        self.assert_rejected_after(change)

    def test_rejects_dropped_waiter(self):
        def change(raw):
            del raw["cases"]["equivalent_overlap"]["scope_typed"]["per_caller"]["b"]
        self.assert_rejected_after(change)

    def test_rejects_corrupted_latency(self):
        def change(raw):
            raw["cases"]["late_after_completion"]["scope_typed"]["decision_latency_ms"]["late"] = 0
        self.assert_rejected_after(change)

    def test_rejects_naive_cross_target_safety_control_that_stops_failing(self):
        def change(raw):
            raw["cases"]["different_target"]["naive_predicate_key"]["per_caller"]["b"] = "ADMISSIBLE_TRUE"
        self.assert_rejected_after(change)

    def test_rejects_changed_frozen_fixture_identity(self):
        def change(raw):
            raw["fixture_sha256"] = "0" * 64
        self.assert_rejected_after(change)

    def test_rejects_no_coalescing_baseline_that_hides_a_call(self):
        def change(raw):
            raw["cases"]["equivalent_overlap"]["no_coalescing"]["verifier_invocations"] = 1
        self.assert_rejected_after(change)

    def test_rejects_unknown_result_upgraded_to_true(self):
        def change(raw):
            raw["cases"]["unknown_result"]["scope_typed"]["per_caller"]["a"] = "ADMISSIBLE_TRUE"
        self.assert_rejected_after(change)


if __name__ == "__main__":
    unittest.main(verbosity=2)
