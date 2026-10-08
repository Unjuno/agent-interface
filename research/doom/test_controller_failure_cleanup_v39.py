import json
import tempfile
import unittest
from pathlib import Path

from doom_controller_failure_cleanup_v1 import (
    ControllerFailureCleanup, reject_duplicate_json_members)

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
    def run_cleanup_events(self, events):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            scope = ControllerFailureCleanup(Planner(), output)
            scope.observe_output(
                events, RetiredReader(),
                lambda predicate, timeout: None, None, [])
            with self.assertRaisesRegex(RuntimeError, "refresh refused"):
                with scope:
                    scope.set_stage("source_refresh")
                    raise RuntimeError("refresh refused: release token mismatch")
            return json.loads((output / "controller-failure.json").read_text())

    def run_cleanup_jsonl(self, lines):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            events = []
            reader_errors = []
            try:
                for line in lines:
                    row = json.loads(
                        line, object_pairs_hook=reject_duplicate_json_members)
                    events.append(row)
            except BaseException as error:
                reader_errors.append(f"{type(error).__name__}: {error}")
            scope = ControllerFailureCleanup(Planner(), output)
            scope.observe_output(events, RetiredReader(), None, None, reader_errors)
            with self.assertRaisesRegex(RuntimeError, "refresh refused"):
                with scope:
                    scope.set_stage("source_refresh")
                    raise RuntimeError("refresh refused: test cleanup")
            receipt = json.loads(
                (output / "controller-failure.json").read_text())
            return receipt

    def test_unique_raw_jsonl_still_certifies_empty_release(self):
        receipt = self.run_cleanup_jsonl([
            '{"event":"accepted","id":"source-refresh-0",'
            '"intent_token":"lease-1"}',
            '{"event":"terminal","id":"source-refresh-0","release":'
            '{"verified":true,"keys_down":[],"buttons_down":[],'
            '"keys_unknown":[],"key_state_errors":[],'
            '"intent_token":"lease-1"}}',
        ])
        self.assertEqual(receipt["stdout_reader_errors"], [])
        self.assertTrue(receipt["input_terminals_complete"])
        self.assertTrue(receipt["input_releases_verified_empty"])

    def test_duplicate_accepted_json_member_fails_closed(self):
        receipt = self.run_cleanup_jsonl([
            '{"event":"accepted","id":"decoy","id":"source-refresh-0",'
            '"intent_token":"lease-1"}',
            '{"event":"terminal","id":"source-refresh-0","release":'
            '{"verified":true,"keys_down":[],"buttons_down":[],'
            '"keys_unknown":[],"key_state_errors":[],'
            '"intent_token":"lease-1"}}',
        ])
        self.assertEqual(len(receipt["stdout_reader_errors"]), 1)
        self.assertIn("duplicate JSON member: 'id'",
                      receipt["stdout_reader_errors"][0])
        self.assertFalse(receipt["input_terminals_complete"])
        self.assertFalse(receipt["input_releases_verified_empty"])

    def test_duplicate_terminal_release_member_fails_closed(self):
        receipt = self.run_cleanup_jsonl([
            '{"event":"accepted","id":"source-refresh-0",'
            '"intent_token":"lease-1"}',
            '{"event":"terminal","id":"source-refresh-0","release":'
            '{"verified":false,"verified":true,"keys_down":[],'
            '"buttons_down":[],"keys_unknown":[],"key_state_errors":[],'
            '"intent_token":"lease-1"}}',
        ])
        self.assertEqual(len(receipt["stdout_reader_errors"]), 1)
        self.assertIn("duplicate JSON member: 'verified'",
                      receipt["stdout_reader_errors"][0])
        self.assertFalse(receipt["input_terminals_complete"])
        self.assertFalse(receipt["input_releases_verified_empty"])

    def test_escaped_duplicate_json_member_name_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "duplicate JSON member: 'id'"):
            json.loads('{"id":"first","\\u0069d":"second"}',
                       object_pairs_hook=reject_duplicate_json_members)

    def run_cleanup(self, release_token=OMIT_TOKEN, release_overrides=None,
                    missing_release_fields=()):
        accepted = {"event": "accepted", "id": "source-refresh-0",
                    "intent_token": "accepted-lease"}
        release = {"verified": True, "keys_down": [], "buttons_down": [],
                   "keys_unknown": [], "key_state_errors": []}
        if release_token is not OMIT_TOKEN:
            release["intent_token"] = release_token
        release.update(release_overrides or {})
        for field in missing_release_fields:
            release.pop(field, None)
        terminal = {"event": "terminal", "id": "source-refresh-0",
                    "release": release}
        return self.run_cleanup_events([accepted, terminal])

    def test_matching_release_token_is_retained_as_empty(self):
        receipt = self.run_cleanup("accepted-lease")
        self.assertTrue(receipt["input_release_verified_empty"])

    def test_mismatched_release_token_is_not_certified_empty(self):
        receipt = self.run_cleanup("different-lease")
        self.assertFalse(receipt["input_release_verified_empty"])

    def test_release_without_optional_token_keeps_legacy_id_binding(self):
        receipt = self.run_cleanup()
        self.assertTrue(receipt["input_release_verified_empty"])

    def test_cancelled_without_admission_accepts_null_lease_token(self):
        accepted = {"event": "accepted", "id": "source-refresh-0",
                    "intent_token": "accepted-lease"}
        terminal = {
            "event": "terminal", "id": "source-refresh-0",
            "status": "cancelled",
            "release": {"verified": True, "keys_down": [],
                        "buttons_down": [], "keys_unknown": [],
                        "key_state_errors": [], "intent_token": None},
        }
        receipt = self.run_cleanup_events([accepted, terminal])
        self.assertTrue(receipt["input_releases_verified_empty"])

    def test_cancelled_admission_requires_matching_owner_release(self):
        accepted = {"event": "accepted", "id": "source-refresh-0",
                    "intent_token": "accepted-lease"}
        admission = {"event": "input_admission", "id": "source-refresh-0",
                     "intent_token": "accepted-lease"}
        terminal = {
            "event": "terminal", "id": "source-refresh-0",
            "status": "cancelled",
            "release": {"verified": True, "keys_down": [],
                        "buttons_down": [], "keys_unknown": [],
                        "key_state_errors": [], "intent_token": "accepted-lease"},
        }
        missing_receipt = self.run_cleanup_events([accepted, admission, terminal])
        self.assertFalse(missing_receipt["input_releases_verified_empty"])
        owner_release = {"event": "input_released", "id": "source-refresh-0",
                         "intent_token": "accepted-lease",
                         "owner_release": {"verified": True, "keys_down": [],
                                           "buttons_down": [], "keys_unknown": [],
                                           "key_state_errors": [],
                                           "intent_token": "accepted-lease"}}
        matching_receipt = self.run_cleanup_events(
            [accepted, admission, owner_release, terminal])
        self.assertTrue(matching_receipt["input_releases_verified_empty"])

    def test_duplicate_input_release_receipts_fail_closed(self):
        accepted = {"event": "accepted", "id": "source-refresh-0",
                    "intent_token": "accepted-lease"}
        admission = {"event": "input_admission", "id": "source-refresh-0",
                     "intent_token": "accepted-lease"}
        good_release = {"event": "input_released", "id": "source-refresh-0",
                        "intent_token": "accepted-lease",
                        "owner_release": {"verified": True, "keys_down": [],
                                          "buttons_down": [], "keys_unknown": [],
                                          "key_state_errors": [],
                                          "intent_token": "accepted-lease"}}
        contradictory_release = {"event": "input_released", "id": "source-refresh-0",
                                 "intent_token": "accepted-lease",
                                 "owner_release": {"verified": False,
                                                   "keys_down": ["KEY_W"],
                                                   "buttons_down": [],
                                                   "keys_unknown": [],
                                                   "key_state_errors": [],
                                                   "intent_token": "accepted-lease"}}
        terminal = {"event": "terminal", "id": "source-refresh-0",
                    "status": "cancelled",
                    "release": {"verified": True, "keys_down": [],
                                "buttons_down": [], "keys_unknown": [],
                                "key_state_errors": [],
                                "intent_token": "accepted-lease"}}
        for releases in ((good_release, contradictory_release),
                         (contradictory_release, good_release)):
            with self.subTest(first_release_verified=releases[0]["owner_release"]["verified"]):
                receipt = self.run_cleanup_events(
                    [accepted, admission, *releases, terminal])
                self.assertFalse(receipt["input_releases_verified_empty"])

    def test_cancelled_admission_rejects_wrong_owner_release_token(self):
        accepted = {"event": "accepted", "id": "source-refresh-0",
                    "intent_token": "accepted-lease"}
        admission = {"event": "input_admission", "id": "source-refresh-0",
                     "intent_token": "accepted-lease"}
        owner_release = {"event": "input_released", "id": "source-refresh-0",
                         "intent_token": "other-lease",
                         "owner_release": {"verified": True, "keys_down": [],
                                           "buttons_down": [], "keys_unknown": [],
                                           "key_state_errors": [],
                                           "intent_token": "other-lease"}}
        terminal = {
            "event": "terminal", "id": "source-refresh-0",
            "status": "cancelled",
            "release": {"verified": True, "keys_down": [],
                        "buttons_down": [], "keys_unknown": [],
                        "key_state_errors": [], "intent_token": "accepted-lease"},
        }
        receipt = self.run_cleanup_events([accepted, admission, owner_release, terminal])
        self.assertFalse(receipt["input_releases_verified_empty"])

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

    def test_duplicate_accepted_id_cannot_be_collapsed_to_one_terminal(self):
        terminal = {"event": "terminal", "id": "duplicate-command",
                    "release": {"verified": True, "keys_down": [],
                                "buttons_down": [], "keys_unknown": [],
                                "key_state_errors": [],
                                "intent_token": "lease-B"}}
        accepts = [
            {"event": "accepted", "id": "duplicate-command",
             "intent_token": "lease-A"},
            {"event": "accepted", "id": "duplicate-command",
             "intent_token": "lease-B"},
        ]
        for ordered_accepts in (accepts, list(reversed(accepts))):
            with self.subTest(accept_tokens=[row["intent_token"] for row in ordered_accepts]):
                receipt = self.run_cleanup_events([*ordered_accepts, terminal])
                self.assertFalse(receipt["input_terminals_complete"])
                self.assertFalse(receipt["input_releases_verified_empty"])
                self.assertEqual(receipt["duplicate_accepted_ids"],
                                 ["duplicate-command"])

    def test_duplicate_terminal_id_fails_closed_in_either_row_order(self):
        accepted = {"event": "accepted", "id": "duplicate-command",
                    "intent_token": "lease-A"}
        terminals = [
            {"event": "terminal", "id": "duplicate-command",
             "release": {"verified": True, "keys_down": [],
                         "buttons_down": [], "keys_unknown": [],
                         "key_state_errors": [], "intent_token": "lease-A"}},
            {"event": "terminal", "id": "duplicate-command",
             "release": {"verified": False, "keys_down": ["KEY_W"],
                         "buttons_down": [], "keys_unknown": [],
                         "key_state_errors": [], "intent_token": "lease-A"}},
        ]
        for ordered_terminals in (terminals, list(reversed(terminals))):
            with self.subTest(first_verified=ordered_terminals[0]["release"]["verified"]):
                receipt = self.run_cleanup_events([accepted, *ordered_terminals])
                self.assertFalse(receipt["input_terminals_complete"])
                self.assertFalse(receipt["input_releases_verified_empty"])
                self.assertEqual(receipt["duplicate_terminal_ids"],
                                 ["duplicate-command"])

    def test_unmatched_or_invalid_event_ids_fail_closed(self):
        valid_release = {"verified": True, "keys_down": [],
                         "buttons_down": [], "keys_unknown": [],
                         "key_state_errors": []}
        cases = [
            ("unmatched_terminal", [
                {"event": "accepted", "id": "accepted-command"},
                {"event": "terminal", "id": "other-command",
                 "release": valid_release},
            ], 0, 0),
            ("invalid_accept_id", [
                {"event": "accepted", "id": 7},
                {"event": "terminal", "id": "terminal-command",
                 "release": valid_release},
            ], 1, 0),
            ("missing_terminal_id", [
                {"event": "accepted", "id": "accepted-command"},
                {"event": "terminal", "release": valid_release},
            ], 0, 1),
        ]
        for name, events, invalid_accepts, invalid_terminals in cases:
            with self.subTest(name=name):
                receipt = self.run_cleanup_events(events)
                self.assertFalse(receipt["input_terminals_complete"])
                self.assertFalse(receipt["input_releases_verified_empty"])
                self.assertEqual(receipt["invalid_accepted_event_id_count"],
                                 invalid_accepts)
                self.assertEqual(receipt["invalid_terminal_event_id_count"],
                                 invalid_terminals)

    def test_non_object_event_records_fail_closed(self):
        for malformed in ("unexpected-json-scalar", [{"event": "accepted", "id": "x"}]):
            with self.subTest(record_type=type(malformed).__name__):
                receipt = self.run_cleanup_events([malformed])
                self.assertFalse(receipt["input_terminals_complete"])
                self.assertFalse(receipt["input_releases_verified_empty"])
                self.assertFalse(receipt["input_event_identities_unambiguous"])
                self.assertEqual(receipt["invalid_event_record_count"], 1)


if __name__ == "__main__":
    unittest.main()
