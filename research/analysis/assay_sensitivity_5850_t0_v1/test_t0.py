import json
import pathlib
import unittest
import importlib.util

ROOT = pathlib.Path(__file__).parent

def load_candidate():
    path = ROOT / "candidate.py"
    if not path.exists():
        raise AssertionError("candidate.classify is not implemented")
    spec = importlib.util.spec_from_file_location("assay_candidate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "qualify"):
        raise AssertionError("candidate.qualify is not implemented")
    return module

class AssaySensitivityTests(unittest.TestCase):
    def test_scenarios_distinguish_resolution_missingness_and_null(self):
        classify = load_candidate().qualify
        fixture = json.loads((ROOT / "fixture.json").read_text())
        got = {x["id"]: classify(x) for x in fixture["cases"]}
        self.assertEqual(got, fixture["expected"])

    def test_raw_result_binds_fixture_digest_and_all_cases(self):
        module = load_candidate()
        result = module.run(ROOT / "fixture.json")
        self.assertEqual(result["allocation"], "5850-ASSAY-SENSITIVITY-T0-20261001-01")
        self.assertEqual(set(result["results"]), {c["id"] for c in json.loads((ROOT / "fixture.json").read_text())["cases"]})
        self.assertEqual(len(result["fixture_sha256"]), 64)

    def test_gross_control_cannot_qualify_meaningful_delta(self):
        classify = load_candidate().qualify
        card = {"id":"gross_only", "meaningful_delta":10, "control_delta":100,
                "resolution":20, "pipeline_shared":True, "missing":False,
                "target_events":10, "primary_defect":False}
        self.assertEqual(classify(card), "HOLD_INADEQUATE_RESOLUTION")

    def test_missing_terminal_outcome_never_qualifies(self):
        classify = load_candidate().qualify
        card = {"id":"missing", "meaningful_delta":10, "control_delta":12,
                "resolution":2, "pipeline_shared":True, "missing":True,
                "target_events":10, "primary_defect":False}
        self.assertEqual(classify(card), "HOLD_MISSING_OUTCOME")

if __name__ == "__main__":
    unittest.main()
