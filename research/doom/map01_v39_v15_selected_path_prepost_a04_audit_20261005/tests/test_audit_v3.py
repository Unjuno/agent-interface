import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "code" / "audit_v3.py"
AUDIT_V2 = ROOT / "code" / "audit_v2.py"
RAW = ROOT / "inputs" / "a02_candidate.stdout"


def load_audit():
    if not AUDIT.is_file():
        raise AssertionError("audit_v3.py is missing; trace-result payload checks are not implemented")
    spec = importlib.util.spec_from_file_location("audit_v3_under_test", AUDIT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_audit_v2():
    spec = importlib.util.spec_from_file_location("audit_v2_baseline", AUDIT_V2)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TraceSampleAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads(RAW.read_text(encoding="utf-8"))
        cls.audit = load_audit()

    def case(self, name):
        return next(x for x in self.raw["cases"] if x["case"] == name)

    def test_accepts_trace_samples_bound_to_query_and_summary(self):
        case = self.case("lost_space_keyrelease")
        self.assertEqual(self.audit.trace_sample_errors(case, [65, 74], [65]), [])

    def test_rejects_post_result_that_disagrees_with_summary(self):
        case = json.loads(json.dumps(self.case("lost_space_keyrelease")))
        result = next(e for e in case["trace"] if e.get("kind") == "keymap_sample_result" and e.get("stage") == "post")
        result["keycodes_down"] = []
        self.assertIn("post_result_summary_mismatch", self.audit.trace_sample_errors(case, [65, 74], [65]))

    def test_v3_closes_the_trace_payload_gap_left_by_v2(self):
        data = json.loads(RAW.read_text(encoding="utf-8"))
        result = next(e for e in data["cases"][1]["trace"]
                      if e.get("kind") == "keymap_sample_result" and e.get("stage") == "post")
        result["keycodes_down"] = []
        v2 = load_audit_v2()
        self.assertFalse(any(not check["passed"] for check in v2.evaluate(data)))
        self.assertTrue(any(not check["passed"] for check in self.audit.evaluate_a04(data)))

    def test_binds_parent_run_record_separately_from_a04_freeze(self):
        hashes = {"raw": "frozen-raw"}
        source_hash = "frozen-auditor"
        parent = {"base_commit": self.audit.A02_BASE,
                  "planned_candidate_invocations": 1,
                  "planned_auditor_invocations": 1,
                  "retries": 0,
                  "source_bindings": [1] * 8}
        freeze = {"allocation": "V39-V15-PREPOST-A04-TRACE-AUDIT-20261005-01",
                  "candidate_invocations_planned": 0,
                  "auditor_invocations_planned": 1,
                  "candidate_invocations_actual": 0,
                  "auditor_invocations_actual": 0,
                  "retries": 0,
                  "auditor_source_sha256": source_hash,
                  "inputs": hashes}
        self.assertEqual(self.audit.preregistration_errors(parent, freeze, hashes, source_hash), [])
        self.assertIn("a04_preregistration_mismatch",
                      self.audit.preregistration_errors(parent, {**freeze, "inputs": {}}, hashes, source_hash))

    def test_rejects_result_with_wrong_stage(self):
        case = json.loads(json.dumps(self.case("lost_space_keyrelease")))
        result = next(e for e in case["trace"] if e.get("kind") == "keymap_sample_result" and e.get("stage") == "post")
        result["stage"] = "pre"
        self.assertIn("post_result_stage_mismatch", self.audit.trace_sample_errors(case, [65, 74], [65]))

    def test_rejects_query_payload_not_bound_to_result(self):
        case = json.loads(json.dumps(self.case("lost_space_keyrelease")))
        query = next(e for e in case["trace"] if e.get("kind") == "query_keymap" and e.get("display") == "post_batch_sampler")
        query["held"] = []
        self.assertIn("post_query_result_mismatch", self.audit.trace_sample_errors(case, [65, 74], [65]))

    def test_rejects_missing_post_query_and_misordered_result(self):
        case = json.loads(json.dumps(self.case("lost_space_keyrelease")))
        query = next(e for e in case["trace"] if e.get("kind") == "query_keymap" and e.get("display") == "post_batch_sampler")
        case["trace"].remove(query)
        errors = self.audit.trace_sample_errors(case, [65, 74], [65])
        self.assertIn("post_query_count_mismatch", errors)

        case = json.loads(json.dumps(self.case("lost_space_keyrelease")))
        query_index = next(i for i, e in enumerate(case["trace"]) if e.get("kind") == "query_keymap" and e.get("display") == "post_batch_sampler")
        result_index = next(i for i, e in enumerate(case["trace"]) if e.get("kind") == "keymap_sample_result" and e.get("stage") == "post")
        case["trace"][query_index], case["trace"][result_index] = case["trace"][result_index], case["trace"][query_index]
        self.assertIn("post_query_result_order_mismatch", self.audit.trace_sample_errors(case, [65, 74], [65]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
