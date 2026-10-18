"""Construction tests for the separate contingency-table auditor."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from audit import independently_classify, mutation_controls, semantic_errors
from candidate import run
from generate import generate


class IndependentAuditConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parent
        cls.config = json.loads((cls.root / "config.json").read_text(encoding="utf-8"))
        cls.fixtures = generate(cls.config)
        cls.truth = {"cases": cls.config["expected"]}
        cls.candidate = run(cls.fixtures, cls.config)
        cls.freeze = {"inputs": {"fixtures.json": "not-used-by-control", "truth.json": "not-used-by-control"}}

    def test_independent_contingency_oracle_matches_all_five_candidate_rows(self):
        self.assertEqual(semantic_errors(self.fixtures, self.config, self.truth, self.candidate), [])
        for fixture in self.fixtures["fixtures"]:
            decision, _ = independently_classify(fixture, self.config)
            row = next(value for value in self.candidate["results"] if value["fixture_id"] == fixture["fixture_id"])
            self.assertEqual(decision["classification"], row["classification"])

    def test_wrong_candidate_class_is_rejected(self):
        changed = json.loads(json.dumps(self.candidate))
        changed["results"][0]["classification"] = "STRUCTURE_NONINVARIANCE"
        self.assertTrue(semantic_errors(self.fixtures, self.config, self.truth, changed))

    def test_all_six_declared_mutation_controls_are_detected(self):
        controls = mutation_controls(self.fixtures, self.config, self.truth, self.candidate, self.freeze)
        self.assertEqual(len(controls), 6)
        self.assertTrue(all(controls.values()), controls)


if __name__ == "__main__":
    unittest.main()
