import importlib.util
import copy
import json
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("t5", Path(__file__).with_name("audit.py"))
t5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t5)


class ClassificationTests(unittest.TestCase):
    cases = [{"id": "positive", "expected_ready": True},
             {"id": "negative", "expected_ready": False}]

    def test_positive_control_failure_is_separate(self):
        self.assertEqual(t5.disposition(self.cases, ["readiness_mismatch:positive"])[0],
                         ["FAIL_POSITIVE_CONTROL"])

    def test_negative_acceptance_is_hypothesis_failure(self):
        self.assertEqual(t5.disposition(self.cases, ["readiness_mismatch:negative"])[0],
                         ["FAIL_TIMESTAMP_ORDER_NEGATIVE_ACCEPTED"])

    def test_both_failures_remain_distinct(self):
        outcomes, pos, neg = t5.disposition(
            self.cases, ["readiness_mismatch:positive", "readiness_mismatch:negative"])
        self.assertEqual(outcomes, ["FAIL_POSITIVE_CONTROL", "FAIL_TIMESTAMP_ORDER_NEGATIVE_ACCEPTED"])
        self.assertEqual(pos, ["positive"])
        self.assertEqual(neg, ["negative"])

    def test_no_mismatch_passes_scoped_gate(self):
        self.assertEqual(t5.disposition(self.cases, [])[0], ["PASS_ORDER_GATE_SCOPED"])


class RawBindingTests(unittest.TestCase):
    t4 = Path(__file__).resolve().parents[1] / "owner_keyup_timestamp_order_5156_t4_20261004"
    cases_doc = json.loads((t4 / "cases.json").read_text())
    raw = json.loads((t4 / "output/raw.json").read_text())

    def test_frozen_raw_reconstructs_exactly(self):
        self.assertEqual(t5.validate_raw(self.cases_doc, self.raw, self.t4)[0], [])

    def test_event_timestamp_mutation_rejected(self):
        raw = copy.deepcopy(self.raw)
        raw["rows"][0]["events"][0]["admitted_ns"] += 1
        self.assertTrue(t5.validate_raw(self.cases_doc, raw, self.t4)[0])

    def test_deleted_events_rejected(self):
        raw = copy.deepcopy(self.raw)
        del raw["rows"][0]["events"]
        self.assertTrue(t5.validate_raw(self.cases_doc, raw, self.t4)[0])

    def test_intent_token_mutation_rejected(self):
        raw = copy.deepcopy(self.raw)
        raw["rows"][0]["analyzer_output"]["holds"][0]["intent_token"] = None
        self.assertTrue(t5.validate_raw(self.cases_doc, raw, self.t4)[0])

    def test_reported_decision_mutation_rejected(self):
        raw = copy.deepcopy(self.raw)
        raw["rows"][0]["analyzer_output"]["decision"] = "FAIL"
        self.assertTrue(t5.validate_raw(self.cases_doc, raw, self.t4)[0])


if __name__ == "__main__":
    unittest.main()
