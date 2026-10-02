import unittest

from audit_raw import audit


def valid():
    return [
        {"event": "fixture", "scope": "host-real-Lease-synthetic-clock"},
        {"event": "case_start", "case": "cancel_before_deadline", "now_ns": 100, "deadline_ns": 1000},
        {"event": "cancel_set", "case": "cancel_before_deadline", "now_ns": 100},
        {"event": "wait_return", "case": "cancel_before_deadline", "now_ns": 100, "cancel_ack": True},
        {"event": "worker_terminal", "case": "cancel_before_deadline", "now_ns": 100, "status": "cancelled"},
        {"event": "case_start", "case": "deadline_without_cancel", "now_ns": 100, "deadline_ns": 1000},
        {"event": "wait_expired", "case": "deadline_without_cancel", "now_ns": 1000},
        {"event": "worker_terminal", "case": "deadline_without_cancel", "now_ns": 1000, "status": "expired"},
        {"event": "case_start", "case": "cancel_at_deadline", "now_ns": 100, "deadline_ns": 1000},
        {"event": "cancel_set", "case": "cancel_at_deadline", "now_ns": 1000},
        {"event": "wait_expired", "case": "cancel_at_deadline", "now_ns": 1000},
        {"event": "worker_terminal", "case": "cancel_at_deadline", "now_ns": 1000, "status": "expired"},
    ]


class ContractTests(unittest.TestCase):
    def test_accepts_declared_trace(self):
        self.assertEqual(audit(valid())["decision"], "PASS_LEASE_CANCEL_ACK_CONTRACT_SCOPED")

    def test_rejects_ignored_cancel_ack(self):
        rows = valid(); rows[4]["status"] = "continued"
        self.assertTrue(audit(rows)["errors"])

    def test_rejects_false_ack(self):
        rows = valid(); rows[3]["cancel_ack"] = False
        self.assertTrue(audit(rows)["errors"])

    def test_rejects_expiry_as_cancel(self):
        rows = valid(); rows[-1]["status"] = "cancelled"
        self.assertTrue(audit(rows)["errors"])

    def test_rejects_predeadline_case_moved_to_deadline(self):
        rows = valid(); rows[2]["now_ns"] = 1000
        self.assertTrue(audit(rows)["errors"])

    def test_rejects_missing_worker_terminal(self):
        rows = valid()[:-1]
        self.assertTrue(audit(rows)["errors"])

    def test_rejects_event_reorder(self):
        rows = valid(); rows[2], rows[3] = rows[3], rows[2]
        self.assertTrue(audit(rows)["errors"])

    def test_rejects_wrong_scope(self):
        rows = valid(); rows[0]["scope"] = "live"
        self.assertTrue(audit(rows)["errors"])


if __name__ == "__main__":
    unittest.main()
