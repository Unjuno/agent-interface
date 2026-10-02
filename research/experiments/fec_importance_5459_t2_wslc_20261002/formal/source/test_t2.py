import copy
import unittest

from auditor import audit_raw
from candidate import ARMS, build_raw, simulate_trace


class ImportanceT2Tests(unittest.TestCase):
    def test_preregistered_grid_and_audit(self):
        raw = build_raw()
        self.assertEqual(len(raw["trace_runs"]), 256 * 4 * len(ARMS))
        self.assertEqual(len(raw["fault_runs"]), 7 * len(ARMS))
        self.assertEqual(audit_raw(raw), [])

    def test_unequal_repair_recovers_scattered_mandatory_pair(self):
        loss = (1 << 0) | (1 << 5)
        equal = simulate_trace(loss, 0, 0, 0, "equal_repair")
        unequal = simulate_trace(loss, 0, 0, 0, "unequal_repair")
        self.assertNotEqual(equal["decisions"]["status"]["state"], "ELIGIBLE")
        self.assertEqual(unequal["decisions"]["status"]["state"], "ELIGIBLE")

    def test_priority_retransmit_schedules_mandatory_before_optional(self):
        loss = (1 << 3) | (1 << 5)
        raw_all = simulate_trace(loss, 0, 0, 0b10, "raw_all_retransmit")
        prioritized = simulate_trace(loss, 0, 0, 0b10, "mandatory_first_retransmit")
        self.assertEqual(raw_all["extra_schedule"][0]["symbol_id"], 3)
        self.assertEqual(prioritized["extra_schedule"][0]["symbol_id"], 5)
        self.assertLess(prioritized["decisions"]["status"]["round"],
                        raw_all["decisions"]["status"]["round"])

    def test_optional_fields_never_implied_by_limited_status(self):
        row = simulate_trace((1 << 1) | (1 << 3) | (1 << 4) | (1 << 6), 0, 0, 0,
                             "mandatory_first_retransmit")
        self.assertEqual(row["decisions"]["status"]["state"], "ELIGIBLE")
        self.assertNotEqual(row["decisions"]["detail"]["state"], "ELIGIBLE")
        self.assertNotEqual(row["whole_window_state"], "COMPLETE")

    def test_malformed_importance_falls_back_without_changing_closure(self):
        for fault in ("importance_missing", "critical_mislabeled_optional"):
            for arm in ARMS:
                row = simulate_trace(0, 0, 0, 0, arm, fault=fault)
                self.assertTrue(row["priority_fallback"] if fault == "importance_missing" else True)
                for decision in row["decisions"].values():
                    if decision["state"] == "ELIGIBLE":
                        self.assertEqual(set(decision["required_ids"]),
                                         set(row["decision_contract"][decision["name"]]))

    def test_auditor_rejects_forged_receipt_and_policy_schedule(self):
        raw = build_raw()
        changed = copy.deepcopy(raw)
        row = next(row for row in changed["trace_runs"]
                   if row["decisions"]["detail"]["state"] != "ELIGIBLE")
        row["decisions"]["detail"]["state"] = "ELIGIBLE"
        self.assertTrue(audit_raw(changed))

        changed = copy.deepcopy(raw)
        row = next(row for row in changed["trace_runs"]
                   if row["extra_schedule"])
        row["extra_schedule"][0]["slot"] = 99
        self.assertTrue(audit_raw(changed))

    def test_auditor_rejects_tampered_equation_and_budget(self):
        raw = build_raw()
        changed = copy.deepcopy(raw)
        changed["trace_runs"][0]["packets"][0]["value"] ^= 1
        self.assertTrue(audit_raw(changed))

        changed = copy.deepcopy(raw)
        changed["trace_runs"][0]["packets"].extend(copy.deepcopy(changed["trace_runs"][0]["packets"][:1]))
        self.assertTrue(audit_raw(changed))


if __name__ == "__main__":
    unittest.main(verbosity=2)
