import json
import tempfile
import unittest
from pathlib import Path

from doom_controller_failure_cleanup_v1 import ControllerFailureCleanup

OMIT_TOKEN = object()


class Planner:
    def close(self, timeout=1):
        return None


class RetiredReader:
    def join(self, timeout=None):
        return None

    def is_alive(self):
        return False


class ControllerFailureCleanupReleaseIdentityTests(unittest.TestCase):
    def run_cleanup(self, release_token=OMIT_TOKEN, events=None):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            accepted = {
                "event": "accepted",
                "id": "source-refresh-0",
                "intent_token": "accepted-lease",
            }
            release = {
                "verified": True,
                "keys_down": [],
                "buttons_down": [],
            }
            if release_token is not OMIT_TOKEN:
                release["intent_token"] = release_token
            terminal = {
                "event": "terminal",
                "id": "source-refresh-0",
                "release": release,
            }
            scope = ControllerFailureCleanup(Planner(), output)
            scope.observe_output(
                [accepted, terminal] if events is None else events, RetiredReader(),
                lambda predicate, timeout: None, None, [])
            with self.assertRaisesRegex(RuntimeError, "refresh refused"):
                with scope:
                    scope.set_stage("source_refresh")
                    raise RuntimeError("refresh refused: release token mismatch")
            return json.loads((output / "controller-failure.json").read_text())

    def test_matching_release_token_is_retained_as_empty(self):
        receipt = self.run_cleanup("accepted-lease")
        self.assertTrue(receipt["input_release_verified_empty"])

    def test_mismatched_release_token_is_not_certified_empty(self):
        receipt = self.run_cleanup("different-lease")
        self.assertFalse(receipt["input_release_verified_empty"])

    def test_release_without_optional_token_keeps_legacy_id_binding(self):
        receipt = self.run_cleanup()
        self.assertTrue(receipt["input_release_verified_empty"])

    def test_duplicate_acceptance_identity_is_ambiguous(self):
        first = {"event": "accepted", "id": "source-refresh-0",
                 "intent_token": "accepted-lease-a"}
        second = {"event": "accepted", "id": "source-refresh-0",
                  "intent_token": "accepted-lease-b"}
        terminal = {"event": "terminal", "id": "source-refresh-0",
                    "release": {"verified": True, "keys_down": [],
                                "buttons_down": [], "intent_token": "accepted-lease-b"}}

        receipt = self.run_cleanup(events=[first, second, terminal])

        self.assertFalse(receipt["input_terminals_complete"])
        self.assertFalse(receipt["input_releases_verified_empty"])
        self.assertFalse(receipt["input_release_verified_empty"])

    def test_conflicting_duplicate_terminals_are_order_independent(self):
        accepted = {"event": "accepted", "id": "source-refresh-0",
                    "intent_token": "accepted-lease"}
        released = {"event": "terminal", "id": "source-refresh-0",
                    "release": {"verified": True, "keys_down": [],
                                "buttons_down": [], "intent_token": "accepted-lease"}}
        unreleased = {"event": "terminal", "id": "source-refresh-0",
                      "release": {"verified": False, "keys_down": [38],
                                  "buttons_down": []}}

        for terminal_rows in ([released, unreleased], [unreleased, released]):
            with self.subTest(order=[row["release"]["verified"] for row in terminal_rows]):
                receipt = self.run_cleanup(events=[accepted, *terminal_rows])
                self.assertFalse(receipt["input_terminals_complete"])
                self.assertFalse(receipt["input_releases_verified_empty"])
                self.assertFalse(receipt["input_release_verified_empty"])


    def test_invalid_acceptance_identity_is_not_dropped(self):
        invalid_values = [None, 7, True, [], {}, '']
        for invalid_id in invalid_values:
            with self.subTest(invalid_id=invalid_id):
                receipt = self.run_cleanup(events=[
                    {'event': 'accepted', 'id': invalid_id, 'intent_token': 'lease-x'}])
                self.assertTrue(receipt['event_identity_ambiguous'])
                self.assertEqual(receipt['invalid_event_identity_counts']['accepted'], 1)
                self.assertFalse(receipt['input_terminals_complete'])
                self.assertFalse(receipt['input_releases_verified_empty'])
                self.assertFalse(receipt['input_release_verified_empty'])

    def test_missing_acceptance_identity_is_not_dropped(self):
        receipt = self.run_cleanup(events=[{'event': 'accepted', 'intent_token': 'lease-x'}])
        self.assertTrue(receipt['event_identity_ambiguous'])
        self.assertEqual(receipt['invalid_event_identity_counts']['accepted'], 1)
        self.assertFalse(receipt['input_terminals_complete'])
        self.assertFalse(receipt['input_releases_verified_empty'])

    def test_malformed_terminal_identity_blocks_empty_release_claim(self):
        accepted = {'event': 'accepted', 'id': 'source-refresh-0',
                    'intent_token': 'accepted-lease'}
        released = {'event': 'terminal', 'id': 'source-refresh-0',
                    'release': {'verified': True, 'keys_down': [],
                                'buttons_down': [], 'intent_token': 'accepted-lease'}}
        malformed = {'event': 'terminal', 'id': None,
                     'release': {'verified': False, 'keys_down': [38], 'buttons_down': []}}
        receipt = self.run_cleanup(events=[accepted, released, malformed])
        self.assertTrue(receipt['event_identity_ambiguous'])
        self.assertEqual(receipt['invalid_event_identity_counts']['terminal'], 1)
        self.assertFalse(receipt['input_terminals_complete'])
        self.assertFalse(receipt['input_releases_verified_empty'])
        self.assertFalse(receipt['input_release_verified_empty'])


    def test_malformed_acceptance_amid_valid_pair_blocks_empty_release(self):
        accepted = {'event': 'accepted', 'id': 'source-refresh-0',
                    'intent_token': 'accepted-lease'}
        malformed = {'event': 'accepted', 'id': None, 'intent_token': 'unknown'}
        terminal = {'event': 'terminal', 'id': 'source-refresh-0',
                    'release': {'verified': True, 'keys_down': [],
                                'buttons_down': [], 'intent_token': 'accepted-lease'}}
        receipt = self.run_cleanup(events=[accepted, malformed, terminal])
        self.assertTrue(receipt['event_identity_ambiguous'])
        self.assertEqual(receipt['invalid_event_identity_counts']['accepted'], 1)
        self.assertFalse(receipt['input_terminals_complete'])
        self.assertFalse(receipt['input_releases_verified_empty'])
        self.assertFalse(receipt['input_release_verified_empty'])


    def test_orphan_terminal_identity_blocks_empty_release_claim(self):
        accepted = {'event': 'accepted', 'id': 'accepted-1',
                    'intent_token': 'token-1'}
        matched = {'event': 'terminal', 'id': 'accepted-1',
                   'release': {'verified': True, 'keys_down': [],
                               'buttons_down': [], 'intent_token': 'token-1'}}
        orphan = {'event': 'terminal', 'id': 'orphan-2',
                  'release': {'verified': False, 'keys_down': [38], 'buttons_down': []}}
        receipt = self.run_cleanup(events=[accepted, matched, orphan])
        self.assertTrue(receipt['event_identity_ambiguous'])
        self.assertEqual(receipt['orphan_terminal_ids'], ['orphan-2'])
        self.assertFalse(receipt['input_terminals_complete'])
        self.assertFalse(receipt['input_releases_verified_empty'])
        self.assertFalse(receipt['input_release_verified_empty'])


if __name__ == "__main__":
    unittest.main()
