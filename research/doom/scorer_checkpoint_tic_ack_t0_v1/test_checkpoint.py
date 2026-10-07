import unittest

from candidate import audit_refresh


class CheckpointTicAckTests(unittest.TestCase):
    def row(self, before=10, after=11, after_read=11, status="REFRESH_RETURNED_RUNTIME_QUALIFICATION_PENDING"):
        return {"status": status, "tic_before": before, "tic_after": after, "tic_after_read": after_read}

    def test_exactly_one_acknowledged_tic_and_stable_score_read_qualifies(self):
        self.assertEqual(audit_refresh(self.row()), {"qualified": True, "reason": "one_tic_acknowledged_and_read_stable"})

    def test_no_op_refresh_is_not_qualified(self):
        self.assertEqual(audit_refresh(self.row(after=10, after_read=10)), {"qualified": False, "reason": "tic_did_not_advance_exactly_one"})

    def test_multiple_tics_are_not_qualified(self):
        self.assertEqual(audit_refresh(self.row(after=12, after_read=12)), {"qualified": False, "reason": "tic_did_not_advance_exactly_one"})

    def test_tic_change_during_score_read_is_not_qualified(self):
        self.assertEqual(audit_refresh(self.row(after_read=12)), {"qualified": False, "reason": "tic_changed_during_score_read"})

    def test_missing_ack_fields_fail_closed(self):
        self.assertEqual(audit_refresh({"status": "REFRESH_RETURNED_RUNTIME_QUALIFICATION_PENDING"}), {"qualified": False, "reason": "missing_or_invalid_tic_ack"})

    def test_helper_status_alone_does_not_qualify(self):
        self.assertEqual(audit_refresh({"status": "REFRESH_RETURNED_RUNTIME_QUALIFICATION_PENDING"}), {"qualified": False, "reason": "missing_or_invalid_tic_ack"})


if __name__ == "__main__":
    unittest.main()
