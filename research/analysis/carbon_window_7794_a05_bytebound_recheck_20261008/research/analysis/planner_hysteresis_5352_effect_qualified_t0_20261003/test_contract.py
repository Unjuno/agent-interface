"""Zero-seed construction tests; these are not formal evidence."""
import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = load("candidate")
        cls.auditor = load("auditor")
        cls.fixture = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
        cls.payload = cls.candidate.run(cls.fixture)
        cls.raw = json.dumps(cls.payload, sort_keys=True, separators=(",", ":")).encode() + b"\n"

    def test_five_frozen_case_shapes(self):
        self.assertEqual([c["id"] for c in self.fixture["cases"]], ["B1", "H1", "P1", "S1", "C1"])
        self.assertTrue(all(len(c["symbols"]) == len(c.get("required_modes", c.get("allowed_modes"))) for c in self.fixture["cases"]))

    def test_candidate_schedules_are_well_formed(self):
        self.assertEqual(len(self.payload["rows"]), 5)
        for row in self.payload["rows"]:
            self.assertEqual(set(row["schedules"]), {"raw", "fixed_hysteresis", "minimum_dwell"})
            self.assertTrue(all(len(bits) == len(row["symbols"]) and set(bits) <= {0, 1} for bits in row["schedules"].values()))

    def test_independent_auditor_classifies_both_divergence_kinds(self):
        receipt = self.auditor.verify(self.fixture, self.raw)
        self.assertTrue(receipt["audit_pass"], receipt["errors"])
        self.assertEqual(receipt["summary"], {
            "benign_divergence_witness": True,
            "harmful_divergence_witness": True,
            "unsafe_prefix_witness": True,
            "benign_boundary_cost_reduced": True,
            "method_disposition": "METHOD_PASS_SCOPED",
        })

    def test_schedule_bit_mutation_is_rejected(self):
        mutated = copy.deepcopy(self.payload)
        mutated["rows"][0]["schedules"]["fixed_hysteresis"][0] ^= 1
        raw = json.dumps(mutated, sort_keys=True, separators=(",", ":")).encode() + b"\n"
        receipt = self.auditor.verify(self.fixture, raw)
        self.assertFalse(receipt["audit_pass"])
        self.assertIn("schedule:B1:fixed_hysteresis", receipt["errors"])

    def test_missing_case_is_rejected(self):
        mutated = copy.deepcopy(self.payload)
        mutated["rows"].pop()
        raw = json.dumps(mutated, sort_keys=True, separators=(",", ":")).encode() + b"\n"
        self.assertFalse(self.auditor.verify(self.fixture, raw)["audit_pass"])


if __name__ == "__main__":
    unittest.main()
