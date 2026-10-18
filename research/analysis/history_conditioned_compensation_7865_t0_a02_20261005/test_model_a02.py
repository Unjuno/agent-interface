import unittest

import model
import oracle


class CompensationHistoryA02Tests(unittest.TestCase):
    def test_independent_oracle_reconstructs_all_28_policy_trace_rows(self):
        self.assertEqual(28, oracle.assert_matches(model.all_results()))

    def test_blind_inverse_loses_disjoint_external_write(self):
        case = model.trace("disjoint")
        blind = model.decide(case, "BLIND_INVERSE")
        guarded = model.decide(case, "FIELD_SCOPED_COMPARE_AND_COMPENSATE")
        self.assertEqual("y", case["state"]["fields"]["body"])
        self.assertEqual("x", blind["state"]["fields"]["body"])
        self.assertEqual("y", guarded["state"]["fields"]["body"])

    def test_field_policy_is_more_selective_on_disjoint_write(self):
        case = model.trace("disjoint")
        whole = model.decide(case, "WHOLE_OBJECT_VERSION_GUARD")
        field = model.decide(case, "FIELD_SCOPED_COMPARE_AND_COMPENSATE")
        self.assertFalse(whole["wrote"])
        self.assertTrue(field["wrote"])

    def test_same_field_aba_replacement_unknown_and_reordered_fail_closed(self):
        for name in ("same_field", "aba", "replacement", "unknown",
                     "out_of_order"):
            result = model.decide(
                model.trace(name), "FIELD_SCOPED_COMPARE_AND_COMPENSATE")
            self.assertEqual("CONFLICT_OR_HOLD", result["disposition"], name)
            self.assertFalse(result["wrote"], name)

    def test_compensation_is_never_labelled_literal_rollback(self):
        for row in model.all_results().values():
            for result in row.values():
                self.assertFalse(result["literal_rollback"])

    def test_lost_aba_revision_is_detected_by_independent_oracle(self):
        rows = model.all_results()
        rows["aba"]["FIELD_SCOPED_COMPARE_AND_COMPENSATE"] = model.decide(
            model.trace("none"), "FIELD_SCOPED_COMPARE_AND_COMPENSATE")
        with self.assertRaises(AssertionError):
            oracle.assert_matches(rows)

    def test_corrupted_effect_footprint_is_detected_by_independent_oracle(self):
        rows = model.all_results()
        rows["disjoint"]["FIELD_SCOPED_COMPARE_AND_COMPENSATE"] = model.decide(
            model.trace("same_field"), "FIELD_SCOPED_COMPARE_AND_COMPENSATE")
        with self.assertRaises(AssertionError):
            oracle.assert_matches(rows)


if __name__ == "__main__":
    unittest.main(verbosity=2)
