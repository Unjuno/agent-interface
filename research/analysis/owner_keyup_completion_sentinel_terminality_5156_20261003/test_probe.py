"""Artifact-level regression checks for the one-shot terminality probe."""
import json
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/formal-01"


class TerminalityProbeArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.control = [json.loads(line) for line in
                       (OUT / "control/raw.jsonl").read_text(encoding="utf-8").splitlines()]
        cls.treatment = [json.loads(line) for line in
                         (OUT / "nonterminal/raw.jsonl").read_text(encoding="utf-8").splitlines()]
        cls.candidate = json.loads((OUT / "CANDIDATE.json").read_text(encoding="utf-8"))
        cls.audit = json.loads((OUT / "INDEPENDENT_AUDIT.json").read_text(encoding="utf-8"))

    def test_control_places_completion_last(self):
        self.assertEqual(self.control[-1]["event"], "runner_complete")
        self.assertEqual(type(self.control[-1]["exit_code"]), int)
        self.assertEqual(self.control[-1]["exit_code"], 0)

    def test_treatment_places_completion_first(self):
        self.assertEqual(self.treatment[0]["event"], "runner_complete")
        self.assertEqual(type(self.treatment[0]["exit_code"]), int)
        self.assertEqual(self.treatment[0]["exit_code"], 0)

    def test_only_completion_position_changes(self):
        self.assertEqual(self.control[-1], self.treatment[0])
        self.assertEqual(self.control[:-1], self.treatment[1:])

    def test_target_and_independent_results_reconcile(self):
        self.assertEqual(self.candidate["status"], "FINDING_NONTERMINAL_COMPLETION_ACCEPTED")
        self.assertEqual(self.audit["status"], self.candidate["status"])
        self.assertEqual(self.audit["errors"], [])
        self.assertEqual(self.audit["control"]["exit_code"], 0)
        self.assertEqual(self.audit["nonterminal"]["exit_code"], 0)


if __name__ == "__main__":
    unittest.main()
