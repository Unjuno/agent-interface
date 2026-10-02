#!/usr/bin/env python3
"""Pre-freeze tests, including adversarial raw-result mutations."""
import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import candidate
import audit


class ConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
        cls.truth = json.loads((HERE / "truth.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "raw.json"
            candidate.main(str(HERE / "fixture.json"), str(path))
            cls.raw = json.loads(path.read_text(encoding="utf-8"))

    def test_independent_audit_accepts_candidate(self):
        result = audit.audit(self.fixture, self.truth, self.raw)
        self.assertEqual(result["result"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["audited_rows"], len(self.fixture["cases"]))

    def test_false_admission_is_rejected(self):
        forged = copy.deepcopy(self.raw)
        row = next(r for r in forged["rows"] if r["id"] == "common_unsafe")
        row["relational_admit"] = True
        with self.assertRaises(AssertionError):
            audit.audit(self.fixture, self.truth, forged)

    def test_dropped_case_is_rejected(self):
        forged = copy.deepcopy(self.raw)
        forged["rows"].pop()
        with self.assertRaises(AssertionError):
            audit.audit(self.fixture, self.truth, forged)

    def test_forged_concrete_state_is_rejected(self):
        forged = copy.deepcopy(self.raw)
        row = next(r for r in forged["rows"] if r["id"] == "common_safe")
        row["concrete_states"][0]["safe"] = False
        with self.assertRaises(AssertionError):
            audit.audit(self.fixture, self.truth, forged)

    def test_all_unsafe_and_mutation_rows_refuse(self):
        for row in self.raw["rows"]:
            if row["id"] not in ("common_safe", "common_boundary"):
                self.assertFalse(row["relational_admit"], row["id"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
