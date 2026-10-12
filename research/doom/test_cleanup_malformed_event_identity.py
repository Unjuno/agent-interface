import json
import tempfile
import unittest
from pathlib import Path

from doom_controller_failure_cleanup_v1 import ControllerFailureCleanup


class Planner:
    def close(self, timeout=1):
        return None


class RetiredReader:
    def join(self, timeout=None):
        return None

    def is_alive(self):
        return False


class MalformedCleanupEventIdentityTests(unittest.TestCase):
    def run_cleanup(self, extra_event):
        events = [
            {"event": "accepted", "id": "control-1", "intent_token": "lease-1"},
            {"event": "terminal", "id": "control-1", "release": {
                "verified": True, "keys_down": [], "buttons_down": [],
                "intent_token": "lease-1"}},
            extra_event,
        ]
        with tempfile.TemporaryDirectory() as directory:
            scope = ControllerFailureCleanup(Planner(), Path(directory))
            scope.observe_output(events, RetiredReader(), lambda predicate, timeout: None,
                                 None, [])
            with self.assertRaisesRegex(RuntimeError, "fixture failure"):
                with scope:
                    scope.set_stage("malformed_event_identity")
                    raise RuntimeError("fixture failure")
            return json.loads((Path(directory) / "controller-failure.json").read_text())

    def assert_unverified(self, event):
        receipt = self.run_cleanup(event)
        self.assertTrue(receipt["event_identity_ambiguous"])
        self.assertFalse(receipt["input_terminals_complete"])
        self.assertFalse(receipt["input_releases_verified_empty"])
        self.assertFalse(receipt["input_release_verified_empty"])

    def test_accepted_rows_without_nonempty_string_ids_fail_closed(self):
        for event in (
            {"event": "accepted"},
            {"event": "accepted", "id": None},
            {"event": "accepted", "id": ""},
            {"event": "accepted", "id": 7},
        ):
            with self.subTest(event=event):
                self.assert_unverified(event)

    def test_terminal_rows_without_nonempty_string_ids_fail_closed(self):
        for event in (
            {"event": "terminal"},
            {"event": "terminal", "id": None},
            {"event": "terminal", "id": ""},
            {"event": "terminal", "id": 7},
        ):
            with self.subTest(event=event):
                self.assert_unverified(event)

    def test_nonobject_or_missing_event_rows_fail_closed(self):
        for event in (None, {"id": "untyped-row"}):
            with self.subTest(event=event):
                self.assert_unverified(event)

    def test_non_list_event_stream_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            scope = ControllerFailureCleanup(Planner(), Path(directory))
            scope.observe_output(None, RetiredReader(), lambda predicate, timeout: None,
                                 None, [])
            with self.assertRaisesRegex(RuntimeError, "fixture failure"):
                with scope:
                    scope.set_stage("malformed_event_identity")
                    raise RuntimeError("fixture failure")
            receipt = json.loads((Path(directory) / "controller-failure.json").read_text())
        self.assertTrue(receipt["event_identity_ambiguous"])
        self.assertFalse(receipt["input_terminals_complete"])
        self.assertFalse(receipt["input_releases_verified_empty"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
