import copy
import unittest

import auditor
import candidate


class VersionDefinedInterventionT0(unittest.TestCase):
    def test_equal_effect_negative_control(self):
        estimates = candidate.summarize(candidate.build_case(equal_effect=True))
        self.assertEqual(estimates["0"]["pooled"], estimates["0"]["standardized"])

    def test_version_mixture_changes_pooled_estimand(self):
        estimates = candidate.summarize(candidate.build_case(equal_effect=False))
        self.assertNotEqual(estimates["0"]["pooled"], estimates["0"]["standardized"])

    def test_infeasible_cell_excluded_from_common_support(self):
        estimates = candidate.summarize(candidate.build_case(equal_effect=False))
        self.assertNotIn(["a2", "b2"], estimates["1"]["common_version_cells"])

    def test_auditor_reconstructs_candidate(self):
        for equal in (True, False):
            rows = candidate.build_case(equal_effect=equal)
            self.assertEqual(candidate.summarize(rows), auditor.audit_rows(rows, equal_effect=equal))

    def test_mutations_rejected_or_unknown(self):
        original = candidate.build_case(equal_effect=False)
        # (1) A silent version relabel creates a duplicated cell and must be rejected.
        relabel = copy.deepcopy(original)
        relabel[0]["a_version"] = "a2"
        with self.assertRaises(ValueError):
            auditor.audit_rows(relabel)
        # (2) Dropping a failed-attempt receipt must be rejected, not disappear silently.
        dropped = [r for r in original if r["row_id"] != "missing-attempt"]
        with self.assertRaises(ValueError):
            auditor.audit_rows(dropped)
        # (3) Alter one coalition's version mix changes the estimated sample and is
        # detected by disagreement with the candidate's frozen estimate.
        altered = copy.deepcopy(original)
        row = next(r for r in altered if r["a_on"] == 1 and r["b_on"] == 0 and r["a_version"] == "a1")
        row["a_version"] = "a2"
        with self.assertRaises(ValueError):
            auditor.audit_rows(altered)
        # (4) Imputing an outcome into the declared structural zero is rejected.
        imputed = copy.deepcopy(original)
        zero = next(r for r in imputed if r["row_id"] == "structural-zero")
        zero.update(feasible=True, task_effect=23, safety_event=1, attempt_status="OBSERVED")
        with self.assertRaises(ValueError):
            auditor.audit_rows(imputed)
        # (5) Scalarizing safety by overwriting the task outcome is detected against
        # the frozen candidate value while the safety field remains independent.
        scalarized = copy.deepcopy(original)
        target = next(r for r in scalarized if r["attempt_status"] == "OBSERVED" and r["safety_event"] == 1)
        target["task_effect"] = target["safety_event"]
        with self.assertRaises(ValueError):
            auditor.audit_rows(scalarized, equal_effect=False)


if __name__ == "__main__":
    unittest.main()
