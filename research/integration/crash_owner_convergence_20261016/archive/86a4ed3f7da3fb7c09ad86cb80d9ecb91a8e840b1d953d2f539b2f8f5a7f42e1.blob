import importlib.util
from pathlib import Path
import time
import unittest


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "candidate", Path(__file__).with_name("candidate.py"))
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)
audit_spec = importlib.util.spec_from_file_location(
    "audit_a06", Path(__file__).with_name("audit_a06.py"))
audit_a06 = importlib.util.module_from_spec(audit_spec)
audit_spec.loader.exec_module(audit_a06)


def valid_raw():
    release = {"event": "owner_release", "reason": "close",
               "intent_token": "a06-intent-1", "valid_until_ns": 6000,
               "verified": True, "keys_down": [], "buttons_down": [],
               "keys_unknown": [], "key_state_errors": [],
               "key_release_attempts": {"38": {"verified": True,
                   "attempts": [{"server_key_down_after": False}]}}}
    admission = {"event": "input_admission", "key": "a", "keycode": 38,
                 "valid_until_ns": 6000, "admitted_ns": 850,
                 "input_ack_ns": 900}
    return {
        "session": {"pid": 100, "returncode": -9, "kill_requested_ns": 1000,
                    "killed_by_sigkill": True},
        "owner": {"pid": 101, "session_pid_at_start": 100,
                  "ppid_at_eof": 50, "eof_ns": 1200,
                  "close_started_ns": 1300, "close_finished_ns": 1400,
                  "owner_id": "owner-1", "intent_token": "a06-intent-1",
                  "expected_focus": 42, "admitted": admission,
                  "owner_records": [release], "release_record_count": 1,
                  "release_record": release, "close_error": None,
                  "thread_stopped": True, "returncode": 0,
                  "forced_kill": False, "receipt_fsynced": True},
        "observer": {"key_press_ns": 950, "key_release_ns": 1500,
                     "keymap_down_before_kill": True,
                     "keymap_up_after_release": True},
        "xvfb": {"returncode": 0},
    }


class ProtocolTests(unittest.TestCase):
    def request(self, **updates):
        request = {
            "schema": "input-owner-rpc-v1",
            "op": "down",
            "key": "a",
            "deadline_ns": time.perf_counter_ns() + 5_000_000_000,
            "intent_token": "a06-intent-1",
            "expected_focus": 42,
        }
        request.update(updates)
        return request

    def test_valid_request_reconstructs_current_lease_semantics(self):
        request = self.request()
        lease, key = candidate.decode_down_request(request)
        self.assertEqual(key, "a")
        self.assertEqual(lease.deadline, request["deadline_ns"])
        self.assertEqual(lease.intent_token, "a06-intent-1")
        self.assertEqual(lease.expected_focus, 42)
        lease.check()

    def test_extra_fields_are_rejected(self):
        request = self.request(untrusted_command="xterm")
        with self.assertRaisesRegex(ValueError, "exact request fields"):
            candidate.decode_down_request(request)

    def test_non_allowlisted_key_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "key not allowlisted"):
            candidate.decode_down_request(self.request(key="space"))

    def test_expired_deadline_is_rejected_before_owner_call(self):
        with self.assertRaisesRegex(ValueError, "deadline expired"):
            candidate.decode_down_request(self.request(deadline_ns=time.perf_counter_ns() - 1))

    def test_missing_or_invalid_observed_focus_is_rejected(self):
        request = self.request(expected_focus=1)
        with self.assertRaisesRegex(ValueError, "observed focus"):
            candidate.decode_down_request(request)

    def test_complete_real_owner_recovery_record_passes(self):
        self.assertEqual(audit_a06.audit(valid_raw()), [])

    def test_unverified_owner_release_is_rejected(self):
        raw = valid_raw()
        raw["owner"]["release_record"]["verified"] = False
        self.assertIn("InputOwner release record did not verify empty state",
                      audit_a06.audit(raw))

    def test_mismatched_intent_receipt_is_rejected(self):
        raw = valid_raw()
        raw["owner"]["release_record"]["intent_token"] = "different-intent"
        self.assertIn("release receipt intent/deadline mismatch",
                      audit_a06.audit(raw))


if __name__ == "__main__":
    unittest.main()
