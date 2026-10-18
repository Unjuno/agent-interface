import unittest
from dataclasses import replace

from experiment import frozen_cycles, summarize
from audit import audit, audit_split, CALIBRATION_IDS, EVALUATION_IDS


class ImperfectRepairMethodTests(unittest.TestCase):
    def test_all_three_repair_operators_are_distinguishable(self):
        rows = frozen_cycles()
        ok, reason = audit(rows)
        self.assertTrue(ok, reason)
        post = summarize(rows)["repair_post_ages"]
        self.assertEqual((post["p1"], post["m1"], post["i1"]), (0, 2, 1))

    def test_unequal_exposure_is_preserved(self):
        rows = frozen_cycles()
        self.assertEqual(sum(r.exposure for r in rows), 12)
        self.assertTrue(audit(rows)[0])
        altered = [replace(r, exposure=r.exposure + 1) if r.cycle_id == "i1" else r
                   for r in rows]
        self.assertEqual(audit(altered), (False, "frozen_input_or_exposure_mismatch"))

    def test_fault_class_relabeling_is_rejected(self):
        rows = frozen_cycles()
        changed = [replace(r, fault_class="other_fault") if r.cycle_id == "m0" else r
                   for r in rows]
        self.assertEqual(audit(changed), (False, "frozen_input_or_exposure_mismatch"))

    def test_evaluation_outcome_leakage_into_calibration_is_rejected(self):
        leaked = tuple(CALIBRATION_IDS) + ("i1",)
        self.assertEqual(audit_split(leaked, tuple(EVALUATION_IDS)),
                         (False, "outcome_leaked_into_calibration"))
        self.assertTrue(audit_split(tuple(CALIBRATION_IDS), tuple(EVALUATION_IDS))[0])

    def test_reset_cannot_erase_required_task_effect(self):
        rows = frozen_cycles()
        changed = [replace(r, retained_effects=()) if r.cycle_id == "p1" else r
                   for r in rows]
        self.assertEqual(audit(changed), (False, "required_effect_erased"))

    def test_censored_recurrence_stays_unknown(self):
        rows = frozen_cycles()
        censored = next(r for r in rows if r.censored)
        self.assertIsNone(censored.observed_recurrence)
        changed = [replace(r, observed_recurrence=False) if r.cycle_id == "c0" else r
                   for r in rows]
        self.assertEqual(audit(changed), (False, "censored_outcome_filled_in"))

    def test_recurrence_is_recomputed_from_fixed_exposure_and_probe(self):
        rows = frozen_cycles()
        self.assertTrue(audit(rows)[0])
        changed = [replace(r, observed_recurrence=not r.observed_recurrence)
                   if r.cycle_id == "m1" else r for r in rows]
        self.assertEqual(audit(changed), (False, "recurrence_oracle_mismatch"))


if __name__ == "__main__":
    unittest.main()
