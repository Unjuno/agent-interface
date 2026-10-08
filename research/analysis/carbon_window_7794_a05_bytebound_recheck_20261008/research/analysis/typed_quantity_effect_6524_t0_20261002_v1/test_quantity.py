import unittest

from candidate import load_fixture, run_candidate
from auditor import audit, corrupt


class TypedQuantityConstructionTests(unittest.TestCase):
    def test_fixture_has_eleven_frozen_quantity_boundaries(self):
        cases = load_fixture()["cases"]
        self.assertEqual(len(cases), 11)
        self.assertEqual(len({case["id"] for case in cases}), 11)

    def test_correct_conversion_and_bounded_rounding_are_accepted(self):
        rows = {row["case_id"]: row for row in run_candidate(load_fixture())}
        self.assertEqual(rows["equivalent_cm_to_m"]["typed_status"], "PASS")
        self.assertEqual(rows["rounding_within_tolerance"]["typed_status"], "PASS")
        self.assertFalse(rows["equivalent_cm_to_m"]["bare_number_pass"])

    def test_bare_number_false_positive_is_rejected_by_typed_oracle(self):
        rows = {row["case_id"]: row for row in run_candidate(load_fixture())}
        for case_id in ("same_number_wrong_unit", "wrong_dimension_same_numeral",
                        "wrong_kind_same_dimension"):
            self.assertTrue(rows[case_id]["bare_number_pass"])
            self.assertNotEqual(rows[case_id]["typed_status"], "PASS")
        self.assertEqual(rows["wrong_kind_same_dimension"]["typed_status"], "WRONG_KIND")

    def test_state_and_effect_failures_are_not_normalized_to_pass(self):
        rows = {row["case_id"]: row for row in run_candidate(load_fixture())}
        self.assertEqual(rows["selector_switched_after_entry"]["typed_status"], "WRONG_MAGNITUDE")
        self.assertEqual(rows["rounding_outside_tolerance"]["typed_status"], "WRONG_MAGNITUDE")
        self.assertEqual(rows["no_effect_existing_value"]["typed_status"], "NO_EFFECT")
        self.assertEqual(rows["duplicate_effect"]["typed_status"], "WRONG_EFFECT_COUNT")

    def test_unknown_conversion_and_rounding_remain_unknown(self):
        rows = {row["case_id"]: row for row in run_candidate(load_fixture())}
        self.assertEqual(rows["unknown_unit"]["typed_status"], "UNKNOWN_CONVERSION")
        self.assertEqual(rows["unknown_rounding"]["typed_status"], "UNKNOWN_ROUNDING")

    def test_independent_raw_audit_reconstructs_candidate(self):
        fixture = load_fixture()
        raw = run_candidate(fixture)
        report = audit(raw, fixture)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["case_count"], 11)
        self.assertEqual(report["typed_passes"], 2)
        self.assertEqual(report["bare_number_false_positives"], 6)

    def test_all_nine_copied_output_mutations_are_effective_and_rejected(self):
        fixture = load_fixture()
        raw = run_candidate(fixture)
        for field in ("case_id", "bare_number_pass", "typed_status", "persisted_value",
                      "persisted_unit", "persisted_dimension", "persisted_kind",
                      "effect_count", "effect_id"):
            changed = corrupt(raw, field)
            self.assertNotEqual(changed, raw)
            self.assertTrue(audit(changed, fixture)["errors"], field)


if __name__ == "__main__":
    unittest.main()
