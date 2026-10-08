import copy
import importlib.util
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parent
AUDITOR = ROOT / "auditor.py"


class IndependentAuditMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not AUDITOR.exists():
            raise AssertionError("independent raw-only auditor is missing")
        spec = importlib.util.spec_from_file_location("auditor", AUDITOR)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)
        cls.fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
        cls.raw = json.loads((ROOT / "construction_candidate_v2.json").read_text(encoding="utf-8"))

    def mutate(self, mutate_row):
        raw = copy.deepcopy(self.raw)
        mutate_row(raw)
        self.assertFalse(self.module.audit(self.fixture, raw)["accepted"])

    def test_accepts_exact_raw_candidate_and_reconstructs_all_attempts(self):
        result = self.module.audit(self.fixture, self.raw)
        self.assertTrue(result["accepted"])
        self.assertEqual(result["audited_cases"], 6)
        self.assertEqual(result["audited_routes"], 12)

    def test_rejects_dropping_a_critical_failure_gate(self):
        def change(raw):
            route = raw["results"][0]["routes"]["B"]
            route["failed_gates"].remove("claim_citation_binding")
        self.mutate(change)

    def test_rejects_promoting_unknown_render_to_pass(self):
        def change(raw):
            raw["results"][4]["routes"]["B"]["dependency_status"] = "PASS"
        self.mutate(change)

    def test_rejects_swapping_claim_citation_target(self):
        def change(raw):
            raw["results"][0]["routes"]["A"]["evidence"]["citation_target_id"] = "study-2"
        self.mutate(change)

    def test_rejects_double_counting_a_checkpoint(self):
        def change(raw):
            raw["results"][0]["routes"]["A"]["partial_score"] += 3
        self.mutate(change)

    def test_rejects_turning_cosmetic_failure_into_a_hard_gate(self):
        def change(raw):
            raw["results"][2]["routes"]["B"]["dependency_status"] = "FAIL"
            raw["results"][2]["routes"]["B"]["viability"] = "FAIL"
        self.mutate(change)


if __name__ == "__main__":
    unittest.main()
