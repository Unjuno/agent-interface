import copy
import unittest

try:
    from .audit import EXPECTED, check
except ImportError:
    from audit import EXPECTED, check


def valid_rows():
    rows = []
    for index, policy, rep in EXPECTED:
        stale = policy != "CURRENT_FRESH_MAP"
        emitted = [] if policy == "SNAPSHOT_REFUSE_ON_CHANGE" else [
            {"type": "KeyPress", "detail": 37}, {"type": "KeyPress", "detail": 52 if stale else 29},
            {"type": "KeyRelease", "detail": 52 if stale else 29}, {"type": "KeyRelease", "detail": 37}]
        observed = copy.deepcopy(emitted)
        rows.append({"spec": {"index": index, "policy": policy, "rep": rep}, "error": None,
                     "mapping": {"server_changed": True, "retained_map_stale": True,
                                 "retained_z_keycode": 52, "fresh_z_keycode": 29,
                                 "control_keycode": 37},
                     "decision": "REFUSE_STALE_MAP" if not emitted else "EMIT",
                     "emission_requests": emitted, "server_events": observed,
                     "key_state_after_request": [] if not emitted else [
                         {"target_down": True, "control_down": True},
                         {"target_down": True, "control_down": True},
                         {"target_down": False, "control_down": True},
                         {"target_down": False, "control_down": False}],
                     "terminal_state": {"neutral": True}, "socket_absent_after_cleanup": True,
                     "auth_file_absent_after_cleanup": True,
                     "process_receipts": {"xvfb_reaped": True, "xvfb_exit": -15}})
    return rows


class AuditGateTests(unittest.TestCase):
    def test_complete_schedule(self):
        self.assertEqual(check(valid_rows()), [])

    def test_missing_row_rejected(self):
        self.assertIn("row_count", check(valid_rows()[:-1]))

    def test_stale_snapshot_must_not_emit(self):
        rows = valid_rows()
        rows[1]["emission_requests"] = [{"type": "KeyPress"}]
        self.assertIn("snapshot_not_fail_closed", check(rows))

    def test_current_map_must_emit_fresh_code(self):
        rows = valid_rows()
        rows[2]["emission_requests"][1]["detail"] = 52
        self.assertIn("emission_sequence", check(rows))

    def test_terminal_release_required(self):
        rows = valid_rows()
        rows[0]["terminal_state"]["neutral"] = False
        self.assertIn("terminal_not_neutral", check(rows))

    def test_cleanup_required(self):
        rows = valid_rows()
        rows[0]["auth_file_absent_after_cleanup"] = False
        self.assertIn("cleanup_incomplete", check(rows))

    def test_request_state_not_event_presentation_is_authoritative(self):
        rows = valid_rows()
        rows[0]["server_events"] = [
            {"type": kind, "detail": detail} for kind, detail in
            [("KeyRelease", 37), ("KeyPress", 37), ("KeyRelease", 52), ("KeyPress", 52),
             ("KeyRelease", 52), ("KeyRelease", 37)]]
        self.assertEqual(check(rows), [])

    def test_unbalanced_server_state_rejected(self):
        rows = valid_rows()
        rows[0]["key_state_after_request"][2]["target_down"] = True
        self.assertIn("target_state_transition", check(rows))


if __name__ == "__main__":
    unittest.main()
