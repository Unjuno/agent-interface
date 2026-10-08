import json
import unittest
from pathlib import Path

import auditor
import candidate


ROOT = Path(__file__).resolve().parent


class IsolatedCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = json.loads((ROOT / "candidate-input.json").read_text())
        cls.oracle = json.loads((ROOT / "oracle.json").read_text())
        cls.raw = candidate.run(cls.inputs)

    def row(self, scenario, arm):
        return next(row for row in self.raw["rows"] if row["scenario"] == scenario and row["arm"] == arm)

    def test_candidate_source_and_input_exclude_oracle_truth(self):
        source = (ROOT / "candidate.py").read_text()
        self.assertNotIn("truth_by_case_id", source)
        self.assertNotIn("oracle.json", source)
        self.assertNotIn("hidden_state", json.dumps(self.inputs))
        self.assertNotIn("truth_by_case_id", json.dumps(self.inputs))
        self.assertEqual(set(case["case_id"] for case in self.inputs["cases"]), set(self.oracle["truth_by_case_id"]))

    def test_primary_identical_set_different_effect_evidence(self):
        generic = self.row("primary", "GENERIC_IG")
        aware = self.row("primary", "WITNESS_AWARE")
        self.assertEqual(generic["admitted_action_set"], aware["admitted_action_set"])
        self.assertEqual(generic["decision"], "UNKNOWN_EFFECT_WITNESS_LOST")
        self.assertEqual(aware["decision"], "COMPLETE")

    def test_controls_and_complete_reconstruction(self):
        self.assertEqual(len(self.raw["rows"]), 56)
        self.assertEqual(self.row("witness-irrelevant", "GENERIC_IG")["decision"], "COMPLETE")
        self.assertEqual(self.row("no-safe-path", "WITNESS_AWARE")["decision"], "UNKNOWN")
        self.assertEqual(self.row("stale-receipt", "WITNESS_AWARE")["decision"], "UNKNOWN")
        self.assertEqual(self.row("duplicate-receipt", "WITNESS_AWARE")["decision"], "COMPLETE")
        self.assertEqual(self.row("urgent-stop", "WITNESS_AWARE")["decision"], "STOP_AND_RELEASE")
        self.assertEqual(self.row("misspecified-model", "WITNESS_AWARE")["decision"], "UNKNOWN_MODEL_MISMATCH")
        self.assertEqual(auditor.audit(self.inputs, self.oracle, self.raw)["rows"], 56)

    def test_auditor_rejects_six_corruptions(self):
        mutations = (
            lambda raw: raw["rows"][0].update(authority_grants=1),
            lambda raw: next(row for row in raw["rows"] if row["scenario"] == "primary" and row["arm"] == "GENERIC_IG").update(decision="COMPLETE", completed=True),
            lambda raw: next(row for row in raw["rows"] if row["scenario"] == "primary" and row["arm"] == "WITNESS_AWARE")["trace"][-1].update(action="commit-b"),
            lambda raw: raw["rows"].pop(),
            lambda raw: raw["rows"].append(dict(raw["rows"][0])),
            lambda raw: next(row for row in raw["rows"] if row["scenario"] == "urgent-stop" and row["arm"] == "WITNESS_AWARE").update(decision="COMPLETE", completed=True),
        )
        for mutate in mutations:
            corrupted = json.loads(json.dumps(self.raw))
            mutate(corrupted)
            with self.assertRaises(ValueError):
                auditor.audit(self.inputs, self.oracle, corrupted)


if __name__ == "__main__":
    unittest.main()
