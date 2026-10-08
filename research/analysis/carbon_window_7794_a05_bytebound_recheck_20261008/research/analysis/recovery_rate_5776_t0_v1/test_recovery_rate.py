"""Focused host CI for the frozen #5776 finite candidate/auditor contract."""
import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RecoveryRateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = load("candidate")
        cls.audit = load("audit")
        cls.fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))

    def test_frozen_complete_population_and_method_fail(self):
        doc = self.candidate.build_raw()
        self.assertEqual(doc["episode_count"], 160)
        self.assertEqual(doc["opportunity_count"], 1280)
        self.assertEqual(doc["threshold"], 3.5)
        self.assertEqual(doc["method_disposition"], "FAIL_METHOD")
        self.assertEqual(doc["summary"]["heldout_gradual_sensitivity"], 0.25)
        self.assertEqual(self.audit.reconstruct(doc, self.fixture), ["heldout_gradual_sensitivity_gate"])

    def test_every_allocated_episode_is_present(self):
        doc = self.candidate.build_raw()
        keys = {(row["mechanism"], row["episode_id"]) for row in doc["episodes"]}
        expected = {(m, i) for m in self.audit.EXPECTED_MECHANISMS for i in range(40)}
        self.assertEqual(keys, expected)

    def test_mutation_controls(self):
        doc = self.candidate.build_raw()
        results = self.audit.mutation_results(doc, self.fixture)
        self.assertEqual(len(results), 6)
        self.assertTrue(all(row["rejected"] for row in results))


if __name__ == "__main__":
    unittest.main()
