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


if __name__ == "__main__":
    unittest.main()
