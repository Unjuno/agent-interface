import unittest

from .audit import audit_record


def record():
    healthy = {"case": "healthy", "final_down": [], "final_ledger": {},
               "release": {"verified": True}}
    same = {"case": "same_connection_sync_block",
            "before_resume": {"writer_alive": True, "release_alive": True,
                              "release_returned": False},
            "final_down": [], "server_events": [
                {"phase": "apply", "kind": 2}, {"phase": "apply", "kind": 3}]}
    separate = lambda name: {"case": name,
        "before_resume": {"release_returned": True,
                          "release": {"verified": True}, "server_down": []},
        "final_down": [37], "final_ledger": {},
        "server_events": [{"phase": "apply", "connection": "control", "kind": 3},
                          {"phase": "apply", "connection": "writer", "kind": 2}]}
    stopped = {"case": "server_wide_stop",
               "before_resume": {"release_returned": False, "release_alive": True,
                                 "server_down": [37]},
               "final_down": [], "writer_outcomes": [{"verified": True}]}
    rows = [healthy, same, separate("separate_up_before_send"),
            separate("separate_up_before_sync"), stopped]
    return {"schema": "fake-x-release-order-a01-v1", "rows": rows}


class ReleaseOrderAuditTests(unittest.TestCase):
    def test_accepts_expected_counterexample_schedule(self):
        result = audit_record(record())
        self.assertEqual(result["false_clear_cases"], 2)

    def test_rejects_mutated_late_press_state(self):
        row = record()
        next(item for item in row["rows"] if item["case"] == "separate_up_before_send")["final_down"] = []
        with self.assertRaises(AssertionError):
            audit_record(row)

    def test_rejects_fabricated_same_connection_progress(self):
        row = record()
        next(item for item in row["rows"] if item["case"] == "same_connection_sync_block")["before_resume"]["release_returned"] = True
        with self.assertRaises(AssertionError):
            audit_record(row)

    def test_rejects_missing_boundary(self):
        row = record()
        row["rows"] = row["rows"][:-1]
        with self.assertRaises(AssertionError):
            audit_record(row)


if __name__ == "__main__":
    unittest.main()
