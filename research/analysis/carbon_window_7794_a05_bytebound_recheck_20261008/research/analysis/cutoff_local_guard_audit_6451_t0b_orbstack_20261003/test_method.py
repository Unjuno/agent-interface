import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


candidate = load("candidate")
auditor = load("auditor")


class CutoffT0bTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads((ROOT / "cases.json").read_text())
        cls.raw = candidate.run(cls.spec)

    def test_all_six_frozen_case_decisions_and_effects(self):
        self.assertEqual([r["decision"] for r in self.raw["results"]], self.spec["expected_decisions"])
        self.assertAlmostEqual(self.raw["results"][0]["local_effect"], 2.0)
        self.assertAlmostEqual(self.raw["results"][1]["local_effect"], 0.0)
        self.assertAlmostEqual(self.raw["results"][5]["first_stage_jump"], 0.5)
        self.assertAlmostEqual(self.raw["results"][5]["local_effect"], 2.0)

    def test_comparator_is_strictly_restricted_to_frozen_bandwidth(self):
        r = self.raw["results"][0]
        self.assertEqual(r["local_denominator"], 8)
        self.assertEqual(r["left_local_n"], 4)
        self.assertEqual(r["right_local_n"], 4)
        self.assertAlmostEqual(r["naive_near_cutoff_difference"], 11.0)
        self.assertAlmostEqual(r["local_effect"], 2.0)

    def test_auditor_reconstructs_all_rows_decisions_and_denominators(self):
        result = auditor.audit(self.spec, self.raw)
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["reconstructed_cases"], 6)
        self.assertEqual(result["errors"], [])

    def test_five_effective_corruptions_are_rejected(self):
        result = auditor.controls(self.spec, self.raw)
        self.assertEqual(result["status"], "PASS_CONTROLS")
        self.assertEqual((result["rejected"], result["total"]), (5, 5))
        self.assertTrue(all(c["effective"] and c["rejected"] for c in result["controls"]))

    def test_attempt_count_mutation_fails(self):
        mutated = json.loads(json.dumps(self.raw))
        mutated["attempted_cases"] -= 1
        self.assertEqual(auditor.audit(self.spec, mutated)["status"], "FAIL_AUDIT")


if __name__ == "__main__":
    unittest.main()
