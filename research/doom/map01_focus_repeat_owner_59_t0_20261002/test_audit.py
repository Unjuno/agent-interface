"""Contract tests for the owner-integrated focus/autorepeat raw auditor."""
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent
AUDIT_PATH = ROOT / "audit.py"
SPEC = importlib.util.spec_from_file_location("focus_repeat_audit", AUDIT_PATH)
AUDIT = importlib.util.module_from_spec(SPEC) if SPEC else None
if SPEC and SPEC.loader and AUDIT_PATH.exists():
    SPEC.loader.exec_module(AUDIT)
else:
    AUDIT = None


def valid_raw():
    return {
        "schema": "issue59-focus-repeat-owner-raw-v1",
        "allocation_id": "ISSUE59-FOCUS-REPEAT-OWNER-T0-20261002-01",
        "candidate_invocations": 1,
        "retries": 0,
        "xvfb_exit_code": 0,
        "xvfb_socket_removed": True,
        "xvfb_lock_removed": True,
        "positive_control": {
            "window": "A",
            "keycode": 25,
            "repeat_events": [
                {"type": "KeyPress", "window": "A", "keycode": 25, "time_ns": 12},
                {"type": "KeyPress", "window": "A", "keycode": 25, "time_ns": 22},
            ],
            "verified_release": True,
        },
        "trial": {
            "owner_admission": {"window": "A", "keycode": 25, "admitted_ns": 100, "ack_ns": 101},
            "focus_change": {"from": "A", "to": "B", "request_ns": 110, "sync_returned_ns": 111,
                             "observed_focus": "B", "observed_ns": 112},
            "owner_focus_samples": [
                {"focus": "A", "started_ns": 108, "finished_ns": 109},
                {"focus": "B", "started_ns": 113, "finished_ns": 114},
            ],
            "owner_release": {
                "reason": "focus_changed",
                "keycode": 25,
                "request_ns": 115,
                "sync_returned_ns": 118,
                "verified_ns": 118,
                "verified_empty": True,
                "keys_down": [],
            },
            "new_focus_event_pump": {
                "window": "B",
                "started_ns": 112,
                "stopped_ns": 130,
                "complete": True,
                "events": [],
            },
        },
    }


