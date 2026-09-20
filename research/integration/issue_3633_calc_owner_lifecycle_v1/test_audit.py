import copy
import unittest

from audit import classify, digest


def passing_raw():
    return {
        "allocation_id": "issue3644-calc-owner-lifecycle-formal-01",
        "decision": "PASS_PRIVATE_PROCESS_GROUP_CLEANUP_SCOPED",
        "operations": {"geometry": 0, "focus": 0, "input": 0,
                       "model": 0, "network": 0},
        "audit_unit_tests": {"returncode": 0, "stderr": "Ran 6 tests"},
        "launch": {"pgid_expected": 100, "reaped": True},
        "window_owner": {"xid": 500, "proc": {"pid": 101,
                           "start_ticks": "777", "pgid": 100, "sid": 100}},
        "group_members_before": [{"pid": 100, "start_ticks": "700"},
                                 {"pid": 101, "start_ticks": "777"}],
        "termination": {"attempts": 1},
        "samples_after": [{"group_members": [],
                           "owner_same_identity_alive": False,
                           "xid_visible": False}],
        "sentinel": {"alive_after_group_signal": True, "reaped": True},
        "cleanup": {"xvfb_returncode": -15, "xvfb_reaped": True,
                    "x_socket_absent": True},
    }


class LifecycleAuditTests(unittest.TestCase):
    def test_accepts_complete_private_group_cleanup(self):
        self.assertEqual(classify(passing_raw()),
                         "PASS_PRIVATE_PROCESS_GROUP_CLEANUP_SCOPED")

    def test_forged_owner_group_fails_closed(self):
        raw = passing_raw()
        raw["window_owner"]["proc"]["pgid"] = 999
        self.assertNotEqual(classify(raw), "PASS_PRIVATE_PROCESS_GROUP_CLEANUP_SCOPED")

    def test_retained_owner_or_xid_fails_closed(self):
        raw = passing_raw()
        raw["samples_after"][-1]["owner_same_identity_alive"] = True
        self.assertEqual(classify(raw), "FAIL_PROCESS_GROUP_CLEANUP")
        raw = passing_raw()
        raw["samples_after"][-1]["xid_visible"] = True
        self.assertEqual(classify(raw), "FAIL_PROCESS_GROUP_CLEANUP")

    def test_sentinel_interference_fails_closed(self):
        raw = passing_raw()
        raw["sentinel"]["alive_after_group_signal"] = False
        self.assertEqual(classify(raw), "FAIL_PROCESS_GROUP_CLEANUP")

    def test_incomplete_reaping_or_socket_evidence_holds(self):
        raw = passing_raw()
        raw["launch"]["reaped"] = False
        self.assertEqual(classify(raw), "HOLD_PROCESS_OWNERSHIP_UNRESOLVED")
        raw = passing_raw()
        raw["cleanup"]["x_socket_absent"] = False
        self.assertEqual(classify(raw), "HOLD_PROCESS_OWNERSHIP_UNRESOLVED")

    def test_raw_digest_covers_lifecycle_fields(self):
        raw = passing_raw()
        claimed = digest(raw)
        altered = copy.deepcopy(raw)
        altered["window_owner"]["xid"] = 501
        self.assertNotEqual(claimed, digest(altered))


if __name__ == "__main__":
    unittest.main()
