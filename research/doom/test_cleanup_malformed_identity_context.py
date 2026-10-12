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


class MalformedIdentityContextTests(unittest.TestCase):
    def run_cleanup(self, events):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            scope = ControllerFailureCleanup(Planner(), output)
            scope.observe_output(events, RetiredReader(),
                                 lambda predicate, timeout: None, None, [])
            with self.assertRaisesRegex(RuntimeError, "fixture failure"):
                with scope:
                    scope.set_stage("malformed_identity_context")
                    raise RuntimeError("fixture failure")
            return json.loads((output / "controller-failure.json").read_text())

    @staticmethod
    def valid_pair():
        return [
            {"event": "accepted", "id": "control-1", "intent_token": "lease-1"},
            {"event": "terminal", "id": "control-1", "release": {
                "verified": True, "keys_down": [], "buttons_down": [],
                "keys_unknown": [], "key_state_errors": [],
                "intent_token": "lease-1"}},
        ]

    def assert_not_certified(self, receipt):
        self.assertFalse(receipt["input_event_identities_unambiguous"])
        self.assertFalse(receipt["input_terminals_complete"])
        self.assertFalse(receipt["input_releases_verified_empty"])
        self.assertFalse(receipt["input_release_verified_empty"])

    def test_valid_pair_is_control(self):
        receipt = self.run_cleanup(self.valid_pair())
        self.assertTrue(receipt["input_event_identities_unambiguous"])
        self.assertTrue(receipt["input_terminals_complete"])
        self.assertTrue(receipt["input_releases_verified_empty"])

    def test_malformed_accepted_id_after_valid_pair_fails_closed(self):
        for malformed in (
            {"event": "accepted"},
            {"event": "accepted", "id": None},
            {"event": "accepted", "id": ""},
            {"event": "accepted", "id": 7},
        ):
            with self.subTest(malformed=malformed):
                receipt = self.run_cleanup(self.valid_pair() + [malformed])
                self.assert_not_certified(receipt)
                self.assertEqual(receipt["invalid_accepted_event_id_count"], 1)

    def test_malformed_terminal_id_after_valid_pair_fails_closed(self):
        for malformed in (
            {"event": "terminal"},
            {"event": "terminal", "id": None},
            {"event": "terminal", "id": ""},
            {"event": "terminal", "id": 7},
        ):
            with self.subTest(malformed=malformed):
                receipt = self.run_cleanup(self.valid_pair() + [malformed])
                self.assert_not_certified(receipt)
                self.assertEqual(receipt["invalid_terminal_event_id_count"], 1)

    def test_nonobject_or_undiscriminated_row_after_valid_pair_fails_closed(self):
        for malformed in (None, {}, {"event": None}, {"event": 7}):
            with self.subTest(malformed=malformed):
                receipt = self.run_cleanup(self.valid_pair() + [malformed])
                self.assert_not_certified(receipt)
                self.assertEqual(receipt["invalid_event_record_count"], 1)

    def test_non_list_event_collection_fails_closed(self):
        receipt = self.run_cleanup(None)
        self.assert_not_certified(receipt)
        self.assertEqual(receipt["invalid_event_record_count"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
