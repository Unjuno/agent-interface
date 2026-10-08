import copy
import json
import unittest
from pathlib import Path

import audit
import candidate

FIXTURE = json.loads((Path(__file__).parent / "fixture.json").read_text())
ROWS = candidate.replay(FIXTURE)


class CapacityConservationTests(unittest.TestCase):
    def test_all_fixed_groups_and_horizon_are_present(self):
        self.assertEqual(len(ROWS), 270)
        self.assertEqual(len({(r["case"], r["policy"]) for r in ROWS}), 9)

    def test_every_tick_satisfies_joint_shared_capacity(self):
        self.assertTrue(all(r["total_resource_used"] <= 4 for r in ROWS))
        self.assertTrue(all(r["total_resource_used"] == r["primary_service"] + r["retry_service"] + r["safety_service"] + r["failed_attempt_resource"] for r in ROWS))

    def test_synthetic_feedback_hypothesis_and_controls(self):
        result = audit.audit(FIXTURE, ROWS)
        self.assertEqual(result["status"], "PASS_METHOD_AND_HYPOTHESIS_SCOPED")
        legacy = [r for r in ROWS if r["case"] == "finite_fault_debt_feedback_on" and r["policy"] == "legacy_shared_retry"][-8:]
        self.assertTrue(all(r["safety_service"] == 0 and r["retry_after"] > 0 for r in legacy))

    def test_auditor_rejects_joint_capacity_violation(self):
        corrupt = copy.deepcopy(ROWS)
        row = next(r for r in corrupt if r["case"] == "underload_no_trigger" and r["policy"] == "legacy_shared_retry" and r["tick"] == 0)
        row["safety_service"] += 4
        row["safety_after"] -= 4
        row["total_resource_used"] += 4
        self.assertEqual(audit.audit(FIXTURE, corrupt)["status"], "FAIL_METHOD")

    def test_auditor_rejects_queue_nonconservation(self):
        corrupt = copy.deepcopy(ROWS)
        corrupt[0]["primary_after"] += 1
        self.assertEqual(audit.audit(FIXTURE, corrupt)["status"], "FAIL_METHOD")

    def test_auditor_rejects_authority_from_any_fallback(self):
        corrupt = copy.deepcopy(ROWS)
        corrupt[-1]["authority_admissions"] = 1
        self.assertEqual(audit.audit(FIXTURE, corrupt)["status"], "FAIL_METHOD")


if __name__ == "__main__":
    unittest.main()
