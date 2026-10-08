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
    def run_cleanup(self, release_token=OMIT_TOKEN):
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


if __name__ == "__main__":
    unittest.main()
