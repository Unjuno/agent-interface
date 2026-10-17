import copy
import json
import unittest
from pathlib import Path

from branch_audit import diagnostic_mutations, validate


HERE = Path(__file__).resolve().parent
FIXTURE = json.loads((HERE / "input/fixture.json").read_text())
RAW = json.loads((HERE / "input/candidate-a01.json").read_text())


class PolicyBranchBindingTests(unittest.TestCase):
    def test_unchanged_candidate_replays_every_recoverable_policy(self):
        result = validate(FIXTURE, RAW)
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["cases_reconstructed"], 5)
        self.assertEqual(result["policies_replayed"], 2)

    def test_unsupported_observation_values_are_rejected(self):
        mutation = diagnostic_mutations(RAW)["unsupported_observation_values"]
        result = validate(FIXTURE, mutation)
        self.assertFalse(result["passed"])
        self.assertTrue(any("exactly cover emitted observations" in e for e in result["errors"]))

    def test_swapped_observation_routes_are_rejected(self):
        mutation = diagnostic_mutations(RAW)["swapped_observation_routes"]
        result = validate(FIXTURE, mutation)
        self.assertFalse(result["passed"])
        self.assertTrue(any("all-goal belief" in e for e in result["errors"]))


if __name__ == "__main__":
    unittest.main()
