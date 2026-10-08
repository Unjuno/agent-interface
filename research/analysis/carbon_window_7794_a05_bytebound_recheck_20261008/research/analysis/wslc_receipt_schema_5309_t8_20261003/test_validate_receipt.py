"""Construction and mutation tests; never execute the formal CLI."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

import validate_receipt


INPUT = Path(__file__).parent / "input" / "audit.stdout.json"


class RetainedReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = json.loads(INPUT.read_text(encoding="utf-8"))

    def test_exact_retained_input_passes_identity_and_value_gates(self) -> None:
        result = validate_receipt.build_pass_receipt(INPUT.read_bytes())
        self.assertEqual(result["disposition"], "PASS_RETAINED_RECEIPT_SCHEMA_AUDIT")
        self.assertEqual(result["input"]["bytes"], 306)
        self.assertEqual(result["observed"]["rows"], 432)
        self.assertEqual(result["observed"]["failed_probe_yield_wrong_target"], 0)
        self.assertFalse(result["t7_schema_note"]["t7_verdict_revised"])

    def test_changed_input_identity_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "receipt_byte_count_mismatch|receipt_sha256_mismatch"):
            validate_receipt.validate_bytes(INPUT.read_bytes() + b" ")

    def test_mutated_schema_key_set_rejected(self) -> None:
        changed = dict(self.document)
        del changed["failed_probe_yield_wrong_target"]
        changed["failed_probe_yield_fallback_wrong_target"] = 0
        with self.assertRaisesRegex(ValueError, "receipt_key_set_mismatch"):
            validate_receipt.validate_document(changed)

    def test_mutated_count_rejected(self) -> None:
        changed = dict(self.document, rows=431)
        with self.assertRaisesRegex(ValueError, "receipt_value_mismatch:rows"):
            validate_receipt.validate_document(changed)

    def test_mutated_status_rejected(self) -> None:
        changed = dict(self.document, status="PASS")
        with self.assertRaisesRegex(ValueError, "receipt_value_mismatch:status"):
            validate_receipt.validate_document(changed)

    def test_nonempty_errors_rejected(self) -> None:
        changed = dict(self.document, errors=["corrupt"])
        with self.assertRaisesRegex(ValueError, "receipt_value_mismatch:errors"):
            validate_receipt.validate_document(changed)

    def test_boolean_is_not_accepted_as_integer_count(self) -> None:
        changed = dict(self.document, rows=True)
        with self.assertRaisesRegex(ValueError, "receipt_integer_type_mismatch:rows"):
            validate_receipt.validate_document(changed)


if __name__ == "__main__":
    unittest.main()
