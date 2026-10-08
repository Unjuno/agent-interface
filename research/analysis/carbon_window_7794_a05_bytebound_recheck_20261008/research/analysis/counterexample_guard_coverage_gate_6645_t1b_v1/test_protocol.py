import json
import unittest
from pathlib import Path

from candidate_input.candidate import decide
from auditor import reconstruct


class IsolatedCoverageGateTests(unittest.TestCase):
    def setUp(self):
        base = Path("research/analysis/counterexample_guard_coverage_gate_6645_t1b_v1")
        with (base / "candidate_input/contract.json").open(encoding="utf-8") as source:
            self.contract = json.load(source)
        with (base / "candidate_input/candidate_fixture.json").open(encoding="utf-8") as source:
            self.fixture = json.load(source)
        self.rows = {row["id"]: row for row in self.fixture["rows"]}

    def test_only_gate_switch_changes_hidden_harmful_decision(self):
        row = self.rows["hidden_modal_harmful_incomplete_coverage"]
        self.assertEqual(decide(row, self.contract, False), "ADMIT")
        self.assertEqual(decide(row, self.contract, True), "UNKNOWN")
        self.assertEqual(reconstruct(row, self.contract, False), "ADMIT")
        self.assertEqual(reconstruct(row, self.contract, True), "UNKNOWN")

    def test_safe_and_harmful_hidden_pair_is_observationally_identical(self):
        harmful = self.rows["hidden_modal_harmful_incomplete_coverage"]
        safe = self.rows["hidden_modal_safe_incomplete_coverage"]
        self.assertEqual(harmful["covered_predicates"], safe["covered_predicates"])
        self.assertEqual(harmful["observations"], safe["observations"])
        self.assertEqual(decide(harmful, self.contract, True), "UNKNOWN")
        self.assertEqual(decide(safe, self.contract, True), "UNKNOWN")

    def test_complete_valid_and_known_harm_controls_are_unchanged(self):
        valid = self.rows["valid_complete_coverage"]
        stale = self.rows["known_stale_complete_coverage"]
        for gate in (False, True):
            self.assertEqual(decide(valid, self.contract, gate), "ADMIT")
            self.assertEqual(decide(stale, self.contract, gate), "REFUSE")

    def test_unregistered_family_fails_closed_only_with_gate(self):
        row = self.rows["unregistered_surface_family"]
        self.assertEqual(decide(row, self.contract, False), "ADMIT")
        self.assertEqual(decide(row, self.contract, True), "UNKNOWN")

    def test_false_completeness_and_missing_observation_fail_closed(self):
        row = self.rows["valid_complete_coverage"]
        contract = dict(self.contract, contract_complete_for_fixture=False)
        self.assertEqual(decide(row, contract, True), "UNKNOWN")
        malformed = dict(row, observations={"target_freshness": "current"})
        self.assertEqual(decide(malformed, self.contract, False), "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
