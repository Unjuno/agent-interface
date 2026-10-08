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
    def run_cleanup(self, release_token=OMIT_TOKEN, release_overrides=None,
                    missing_release_fields=()):
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
                "keys_unknown": [],
                "key_state_errors": [],
            }
            if release_token is not OMIT_TOKEN:
                release["intent_token"] = release_token
            release.update(release_overrides or {})
            for field in missing_release_fields:
                release.pop(field, None)
            terminal = {
                "event": "terminal",
                "id": "source-refresh-0",
                "release": release,
            }
            scope = ControllerFailureCleanup(Planner(), output)
            scope.observe_output(
                [accepted, terminal], RetiredReader(),
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

    def test_unknown_key_state_prevents_empty_release_certificate(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            accepted = {"event": "accepted", "id": "source-refresh-0",
                        "intent_token": "accepted-lease"}
            terminal = {
                "event": "terminal", "id": "source-refresh-0",
                "release": {"verified": True, "keys_down": [],
                            "buttons_down": [], "keys_unknown": ["KEY_W"],
                            "intent_token": "accepted-lease"},
            }
            scope = ControllerFailureCleanup(Planner(), output)
            scope.observe_output([accepted, terminal], RetiredReader(),
                                 lambda predicate, timeout: None, None, [])
            with self.assertRaisesRegex(RuntimeError, "fixture"):
                with scope:
                    raise RuntimeError("fixture")
            receipt = json.loads(
                (output / "controller-failure.json").read_text())
            self.assertFalse(receipt["input_release_verified_empty"])

    def test_missing_unknown_key_state_prevents_empty_release_certificate(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            accepted = {"event": "accepted", "id": "source-refresh-0",
                        "intent_token": "accepted-lease"}
            terminal = {
                "event": "terminal", "id": "source-refresh-0",
                "release": {"verified": True, "keys_down": [],
                            "buttons_down": [],
                            "intent_token": "accepted-lease"},
            }
            scope = ControllerFailureCleanup(Planner(), output)
            scope.observe_output([accepted, terminal], RetiredReader(),
                                 lambda predicate, timeout: None, None, [])
            with self.assertRaisesRegex(RuntimeError, "fixture"):
                with scope:
                    raise RuntimeError("fixture")
            receipt = json.loads(
                (output / "controller-failure.json").read_text())
            self.assertFalse(receipt["input_release_verified_empty"])

    def test_key_state_errors_prevent_empty_release_certificate(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            accepted = {"event": "accepted", "id": "source-refresh-0",
                        "intent_token": "accepted-lease"}
            terminal = {
                "event": "terminal", "id": "source-refresh-0",
                "release": {"verified": True, "keys_down": [],
                            "buttons_down": [], "keys_unknown": [],
                            "key_state_errors": [{"source": "keymap_after"}],
                            "intent_token": "accepted-lease"},
            }
            scope = ControllerFailureCleanup(Planner(), output)
            scope.observe_output([accepted, terminal], RetiredReader(),
                                 lambda predicate, timeout: None, None, [])
            with self.assertRaisesRegex(RuntimeError, "fixture"):
                with scope:
                    raise RuntimeError("fixture")
            receipt = json.loads(
                (output / "controller-failure.json").read_text())
            self.assertFalse(receipt["input_release_verified_empty"])

    def test_missing_key_state_errors_prevent_empty_release_certificate(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            accepted = {"event": "accepted", "id": "source-refresh-0",
                        "intent_token": "accepted-lease"}
            terminal = {
                "event": "terminal", "id": "source-refresh-0",
                "release": {"verified": True, "keys_down": [],
                            "buttons_down": [], "keys_unknown": [],
                            "intent_token": "accepted-lease"},
            }
            scope = ControllerFailureCleanup(Planner(), output)
            scope.observe_output([accepted, terminal], RetiredReader(),
                                 lambda predicate, timeout: None, None, [])
            with self.assertRaisesRegex(RuntimeError, "fixture"):
                with scope:
                    raise RuntimeError("fixture")
            receipt = json.loads(
                (output / "controller-failure.json").read_text())
            self.assertFalse(receipt["input_release_verified_empty"])

    def test_release_state_mutation_matrix_fails_closed(self):
        mutations = [
            ("down_key", {"keys_down": ["KEY_W"]}, ()),
            ("down_button", {"buttons_down": [1]}, ()),
            ("unknown_key", {"keys_unknown": ["KEY_W"]}, ()),
            ("state_error", {"key_state_errors": [{"source": "keymap_after"}]}, ()),
            ("unverified", {"verified": False}, ()),
            ("missing_verified", {}, ("verified",)),
            ("missing_keys_down", {}, ("keys_down",)),
            ("missing_buttons_down", {}, ("buttons_down",)),
            ("missing_keys_unknown", {}, ("keys_unknown",)),
            ("missing_key_state_errors", {}, ("key_state_errors",)),
        ]
        for name, overrides, missing in mutations:
            with self.subTest(name=name):
                receipt = self.run_cleanup(
                    release_token="accepted-lease",
                    release_overrides=overrides,
                    missing_release_fields=missing)
                self.assertFalse(receipt["input_release_verified_empty"])


if __name__ == "__main__":
    unittest.main()
