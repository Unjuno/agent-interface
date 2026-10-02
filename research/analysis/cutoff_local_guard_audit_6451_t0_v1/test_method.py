import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location("candidate", ROOT / "candidate.py")
candidate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(candidate)
ASPEC = importlib.util.spec_from_file_location("auditor", ROOT / "auditor.py")
auditor = importlib.util.module_from_spec(ASPEC)
ASPEC.loader.exec_module(auditor)


class CutoffMethodTests(unittest.TestCase):
    def test_valid_sharp_cutoff_recovers_planted_local_effect(self):
        data = json.loads((ROOT / "cases.json").read_text())
        result = candidate.evaluate(data["cases"][0], data)
        self.assertEqual(result["decision"], "ESTIMATE_LOCAL")
        self.assertAlmostEqual(result["local_effect"], 2.0, places=9)

    def test_independent_auditor_reconstructs_all_attempts_and_denominators(self):
        spec = json.loads((ROOT / "cases.json").read_text())
        raw = candidate.run(spec)
        result = auditor.audit(spec, raw)
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["reconstructed_cases"], 6)
        self.assertEqual(result["attempted_case_ids"], [c["id"] for c in spec["cases"]])

    def test_independent_auditor_rejects_row_decision_denominator_and_source_mutations(self):
        spec = json.loads((ROOT / "cases.json").read_text())
        original = candidate.run(spec)
        mutations = []
        x = json.loads(json.dumps(original)); x["results"][0]["rows"].pop(); mutations.append(x)
        x = json.loads(json.dumps(original)); x["results"][2]["decision"] = "ESTIMATE_LOCAL"; mutations.append(x)
        x = json.loads(json.dumps(original)); x["attempted_cases"] = 5; mutations.append(x)
        x = json.loads(json.dumps(original)); x["results"][1]["rows"][0]["outcome"] += 1; mutations.append(x)
        for raw in mutations:
            with self.subTest(raw=raw["results"][0]["denominator"]):
                self.assertNotEqual(auditor.audit(spec, raw)["status"], "PASS_METHOD_SCOPED")

    def test_smooth_trend_zero_effect_is_not_called_a_guard_gain(self):
        data = json.loads((ROOT / "cases.json").read_text())
        result = candidate.evaluate(data["cases"][1], data)
        self.assertEqual(result["decision"], "ESTIMATE_LOCAL")
        self.assertAlmostEqual(result["local_effect"], 0.0, places=9)
        self.assertNotEqual(result["decision"], "POSITIVE_GUARD_GAIN")

    def test_sorting_coincident_transition_and_heaping_refuse_identification(self):
        data = json.loads((ROOT / "cases.json").read_text())
        expected = ["REFUSE_SORTING", "REFUSE_COINCIDENT_TRANSITION", "REFUSE_TIMESTAMP_HEAPING"]
        for case, decision in zip(data["cases"][2:5], expected):
            with self.subTest(case=case["id"]):
                self.assertEqual(candidate.evaluate(case, data)["decision"], decision)

    def test_noncompliance_reports_first_stage_and_fuzzy_local_effect(self):
        data = json.loads((ROOT / "cases.json").read_text())
        result = candidate.evaluate(data["cases"][5], data)
        self.assertEqual(result["decision"], "ESTIMATE_LOCAL_FUZZY")
        self.assertAlmostEqual(result["first_stage_jump"], 0.5, places=9)
        self.assertAlmostEqual(result["local_effect"], 2.0, places=9)


if __name__ == "__main__":
    unittest.main()
