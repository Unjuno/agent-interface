import copy
import json
import unittest
from pathlib import Path

from verify_receipt import validate_receipt, validate_receipt_bytes


INPUT_BYTES = (Path(__file__).parent / "inputs" / "audit.stdout.json").read_bytes()
VALID_RECEIPT = json.loads(INPUT_BYTES.decode("utf-8"))


class RetainedReceiptTests(unittest.TestCase):
    def test_accepts_exact_captured_receipt(self):
        result = validate_receipt_bytes(INPUT_BYTES)
        self.assertEqual(result["status"], "PASS_RETAINED_RECEIPT_SCHEMA_AUDIT")
        self.assertEqual(result["rows"], 432)
        self.assertEqual(result["failed_probe_yield_wrong_target"], 0)

    def test_rejects_changed_input_bytes(self):
        with self.assertRaisesRegex(ValueError, "input SHA-256"):
            validate_receipt_bytes(INPUT_BYTES + b"\n")

    def test_rejects_invalid_utf8_json(self):
        with self.assertRaisesRegex(ValueError, "input SHA-256"):
            validate_receipt_bytes(b"not the retained receipt")

    def test_rejects_legacy_misspelled_yield_field(self):
        receipt = copy.deepcopy(VALID_RECEIPT)
        receipt["failed_probe_yield_fallback_wrong_target"] = receipt.pop(
            "failed_probe_yield_wrong_target"
        )
        with self.assertRaisesRegex(ValueError, "schema keys"):
            validate_receipt(receipt)

    def test_rejects_changed_counts_and_semantic_identity(self):
        for field, value in (("rows", 431), ("unique_cases", 431),
                             ("independent_row_matches", 431),
                             ("semantic_sha256", "0" * 64)):
            with self.subTest(field=field):
                receipt = copy.deepcopy(VALID_RECEIPT)
                receipt[field] = value
                with self.assertRaisesRegex(ValueError, field):
                    validate_receipt(receipt)

    def test_rejects_changed_fallback_wrong_target_counts(self):
        for field, value in (("failed_probe_task_fallback_wrong_target", 26),
                             ("failed_probe_yield_wrong_target", 1)):
            with self.subTest(field=field):
                receipt = copy.deepcopy(VALID_RECEIPT)
                receipt[field] = value
                with self.assertRaisesRegex(ValueError, field):
                    validate_receipt(receipt)

    def test_rejects_nonzero_authority_or_audit_errors(self):
        for field, value in (("authority_grants", 1), ("errors", ["unexpected"])):
            with self.subTest(field=field):
                receipt = copy.deepcopy(VALID_RECEIPT)
                receipt[field] = value
                with self.assertRaisesRegex(ValueError, field):
                    validate_receipt(receipt)

    def test_rejects_wrong_status_or_value_types(self):
        for field, value in (("status", "PASS"), ("rows", True)):
            with self.subTest(field=field):
                receipt = copy.deepcopy(VALID_RECEIPT)
                receipt[field] = value
                with self.assertRaisesRegex(ValueError, field):
                    validate_receipt(receipt)


if __name__ == "__main__":
    unittest.main()