class FocusRepeatAuditContractTests(unittest.TestCase):
    def classify(self, raw):
        self.assertIsNotNone(AUDIT, "audit.py must implement the frozen raw-record contract")
        return AUDIT.classify(raw)

    def test_verified_focus_release_before_any_new_focus_repeat_is_scoped_pass(self):
        result = self.classify(valid_raw())
        self.assertEqual(result["status"], "PASS_OWNER_FOCUS_RELEASE_SCOPED")
        self.assertEqual(result["new_focus_keypresses_before_release"], 0)

    def test_repeat_received_before_verified_release_is_counterexample(self):
        raw = valid_raw()
        raw["trial"]["new_focus_event_pump"]["events"] = [
            {"type": "KeyPress", "window": "B", "keycode": 25, "time_ns": 114},
        ]
        result = self.classify(raw)
        self.assertEqual(result["status"], "COUNTEREXAMPLE_REPEAT_BEFORE_VERIFIED_RELEASE")
        self.assertEqual(result["new_focus_keypresses_before_release"], 1)

    def test_unverified_keymap_release_is_hold_not_pass(self):
        raw = valid_raw()
        raw["trial"]["owner_release"].update(verified_empty=False, keys_down=[25])
        result = self.classify(raw)
        self.assertEqual(result["status"], "HOLD_RELEASE_NOT_VERIFIED")

    def test_missing_repeat_positive_control_is_stop(self):
        raw = valid_raw()
        raw["positive_control"]["repeat_events"] = []
        result = self.classify(raw)
        self.assertEqual(result["status"], "STOP_REPEAT_STIMULUS_NOT_ESTABLISHED")

    def test_incomplete_new_focus_event_coverage_is_hold(self):
        raw = valid_raw()
        raw["trial"]["new_focus_event_pump"]["complete"] = False
        result = self.classify(raw)
        self.assertEqual(result["status"], "HOLD_EVENT_COVERAGE_INCOMPLETE")

    def test_malformed_event_timestamp_is_hold(self):
        raw = valid_raw()
        raw["trial"]["new_focus_event_pump"]["events"] = [
            {"type": "KeyPress", "window": "B", "keycode": 25, "time_ns": "113"},
        ]
        self.assertEqual(self.classify(raw)["status"], "HOLD_RAW_RECORD_INVALID")

    def test_wrong_window_and_key_events_do_not_count_as_repeat(self):
        raw = valid_raw()
        raw["trial"]["new_focus_event_pump"]["events"] = [
            {"type": "KeyPress", "window": "A", "keycode": 25, "time_ns": 114},
            {"type": "KeyPress", "window": "B", "keycode": 26, "time_ns": 114},
        ]
        result = self.classify(raw)
        self.assertEqual(result["status"], "PASS_OWNER_FOCUS_RELEASE_SCOPED")
        self.assertEqual(result["new_focus_keypresses_before_release"], 0)

    def test_release_must_follow_focus_transfer_and_admission(self):
        raw = valid_raw()
        raw["trial"]["owner_release"]["verified_ns"] = 109
        self.assertEqual(self.classify(raw)["status"], "HOLD_RAW_RECORD_INVALID")

    def test_event_receipt_after_verified_release_is_not_counterexample(self):
        raw = valid_raw()
        raw["trial"]["new_focus_event_pump"]["events"] = [
            {"type": "KeyPress", "window": "B", "keycode": 25, "time_ns": 120},
        ]
        result = self.classify(raw)
        self.assertEqual(result["status"], "PASS_OWNER_FOCUS_RELEASE_SCOPED")
        self.assertEqual(result["new_focus_keypresses_before_release"], 0)

    def test_owner_must_observe_focus_change_before_release(self):
        raw = valid_raw()
        raw["trial"]["owner_focus_samples"] = [
            {"focus": "A", "started_ns": 108, "finished_ns": 109},
        ]
        self.assertEqual(self.classify(raw)["status"], "HOLD_RAW_RECORD_INVALID")

    def test_event_records_must_be_monotonic(self):
        raw = valid_raw()
        raw["trial"]["new_focus_event_pump"]["events"] = [
            {"type": "KeyRelease", "window": "B", "keycode": 25, "time_ns": 121},
            {"type": "KeyPress", "window": "B", "keycode": 25, "time_ns": 120},
        ]
        self.assertEqual(self.classify(raw)["status"], "HOLD_RAW_RECORD_INVALID")

    def test_incomplete_release_coverage_is_hold(self):
        raw = valid_raw()
        raw["trial"]["new_focus_event_pump"]["stopped_ns"] = 117
        self.assertEqual(self.classify(raw)["status"], "HOLD_EVENT_COVERAGE_INCOMPLETE")

    def test_summary_status_cannot_override_counterexample_records(self):
        raw = valid_raw()
        raw["status"] = "PASS_OWNER_FOCUS_RELEASE_SCOPED"
        raw["trial"]["new_focus_event_pump"]["events"] = [
            {"type": "KeyPress", "window": "B", "keycode": 25, "time_ns": 114},
        ]
        self.assertEqual(self.classify(raw)["status"], "COUNTEREXAMPLE_REPEAT_BEFORE_VERIFIED_RELEASE")

    def test_failing_release_record_is_hold(self):
        raw = valid_raw()
        raw["trial"]["owner_release"]["verified_empty"] = True
        raw["trial"]["owner_release"]["verified"] = False
        self.assertEqual(self.classify(raw)["status"], "HOLD_RELEASE_NOT_VERIFIED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
