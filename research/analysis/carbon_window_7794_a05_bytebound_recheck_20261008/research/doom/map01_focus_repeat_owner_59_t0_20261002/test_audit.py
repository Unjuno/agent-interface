"""Contract tests for the owner-integrated focus/autorepeat raw auditor."""
import importlib.util
from pathlib import Path
import unittest
from types import SimpleNamespace
import threading
from Xlib import X


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
        "base_main_sha": "a5756d9b31231a4d64268610236622ac44c36f1f",
        "candidate_invocations": 1,
        "retries": 0,
        "xvfb_exit_code": 0,
        "xvfb_socket_removed": True,
        "xvfb_lock_removed": True,
        "source_sha256": {
            "input_owner_v10.py": "ceae7d9983cd0ba13a35e01ce2ce7dbbf03a0397b23ddc123b0110b4d4de670b",
            "executor_v3.py": "ea3fa8c9751a6a41b4814ad6e0d03bec85166765b0a41d2488a51750d17b3a4a",
            "lease.py": "e71f9850d3999a31fcb86c00f9ef7a8ba19bae8d3a8bdc11bf7bd620817a535f",
        },
        "source_git_blobs": {
            "input_owner_v10.py": "341b3c01649943ddaad5f28431a792c4889cc36e",
            "executor_v3.py": "2b072454fd81c41bf9e025217afc78020c7059de",
            "lease.py": "b9dac6bb4063928354733d79bf371909a288a3d1",
        },
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
                {"focus": "B", "started_ns": 110, "finished_ns": 111},
            ],
            "owner_release": {
                "reason": "focus_changed",
                "keycode": 25,
                "request_ns": 115,
                "sync_returned_ns": 118,
                "verified_ns": 118,
                "verified_empty": True,
                "verified": True,
                "keys_down": [],
            },
            "new_focus_event_pump": {
                "window": "B",
                "started_ns": 109,
                "subscription_ns": 109,
                "stopped_ns": 130,
                "subscribed": True,
                "fence_completed": True,
                "error": None,
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

    def test_repeat_during_focus_request_sync_window_is_counterexample(self):
        raw = valid_raw()
        raw["trial"]["new_focus_event_pump"]["events"] = [
            {"type": "KeyPress", "window": "B", "keycode": 25, "time_ns": 110},
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

    def test_unsubscribed_reader_cannot_claim_complete_coverage(self):
        raw = valid_raw()
        raw["trial"]["new_focus_event_pump"]["subscribed"] = False
        self.assertEqual(self.classify(raw)["status"], "HOLD_EVENT_COVERAGE_INCOMPLETE")

    def test_missing_or_failed_final_fence_cannot_claim_complete_coverage(self):
        for field, value in (("fence_completed", False), ("error", "X connection failed")):
            with self.subTest(field=field):
                raw = valid_raw()
                raw["trial"]["new_focus_event_pump"][field] = value
                self.assertEqual(self.classify(raw)["status"], "HOLD_EVENT_COVERAGE_INCOMPLETE")

    def test_subscription_must_precede_focus_request(self):
        raw = valid_raw()
        raw["trial"]["new_focus_event_pump"]["subscription_ns"] = 111
        self.assertEqual(self.classify(raw)["status"], "HOLD_EVENT_COVERAGE_INCOMPLETE")


    def test_same_connection_subscription_and_fenced_final_drain(self):
        from research.doom.map01_focus_repeat_owner_59_t0_20261002.probe import event_pump

        row = SimpleNamespace(type=2, window=SimpleNamespace(id=7), detail=25)

        class FakeWindow:
            def __init__(self):
                self.event_mask = None

            def change_attributes(self, **kwargs):
                self.event_mask = kwargs["event_mask"]

        class FakeDisplay:
            def __init__(self):
                self.window = FakeWindow()
                self.queued = [row]
                self.synced = False

            def create_resource_object(self, kind, identifier):
                self.asserted_identity = (kind, identifier)
                return self.window

            def sync(self):
                self.synced = True

            def pending_events(self):
                return len(self.queued)

            def next_event(self):
                return self.queued.pop(0)

        dpy = FakeDisplay()
        stop = threading.Event()
        stop.set()
        state = {}
        event_pump(dpy, 7, 1, stop, state)
        self.assertEqual(dpy.asserted_identity, ("window", 7))
        self.assertEqual(dpy.window.event_mask, X.KeyPressMask | X.KeyReleaseMask)
        self.assertTrue(state["subscribed"])
        self.assertTrue(state["fence_completed"])
        self.assertIsNone(state["error"])
        self.assertEqual(state["events"][0]["window"], "B")

    def test_event_pump_exception_is_reported_and_never_fenced(self):
        from research.doom.map01_focus_repeat_owner_59_t0_20261002.probe import event_pump

        class BrokenDisplay:
            def create_resource_object(self, *_args):
                raise OSError("reader disconnected")

        state = {}
        stop = threading.Event()
        event_pump(BrokenDisplay(), 7, 1, stop, state)
        self.assertIn("reader disconnected", state["error"])
        self.assertFalse(state["fence_completed"])

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

    def test_event_dequeued_after_release_is_ambiguous_and_cannot_pass(self):
        raw = valid_raw()
        raw["trial"]["new_focus_event_pump"]["events"] = [
            {"type": "KeyPress", "window": "B", "keycode": 25, "time_ns": 120},
        ]
        result = self.classify(raw)
        self.assertEqual(result["status"], "HOLD_EVENT_COVERAGE_INCOMPLETE")
        self.assertEqual(result["new_focus_keypresses_before_release"], 0)

    def test_owner_must_observe_focus_change_before_release(self):
        raw = valid_raw()
        raw["trial"]["owner_focus_samples"] = [
            {"focus": "A", "started_ns": 108, "finished_ns": 109},
        ]
        self.assertEqual(self.classify(raw)["status"], "HOLD_RAW_RECORD_INVALID")

    def test_owner_focus_query_may_beat_external_focus_readback(self):
        raw = valid_raw()
        sample = raw["trial"]["owner_focus_samples"][1]
        sample.update(started_ns=110, finished_ns=111)
        self.assertEqual(self.classify(raw)["status"], "PASS_OWNER_FOCUS_RELEASE_SCOPED")

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

    def test_missing_release_verification_is_hold(self):
        raw = valid_raw()
        raw["trial"]["owner_release"].pop("verified")
        self.assertEqual(self.classify(raw)["status"], "HOLD_RELEASE_NOT_VERIFIED")

    def test_null_release_verification_is_hold(self):
        raw = valid_raw()
        raw["trial"]["owner_release"]["verified"] = None
        self.assertEqual(self.classify(raw)["status"], "HOLD_RELEASE_NOT_VERIFIED")

    def test_failing_release_record_is_hold(self):
        raw = valid_raw()
        raw["trial"]["owner_release"]["verified_empty"] = True
        raw["trial"]["owner_release"]["verified"] = False
        self.assertEqual(self.classify(raw)["status"], "HOLD_RELEASE_NOT_VERIFIED")

    def test_source_identity_hashes_are_required(self):
        raw = valid_raw()
        del raw["source_sha256"]["input_owner_v10.py"]
        self.assertEqual(self.classify(raw)["status"], "HOLD_RAW_RECORD_INVALID")

    def test_source_identity_must_match_refrozen_main(self):
        raw = valid_raw()
        raw["source_git_blobs"]["input_owner_v10.py"] = "0" * 40
        self.assertEqual(self.classify(raw)["status"], "HOLD_RAW_RECORD_INVALID")


if __name__ == "__main__":
    unittest.main(verbosity=2)
