import copy
import unittest

from verify_receipt import validate_receipt


VALID_RECEIPT = {
    "status": "PASS_T6_INDEPENDENT_FINITE_ORACLE",
    "rows": 432,
    "unique_cases": 432,
    "independent_row_matches": 432,
    "semantic_sha256": "a7bd0adc9485df7161b7ce85c27b1dc58fad71ee2fee9cfe081cc61337b0e193",
    "failed_probe_task_fallback_wrong_target": 27,
    "failed_probe_yield_fallback_wrong_target": 0,
    "authority_grants": 0,
    "errors": [],
}


class ValidateReceiptTests(unittest.TestCase):
    def test_accepts_exact_retained_auditor_receipt(self):
        result = validate_receipt(VALID_RECEIPT)
        self.assertEqual(result["status"], "PASS_HOST_RECEIPT_AUDIT")
        self.assertEqual(result["rows"], 432)
        self.assertEqual(result["semantic_sha256"], VALID_RECEIPT["semantic_sha256"])

    def test_rejects_incomplete_row_coverage(self):
        receipt = copy.deepcopy(VALID_RECEIPT)
        receipt["rows"] = 431
        with self.assertRaisesRegex(ValueError, "rows"):
            validate_receipt(receipt)

    def test_rejects_changed_semantic_identity(self):
        receipt = copy.deepcopy(VALID_RECEIPT)
        receipt["semantic_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "semantic_sha256"):
            validate_receipt(receipt)

    def test_rejects_wrong_target_fallback_regression(self):
        receipt = copy.deepcopy(VALID_RECEIPT)
        receipt["failed_probe_yield_fallback_wrong_target"] = 1
        with self.assertRaisesRegex(ValueError, "failed_probe_yield_fallback_wrong_target"):
            validate_receipt(receipt)

    def test_rejects_authority_or_audit_errors(self):
        for field, value in (("authority_grants", 1), ("errors", ["unexpected"])):
            with self.subTest(field=field):
                receipt = copy.deepcopy(VALID_RECEIPT)
                receipt[field] = value
                with self.assertRaisesRegex(ValueError, field):
                    validate_receipt(receipt)

    def test_rejects_wrong_auditor_status(self):
        receipt = copy.deepcopy(VALID_RECEIPT)
        receipt["status"] = "PASS"
        with self.assertRaisesRegex(ValueError, "status"):
            validate_receipt(receipt)


if __name__ == "__main__":
    unittest.main()

