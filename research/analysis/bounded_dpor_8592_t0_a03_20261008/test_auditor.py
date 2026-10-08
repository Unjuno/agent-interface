"""Construction tests for the separately implemented exhaustive oracle."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from auditor import audit
from candidate import run


PACKAGE = Path(__file__).parent


def frozen_inputs():
    public = json.loads((PACKAGE / "input.json").read_text(encoding="utf-8"))
    truth = json.loads((PACKAGE / "truth.json").read_text(encoding="utf-8"))
    return public, truth


def small_mutation_fixture(case_id="mutation_lifecycle"):
    original, _ = frozen_inputs()
    events = [
        event for event in original["cases"][0]["events"]
        if event["id"] in {"lease:revoke", "tool:dispatch"}
    ]
    public = {"schema": original["schema"], "cases": [{"case_id": case_id, "events": events}]}
    truth = {"schema": "bounded-dpor-truth-v1", "expected_full_schedule_counts": {case_id: 2}}
    return public, truth


class ExhaustiveOracleTests(unittest.TestCase):
    def test_exhaustive_oracle_reconstructs_reduced_results_and_fault_witness(self):
        public, truth = frozen_inputs()

        result = audit(public, truth, run(public))

        self.assertEqual(result["status"], "PASS_DPOR_METHOD_SCOPED", result["errors"])
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["summary"]["full_schedules"], 45360)
        self.assertIn("ACK_BEFORE_EFFECT_RECEIPT", result["summary"]["violations"])
        self.assertGreaterEqual(result["summary"]["commuting_control_reduction_fraction"], 0.2)

    def test_auditor_rejects_missing_schedule_evidence(self):
        public, truth = small_mutation_fixture()
        raw = run(public)
        raw["cases"][0]["schedule_traces"].pop()

        result = audit(public, truth, raw)

        self.assertNotEqual(result["status"], "PASS_DPOR_METHOD_SCOPED")
        self.assertTrue(any("trace count" in error for error in result["errors"]))

    def test_auditor_rejects_a_false_independence_declaration(self):
        public, truth = small_mutation_fixture()
        mutant = copy.deepcopy(public)
        revoke = next(event for event in mutant["cases"][0]["events"] if event["id"] == "lease:revoke")
        revoke["writes"] = []
        revoke["authority_epoch"] = []
        raw = run(mutant)

        result = audit(public, truth, raw)

        self.assertNotEqual(result["status"], "PASS_DPOR_METHOD_SCOPED")
        self.assertTrue(any("unsound independence" in error for error in result["errors"]))

    def test_auditor_rejects_corrupted_transition_receipts(self):
        public, truth = small_mutation_fixture()
        raw = run(public)
        row = next(case for case in raw["cases"] if case["case_id"] == "mutation_lifecycle")
        row["schedule_traces"][0]["outputs"][0]["status"] = "invented_success"

        result = audit(public, truth, raw)

        self.assertNotEqual(result["status"], "PASS_DPOR_METHOD_SCOPED")
        self.assertTrue(any("replay mismatch" in error for error in result["errors"]))

    def test_auditor_rejects_removing_the_only_safety_violation_witness(self):
        original, _ = frozen_inputs()
        event = next(item for item in original["cases"][0]["events"] if item["id"] == "caller:ack")
        public = {"schema": original["schema"], "cases": [{"case_id": "mutation_witness", "events": [event]}]}
        truth = {
            "schema": "bounded-dpor-truth-v1",
            "expected_full_schedule_counts": {"mutation_witness": 1},
            "required_violations": ["ACK_BEFORE_EFFECT_RECEIPT"],
        }
        raw = run(public)
        row = next(case for case in raw["cases"] if case["case_id"] == "mutation_witness")
        row["schedule_traces"] = [trace for trace in row["schedule_traces"] if not trace["violations"]]

        result = audit(public, truth, raw)

        self.assertNotEqual(result["status"], "PASS_DPOR_METHOD_SCOPED")
        self.assertTrue(any("violation witness" in error for error in result["errors"]))

    def test_auditor_rejects_incomplete_ordered_pair_baseline(self):
        public, truth = small_mutation_fixture()
        raw = run(public)
        baseline = raw["cases"][0]["ordered_pair_baseline"]
        baseline["ordered_pairs"].pop()

        result = audit(public, truth, raw)

        self.assertNotEqual(result["status"], "PASS_DPOR_METHOD_SCOPED")
        self.assertTrue(any("ordered-pair baseline coverage mismatch" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
