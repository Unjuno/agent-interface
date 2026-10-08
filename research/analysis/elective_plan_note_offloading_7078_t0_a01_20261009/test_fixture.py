"""Pre-freeze construction controls; these are not formal candidate/auditor runs."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("candidate_fixture", HERE / "candidate.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)
audit_spec = importlib.util.spec_from_file_location("auditor_fixture", HERE / "auditor.py")
auditor = importlib.util.module_from_spec(audit_spec)
audit_spec.loader.exec_module(auditor)
DATA = json.loads((HERE / "input.json").read_text())
ORACLE = json.loads((HERE / "oracle.json").read_text())


class FixtureTests(unittest.TestCase):
    def setUp(self):
        self.output = candidate.run(copy.deepcopy(DATA))

    def test_authored_decision_cases(self):
        self.assertEqual({r["id"]: r["choice"] for r in self.output["rows"]}, ORACLE["expected_choices"])

    def test_clean_independent_audit(self):
        self.assertEqual(auditor.audit(DATA, self.output, ORACLE), [])

    def test_mutation_mandatory_laundering(self):
        bad = copy.deepcopy(self.output); bad["rows"][0]["mandatory_ids"] = []
        self.assertTrue(any("mandatory" in e for e in auditor.audit(DATA, bad, ORACLE)))

    def test_mutation_factual_support_substituted_for_q0(self):
        changed = copy.deepcopy(DATA); changed["cases"][0]["q0"] = 0.99
        self.assertTrue(auditor.audit(changed, self.output, ORACLE))

    def test_mutation_calibration_leakage(self):
        changed = copy.deepcopy(DATA); changed["calibration_ids"].append("eval-c")
        self.assertTrue(any("leakage" in e for e in auditor.audit(changed, self.output, ORACLE)))

    def test_mutation_failed_write_relabeled_delivered(self):
        changed = copy.deepcopy(DATA); changed["cases"][2]["delivered"] = True
        self.assertTrue(auditor.audit(changed, self.output, ORACLE))

    def test_mutation_stale_generation(self):
        changed = copy.deepcopy(DATA); changed["cases"][0]["generation"] = 8
        self.assertTrue(auditor.audit(changed, self.output, ORACLE))

    def test_mutation_source_misbinding(self):
        changed = copy.deepcopy(DATA); changed["cases"][0]["note_source"] = "other-source"
        self.assertTrue(auditor.audit(changed, self.output, ORACLE))

    def test_mutation_support_now_mislabeled_as_q0(self):
        changed = copy.deepcopy(DATA); changed["cases"][0]["q0_kind"] = "present_factual_support"
        self.assertTrue(auditor.audit(changed, self.output, ORACLE))

    def test_mutation_forecast_cost_erased(self):
        changed = copy.deepcopy(DATA); changed["cases"][1]["forecast_write_read_cost"] = 0
        self.assertTrue(auditor.audit(changed, self.output, ORACLE))


if __name__ == "__main__":
    unittest.main()
