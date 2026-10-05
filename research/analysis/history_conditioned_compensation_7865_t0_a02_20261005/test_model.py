import unittest

import model
import oracle


class CompensationHistoryTests(unittest.TestCase):
    def test_independent_oracle_reconstructs_every_policy_trace(self):
        results = model.all_results()
        self.assertEqual(28, oracle.assert_matches(results))

    def test_blind_inverse_loses_the_disjoint_external_write(self):
        blind = model.decide(model.trace("disjoint"), "BLIND_INVERSE")
        guarded = model.decide(
            model.trace("disjoint"), "FIELD_SCOPED_COMPARE_AND_COMPENSATE")
        self.assertEqual("x", model.trace("disjoint")["state"]["fields"]["body"])
        self.assertEqual("x", blind["state"]["fields"]["body"])
        self.assertEqual("y", guarded["state"]["fields"]["body"])

    def test_field_policy_is_strictly_more_selective_on_disjoint_write(self):
        case = model.trace("disjoint")
        object_guard = model.decide(case, "WHOLE_OBJECT_VERSION_GUARD")
        field_guard = model.decide(
            case, "FIELD_SCOPED_COMPARE_AND_COMPENSATE")
        self.assertFalse(object_guard["wrote"])
        self.assertTrue(field_guard["wrote"])

    def test_conflict_and_unidentifiable_histories_fail_closed(self):
        for name in ("same_field", "aba", "replacement", "unknown",
                     "out_of_order"):
            result = model.decide(
                model.trace(name), "FIELD_SCOPED_COMPARE_AND_COMPENSATE")
            self.assertEqual("CONFLICT_OR_HOLD", result["disposition"], name)
            self.assertFalse(result["wrote"], name)

    def test_compensation_never_claims_literal_rollback(self):
        for row in model.all_results().values():
            for result in row.values():
                self.assertFalse(result["literal_rollback"])

    def test_revision_corruption_is_rejected_by_independent_oracle(self):
        results = model.all_results()
        results["aba"]["FIELD_SCOPED_COMPARE_AND_COMPENSATE"] = model.decide(
            model.trace("none"), "FIELD_SCOPED_COMPARE_AND_COMPENSATE")
        with self.assertRaises(AssertionError):
            oracle.assert_matches(results)

    def test_footprint_corruption_is_rejected_by_independent_oracle(self):
        results = model.all_results()
        results["disjoint"]["FIELD_SCOPED_COMPARE_AND_COMPENSATE"] = model.decide(
            model.trace("same_field"), "FIELD_SCOPED_COMPARE_AND_COMPENSATE")
        with self.assertRaises(AssertionError):
            oracle.assert_matches(results)


if __name__ == "__main__":
    unittest.main(verbosity=2)
