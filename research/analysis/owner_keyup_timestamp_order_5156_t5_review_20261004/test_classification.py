import importlib.util
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


if __name__ == "__main__":
    unittest.main()
