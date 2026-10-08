import unittest

from candidate import classify, evaluate
from auditor import audit


class RecoveryClassificationTests(unittest.TestCase):
    def test_classifies_only_independently_confirmed_effect_and_receipt(self):
        image = {"effect": "CONFIRMED", "receipt": "DONE", "receipt_bytes_valid": True}
        self.assertEqual("EFFECT_AND_RECEIPT_CONFIRMED", classify(image))

    def test_effect_without_durable_receipt_is_unknown(self):
        image = {"effect": "CONFIRMED", "receipt": "ABSENT", "receipt_bytes_valid": True}
        self.assertEqual("UNKNOWN_RECONCILE", classify(image))

    def test_receipt_without_confirmed_effect_is_unknown(self):
        image = {"effect": "NO_EFFECT_CONFIRMED", "receipt": "DONE", "receipt_bytes_valid": True}
        self.assertEqual("UNKNOWN_RECONCILE", classify(image))

    def test_no_effect_requires_absent_receipt_and_independent_negative_oracle(self):
        image = {"effect": "NO_EFFECT_CONFIRMED", "receipt": "ABSENT", "receipt_bytes_valid": True}
        self.assertEqual("NO_EFFECT_CONFIRMED", classify(image))

    def test_torn_or_invalid_receipt_is_untrusted(self):
        image = {"effect": "CONFIRMED", "receipt": "TORN", "receipt_bytes_valid": False}
        self.assertEqual("CORRUPT_OR_UNTRUSTED", classify(image))

    def test_evaluator_emits_all_process_and_machine_crash_images(self):
        fixture = {
            "scenarios": [{
                "id": "cut-before-dir-sync",
                "process_images": [{"effect": "CONFIRMED", "receipt": "DONE", "receipt_bytes_valid": True}],
                "machine_images": [
                    {"effect": "CONFIRMED", "receipt": "ABSENT", "receipt_bytes_valid": True},
                    {"effect": "CONFIRMED", "receipt": "DONE", "receipt_bytes_valid": True},
                ],
            }]
        }
        rows = evaluate(fixture)
        self.assertEqual(3, len(rows))
        self.assertEqual("EFFECT_AND_RECEIPT_CONFIRMED", rows[0]["classification"])
        self.assertEqual("UNKNOWN_RECONCILE", rows[1]["classification"])

    def test_raw_auditor_rejects_tampered_completion_classification(self):
        fixture = {
            "scenarios": [{
                "id": "effect-without-receipt",
                "process_images": [],
                "machine_images": [{"effect": "CONFIRMED", "receipt": "ABSENT", "receipt_bytes_valid": True}],
            }]
        }
        forged = [{
            "scenario": "effect-without-receipt", "model": "MACHINE", "image_index": 0,
            "image": {"effect": "CONFIRMED", "receipt": "ABSENT", "receipt_bytes_valid": True},
            "classification": "EFFECT_AND_RECEIPT_CONFIRMED",
        }]
        self.assertFalse(audit(fixture, forged)["pass"])

    def test_raw_auditor_accepts_independently_correct_rows(self):
        fixture = {
            "scenarios": [{
                "id": "same-store-commit",
                "process_images": [],
                "machine_images": [{"effect": "CONFIRMED", "receipt": "DONE", "receipt_bytes_valid": True}],
            }]
        }
        rows = evaluate(fixture)
        report = audit(fixture, rows)
        self.assertTrue(report["pass"])
        self.assertEqual(1, report["rows_checked"])


if __name__ == "__main__":
    unittest.main()
