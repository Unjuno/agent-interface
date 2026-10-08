"""Finite controls for strict temporal receipt audit adjudication."""
import unittest

from audit import REQUIRED_KEYS, adjudicate, mutate_one


BOUNDARY = {"effect_at_700_plan_case": "reject",
            "effect_at_700_plan_note": "causally eligible",
            "effect_at_700_legacy_audit_expected": True,
            "lease_deadline_semantics": "exclusive"}


def complete_control():
    values = {key: False for key in REQUIRED_KEYS}
    values.update({"execution_end_700": True, "execution_end_999": True,
                   "effect_at_700": True, "effect_at_701": True,
                   "effect_at_900": True})
    return values


class StrictAuditTests(unittest.TestCase):
    def test_complete_typed_record_still_holds_on_explicit_plan_conflict(self):
        record = complete_control()
        result = adjudicate(record, list(record), BOUNDARY)
        self.assertEqual(result["disposition"], "HOLD_CONTRACT_AMBIGUITY")

    def test_original_record_holds_for_missing_plan_baseline(self):
        record = {key: False for key in REQUIRED_KEYS if key != "effect_at_900"}
        record.update({"execution_end_700": True, "execution_end_999": True,
                       "execution_end_1000": True, "execution_end_1001": True,
                       "effect_at_499": True, "effect_at_699": True,
                       "effect_at_700": True, "effect_at_701": True,
                       "execution_wrong_command": False})
        result = adjudicate(record, list(record), BOUNDARY)
        self.assertEqual(result["disposition"], "HOLD_SCHEMA")
        self.assertEqual(result["missing"], ["effect_at_900"])

    def test_each_required_case_rejects_missing_null_string_and_integer(self):
        base = complete_control()
        for key in sorted(REQUIRED_KEYS):
            for mode in ("missing", "null", "string", "integer"):
                with self.subTest(key=key, mode=mode):
                    mutated, observed = mutate_one(base, key, mode)
                    result = adjudicate(mutated, observed, BOUNDARY)
                    self.assertEqual(result["disposition"], "HOLD_SCHEMA")

    def test_effect_at_900_added_to_original_without_source_inventory_holds(self):
        original = {key: False for key in REQUIRED_KEYS if key != "effect_at_900"}
        original["effect_at_900"] = True
        frozen_inventory = sorted(REQUIRED_KEYS - {"effect_at_900"})
        result = adjudicate(original, frozen_inventory, BOUNDARY)
        self.assertEqual(result["disposition"], "HOLD_SCHEMA")
        self.assertIn("record_keys_differ_from_frozen_observation_inventory",
                      result["errors"])

    def test_boundary_label_or_expected_value_drift_holds(self):
        record = complete_control()
        mutated_contract = dict(BOUNDARY, effect_at_700_legacy_audit_expected=False)
        result = adjudicate(record, list(record), mutated_contract)
        self.assertEqual(result["disposition"], "HOLD_BOUNDARY_CONFIGURATION")


if __name__ == "__main__":
    unittest.main()
