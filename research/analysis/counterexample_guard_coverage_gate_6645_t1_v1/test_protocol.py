import json
import unittest
from pathlib import Path

from auditor import expected
from candidate import decide


class CoverageGateTests(unittest.TestCase):
    def setUp(self):
        with Path("research/analysis/counterexample_guard_coverage_gate_6645_t1_v1/contract.json").open(encoding="utf-8") as source:
            self.contract = json.load(source)
        with Path("research/analysis/counterexample_guard_coverage_gate_6645_t1_v1/fixture.json").open(encoding="utf-8") as source:
            self.fixture = json.load(source)
        self.rows = {row["id"]: row for row in self.fixture["rows"]}

    def test_complete_valid_control_is_admitted(self):
        row = self.rows["valid_complete_coverage"]
        self.assertEqual(decide(row, self.contract), "ADMIT")
        self.assertEqual(expected(row, self.contract), "ADMIT")

    def test_registered_but_uncovered_hidden_family_fails_closed(self):
        row = self.rows["hidden_modal_family_harmful"]
        self.assertEqual(decide(row, self.contract), "UNKNOWN")
        self.assertEqual(expected(row, self.contract), "UNKNOWN")

    def test_unregistered_family_fails_closed(self):
        row = self.rows["unregistered_family"]
        self.assertEqual(decide(row, self.contract), "UNKNOWN")
        self.assertEqual(expected(row, self.contract), "UNKNOWN")

    def test_known_harmful_state_is_refused_when_coverage_is_complete(self):
        row = dict(self.rows["known_stale_target"], candidate_covered_families=list(self.contract["required_families"]))
        self.assertEqual(decide(row, self.contract), "REFUSE")
        self.assertEqual(expected(row, self.contract), "REFUSE")

    def test_incomplete_contract_never_admits(self):
        contract = dict(self.contract, contract_complete_for_fixture=False)
        for row in self.fixture["rows"]:
            self.assertEqual(decide(row, contract), "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
