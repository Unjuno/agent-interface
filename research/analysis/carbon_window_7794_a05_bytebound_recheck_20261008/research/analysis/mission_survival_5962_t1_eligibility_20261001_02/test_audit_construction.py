import json
import tarfile
import unittest
import audit_sessions


MANIFEST = "manifest.json"
ARCHIVE = "raw.tar.gz"


class EligibilityAuditConstruction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = audit_sessions.audit(MANIFEST, ARCHIVE)

    def test_archive_manifest_covers_every_member(self):
        self.assertEqual(self.result["integrity"]["members_verified"], 1051)
        self.assertEqual(self.result["integrity"]["member_errors"], 0)

    def test_current_pair_has_ordered_complete_descriptive_outcomes(self):
        current = self.result["campaigns"][0]
        self.assertEqual(current["route_order"], ["direct", "guarded"])
        for route in current["routes"].values():
            self.assertTrue(route["six_task_order_complete"])
            self.assertTrue(route["effect_oracle_complete_exact_once"])
            self.assertTrue(route["task_phases_show_carryover"])

    def test_prior_stop_and_interruption_are_not_dropped_or_filled(self):
        interrupted = self.result["campaigns"][1]["routes"]["guarded"]
        self.assertEqual(interrupted["effect_oracle_record_count"], 3)
        self.assertEqual(interrupted["effect_oracle_missing"], ["task-4", "task-5", "task-6"])
        stopped = self.result["campaigns"][2]["routes"]["direct"]
        self.assertEqual(stopped["effect_oracle_record_count"], 0)
        self.assertFalse(self.result["campaigns"][2]["routes"]["guarded"]["allocation_present"])

    def test_no_comparable_route_cohort_is_admitted(self):
        classification = self.result["classification"]
        self.assertFalse(classification["current_pair_has_explicit_stable_session_ids"])
        self.assertFalse(classification["current_pair_has_explicit_reset_boundary"])
        self.assertFalse(classification["t2_route_ranking_eligible"])
        self.assertEqual(classification["disposition"], "HOLD_T2_NO_COMPARABLE_SESSION_COHORT")


if __name__ == "__main__":
    unittest.main()
