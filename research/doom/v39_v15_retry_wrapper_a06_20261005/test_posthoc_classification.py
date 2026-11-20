import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posthoc_classification import EXPECTED_FROZEN_FAILURE, classify


class PosthocClassificationTests(unittest.TestCase):
    def setUp(self):
        self.raw_checks = {"drop_then_retry": True, "receipt_identity": True}
        self.frozen_audit = {
            "status": "FAIL",
            "checks": dict(EXPECTED_FROZEN_FAILURE),
        }

    def test_identifies_only_the_exact_recorded_auditor_failure_signature(self):
        self.assertEqual(
            classify(self.raw_checks, self.frozen_audit),
            "RAW_BEHAVIOR_CONFIRMED_AUDITOR_SCHEMA_BUG",
        )

    def test_does_not_label_a_different_failed_check_as_the_schema_bug(self):
        self.frozen_audit["checks"]["first_keyup_was_dropped"] = False
        self.assertEqual(classify(self.raw_checks, self.frozen_audit), "POSTHOC_CHECK_FAILURE")

    def test_does_not_infer_a_failed_check_from_status_alone(self):
        del self.frozen_audit["checks"]
        self.assertEqual(classify(self.raw_checks, self.frozen_audit), "POSTHOC_CHECK_FAILURE")

    def test_does_not_classify_raw_check_failure_as_auditor_schema_bug(self):
        self.raw_checks["receipt_identity"] = False
        self.assertEqual(classify(self.raw_checks, self.frozen_audit), "POSTHOC_CHECK_FAILURE")


if __name__ == "__main__":
    unittest.main()
