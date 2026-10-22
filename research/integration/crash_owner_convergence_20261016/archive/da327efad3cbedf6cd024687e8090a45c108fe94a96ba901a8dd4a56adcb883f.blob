import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest


AUDITOR = Path(__file__).with_name("audit_raw.py")
spec = importlib.util.spec_from_file_location("audit_raw", AUDITOR)
audit_raw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_raw)
candidate_spec = importlib.util.spec_from_file_location(
    "candidate", Path(__file__).with_name("candidate.py"))
candidate = importlib.util.module_from_spec(candidate_spec)
candidate_spec.loader.exec_module(candidate)


def valid_raw():
    return {
        "session": {"pid": 100, "returncode": -9, "killed_by_sigkill": True,
                    "kill_requested_ns": 1000, "dead_ns": 1100},
        "owner": {"pid": 101, "session_pid_at_start": 100,
                  "ppid_at_eof": 1, "eof_ns": 1200, "release_started_ns": 1300,
                  "release_verified_ns": 1400, "keys_down_before_release": [38],
                  "keys_down_after_release": [], "keymap_up": True,
                  "receipt_fsynced": True, "returncode": 0, "forced_kill": False},
        "observer": {"key_press_ns": 900, "key_release_ns": 1350,
                     "keymap_down_before_kill": True, "keymap_up_after_release": True},
        "xvfb": {"returncode": 0},
    }


class AuditTests(unittest.TestCase):
    def test_complete_parent_crash_recovery_passes(self):
        self.assertEqual(audit_raw.audit(valid_raw()), [])

    def test_owner_release_before_session_death_is_rejected(self):
        raw = valid_raw()
        raw["owner"]["eof_ns"] = 1200
        raw["owner"]["release_started_ns"] = 1150
        self.assertIn("session kill, owner EOF, and release ordering invalid",
                      audit_raw.audit(raw))

    def test_missing_external_keymap_verification_is_rejected(self):
        raw = valid_raw()
        raw["observer"]["keymap_up_after_release"] = False
        self.assertIn("independent keymap did not verify key-up", audit_raw.audit(raw))

    def test_forced_owner_kill_is_not_counted_as_recovery(self):
        raw = valid_raw()
        raw["owner"]["forced_kill"] = True
        self.assertIn("owner required forced termination", audit_raw.audit(raw))

    def test_x_event_record_uses_window_id_without_server_event_attribute(self):
        event = SimpleNamespace(type=2, detail=38, window=SimpleNamespace(id=123))
        record = candidate.event_record(event, observed_ns=456)
        self.assertEqual(record, {"type": 2, "keycode": 38,
                                  "observed_ns": 456, "window": 123})


if __name__ == "__main__":
    unittest.main()
