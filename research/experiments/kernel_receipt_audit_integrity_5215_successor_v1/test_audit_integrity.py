import copy
import unittest
from audit_integrity import audit, EXPECTED_KEYS

BASE = {
"execution_end_700": True, "execution_end_999": True, "execution_end_1000": True,
"execution_end_1001": True, "execution_wrong_command": False,
"effect_at_499": True, "effect_at_699": True, "effect_at_700": True, "effect_at_701": True,
}

class AuditIntegrityTests(unittest.TestCase):
    def test_original_record_is_held_for_legacy_plan_conflict(self):
        got = audit(BASE)
        self.assertEqual(got["disposition"], "HOLD_LEGACY_PLAN_CONFLICT")
        self.assertEqual(got["errors"], [])
        self.assertEqual(got["expected_cases"]["execution_end_999"], False)
        self.assertEqual(got["expected_cases"]["effect_at_700"], True)

    def test_missing_each_negative_field_is_rejected(self):
        for key in ("execution_end_1000", "execution_end_1001", "effect_at_499", "effect_at_699"):
            with self.subTest(key=key):
                record = dict(BASE); record.pop(key)
                self.assertTrue(audit(record)["errors"])

    def test_null_and_string_negative_values_are_rejected(self):
        for bad in (None, "true"):
            for key in ("execution_end_1000", "execution_end_1001", "effect_at_499", "effect_at_699"):
                with self.subTest(key=key, bad=bad):
                    record = dict(BASE); record[key] = bad
                    self.assertTrue(audit(record)["errors"])

    def test_unexpected_key_is_rejected(self):
        record = dict(BASE); record["extra"] = False
        self.assertIn("required_key_set_mismatch", audit(record)["errors"])

    def test_boolean_is_not_accepted_as_integer_and_integer_not_as_boolean(self):
        record = dict(BASE); record["execution_end_1000"] = 1
        self.assertIn("non_boolean:execution_end_1000", audit(record)["errors"])

    def test_each_accepted_temporal_case_must_match_integer_inequality(self):
        for key in ("execution_end_700", "execution_end_999", "execution_end_1000", "execution_end_1001",
                    "effect_at_499", "effect_at_699", "effect_at_700", "effect_at_701"):
            with self.subTest(key=key):
                record = dict(BASE); record[key] = False
                self.assertIn("outcome_mismatches_timestamp_or_identity:" + key, audit(record)["errors"])

    def test_identity_negative_must_remain_refused(self):
        self.assertFalse(BASE["execution_wrong_command"])
        record = dict(BASE); record["execution_wrong_command"] = True
        self.assertIn("outcome_mismatches_timestamp_or_identity:execution_wrong_command", audit(record)["errors"])

    def test_non_object_is_rejected(self):
        for value in (None, [], "record"):
            self.assertEqual(audit(value)["disposition"], "HOLD_SCHEMA")

if __name__ == "__main__":
    unittest.main()
