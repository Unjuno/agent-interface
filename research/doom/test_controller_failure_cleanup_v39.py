import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from doom_controller_failure_cleanup_v1 import (
    ControllerFailureCleanup, load_controller_event, operation_release_verified,
    capture_raw_stdout_events, reject_duplicate_json_members,
    reject_stdout_reader_failure)

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
    def run_cleanup(self, release_token=OMIT_TOKEN, extra_events=(), status="failed",
                    release_overrides=None, missing_release_fields=()):
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
            "status": status,
            "release": release,
        }
        return self.run_cleanup_events([accepted, *extra_events, terminal])

    def run_cleanup_events(self, events, *, renewal=None):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            scope = ControllerFailureCleanup(Planner(), output)
            scope.observe_output(
                events, RetiredReader(),
                lambda predicate, timeout: None, None, [])
            with self.assertRaisesRegex(RuntimeError, "refresh refused"):
                with scope:
                    scope.set_stage("source_refresh")
                    error = RuntimeError("refresh refused: release token mismatch")
                    if renewal is not None:
                        error.cover_renewal_receipt = renewal
                    raise error
            return json.loads((output / "controller-failure.json").read_text())

    def run_cleanup_jsonl(self, lines):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            events = []
            reader_errors = []
            try:
                for line in lines:
                    row = load_controller_event(line)
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

    def test_orphan_renewal_input_cannot_certify_empty_release(self):
        receipt = self.run_cleanup_events([{"event": "input_admission", "id": "renew-1",
                                           "intent_token": "renewed-lease"}],
            renewal={"id": "renew-1", "admission": "UNKNOWN",
                     "input_recovery_required": True, "verified_empty_release": False})
        self.assertEqual(receipt["orphan_input_event_ids"], ["renew-1"])
        self.assertEqual(receipt["cover_renewal"]["id"], "renew-1")
        self.assertEqual(receipt["cover_renewal"]["admission"], "UNKNOWN")
        self.assertEqual(receipt["task_effect"], "unknown")
        self.assertTrue(receipt["input_recovery_required"])
        self.assertFalse(receipt["input_terminals_complete"])
        self.assertFalse(receipt["input_releases_verified_empty"])

    def test_unresolved_renewal_with_no_runtime_rows_stays_unknown(self):
        receipt = self.run_cleanup_events([], renewal={"id": "renew-1", "admission": "UNKNOWN",
            "input_recovery_required": True, "verified_empty_release": False})
        self.assertEqual(receipt["cover_renewal"]["id"], "renew-1")
        self.assertTrue(receipt["input_recovery_required"])
        self.assertFalse(receipt["input_terminals_complete"])
        self.assertFalse(receipt["input_releases_verified_empty"])

    def test_global_renewal_release_rechecks_bound_intent_against_events(self):
        token = "renewed-lease"
        accepted = {"event": "accepted", "id": "renew-1", "intent_token": token}
        admitted = {"event": "input_admission", "id": "renew-1", "intent_token": token}
        release = {"verified": True, "keys_down": [], "buttons_down": [],
                   "keys_unknown": [], "key_state_errors": []}
        released = {"event": "input_released", "id": "renew-1", "intent_token": token,
                    "owner_release": {**release, "intent_token": token}}
        terminal = {"event": "terminal", "id": "renew-1", "status": "cancelled",
                    "release": {**release, "intent_token": None}}
        for reported in (token, "different-lease"):
            with self.subTest(reported=reported):
                receipt = self.run_cleanup_events([accepted, admitted, released, terminal],
                    renewal={"id": "renew-1", "admission": "UNKNOWN",
                             "input_recovery_required": False, "verified_empty_release": True,
                             "verified_release_intent_token": reported})
                self.assertEqual(receipt["input_releases_verified_empty"], reported == token)
                self.assertEqual(receipt["input_recovery_required"], reported != token)
                self.assertEqual(receipt["cover_renewal"]["admission"], "UNKNOWN")
                self.assertEqual(receipt["task_effect"], "unknown")

    def test_release_verification_requires_ordered_owned_events(self):
        identifier = "renew-1"
        token = "renewed-lease"
        empty = {"verified": True, "keys_down": [], "buttons_down": [],
                 "keys_unknown": [], "key_state_errors": [], "intent_token": token}
        accepted = {"event": "accepted", "id": identifier, "intent_token": token}
        first = {"event": "input_admission", "id": identifier, "intent_token": token, "key": "Up"}
        second = {**first, "key": "Left"}
        transition = {"event": "input_release_transition", "id": identifier,
                      "intent_token": token}
        released = {"event": "input_released", "id": identifier, "intent_token": token,
                    "owner_release": empty}
        terminal = {"event": "terminal", "id": identifier, "status": "cancelled",
                    "release": {**empty, "intent_token": None}}
        local = {"id": identifier, "admission": "UNKNOWN", "input_recovery_required": False,
                 "verified_empty_release": True, "verified_release_intent_token": token}
        ordered = [accepted, first, transition, second, released, terminal]
        self.assertTrue(operation_release_verified(identifier, ordered, require_intent=True))
        self.assertTrue(self.run_cleanup_events(ordered, renewal=local)["input_releases_verified_empty"])
        cases = {
            "early release": [accepted, first, released, second, terminal],
            "post-terminal admission": [accepted, first, released, terminal, second],
            "pre-acceptance admission": [first, accepted, released, terminal],
            "post-terminal release": [accepted, first, terminal, released],
            "terminal before acceptance": [terminal, accepted],
        }
        for name, events in cases.items():
            with self.subTest(name=name):
                self.assertFalse(operation_release_verified(identifier, events, require_intent=True))
                receipt = self.run_cleanup_events(events, renewal=local)
                self.assertFalse(receipt["input_releases_verified_empty"])
                self.assertTrue(receipt["input_recovery_required"])
                self.assertEqual(receipt["task_effect"], "unknown")

    def test_ordinary_terminal_release_cannot_precede_admission(self):
        accepted = {"event": "accepted", "id": "ordinary-1", "intent_token": "lease-1"}
        admission = {**accepted, "event": "input_admission"}
        terminal = {**accepted, "event": "terminal", "status": "completed",
                    "release": {"verified": True, "keys_down": [], "buttons_down": [],
                                "keys_unknown": [], "key_state_errors": [], "intent_token": "lease-1"}}
        self.assertTrue(self.run_cleanup_events([accepted, admission, terminal])["input_releases_verified_empty"])
        self.assertFalse(self.run_cleanup_events([accepted, terminal, admission])["input_releases_verified_empty"])

    def test_nonfinite_ack_values_are_rejected_by_reader_and_cleanup(self):
        for numeral in ("NaN", "Infinity", "-Infinity", "1e9999"):
            with self.subTest(numeral=numeral):
                receipt = self.run_cleanup_jsonl([
                    '{"event":"accepted","id":"renew-1","intent_token":"renewed-lease","accepted_ns":'
                    + numeral + '}',
                ])
                self.assertIn("non-finite JSON number", receipt["stdout_reader_errors"][0])
                self.assertFalse(receipt["input_releases_verified_empty"])

    def test_matching_release_token_is_retained_as_empty(self):
        receipt = self.run_cleanup("accepted-lease")
        self.assertTrue(receipt["input_release_verified_empty"])

    def test_mismatched_release_token_is_not_certified_empty(self):
        receipt = self.run_cleanup("different-lease")
        self.assertFalse(receipt["input_release_verified_empty"])

    def test_release_without_optional_token_keeps_legacy_id_binding(self):
        receipt = self.run_cleanup()
        self.assertTrue(receipt["input_release_verified_empty"])

    def test_malformed_present_accepted_token_fails_closed_without_input(self):
        for accepted_token in (None, 7, "", [], {}):
            accepted = {"event": "accepted", "id": "source-refresh-0",
                        "intent_token": accepted_token}
            terminal = {"event": "terminal", "id": "source-refresh-0",
                        "release": {"verified": True, "keys_down": [],
                                    "buttons_down": [], "keys_unknown": [],
                                    "key_state_errors": []}}
            with self.subTest(accepted_token=accepted_token):
                receipt = self.run_cleanup_events([accepted, terminal])
                self.assertFalse(receipt["input_releases_verified_empty"])
                self.assertFalse(receipt["input_release_verified_empty"])

    def test_absent_accepted_token_retains_legacy_id_binding(self):
        accepted = {"event": "accepted", "id": "source-refresh-0"}
        terminal = {"event": "terminal", "id": "source-refresh-0",
                    "release": {"verified": True, "keys_down": [],
                                "buttons_down": [], "keys_unknown": [],
                                "key_state_errors": []}}
        receipt = self.run_cleanup_events([accepted, terminal])
        self.assertTrue(receipt["input_releases_verified_empty"])

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

    def test_missing_or_invalid_event_discriminator_fails_closed(self):
        accepted = {"event": "accepted", "id": "command-1",
                    "intent_token": "lease-1"}
        terminal = {
            "event": "terminal", "id": "command-1",
            "release": {"verified": True, "keys_down": [],
                        "buttons_down": [], "keys_unknown": [],
                        "key_state_errors": [], "intent_token": "lease-1"},
        }
        for malformed in ({}, {"event": None}, {"event": 7},
                          {"event": ""}):
            with self.subTest(malformed=malformed):
                receipt = self.run_cleanup_events(
                    [accepted, malformed, terminal])
                self.assertEqual(receipt["invalid_event_record_count"], 1)
                self.assertFalse(receipt["input_event_identities_unambiguous"])
                self.assertFalse(receipt["input_terminals_complete"])
                self.assertFalse(receipt["input_releases_verified_empty"])


    def test_cancelled_without_admission_accepts_empty_terminal_without_lease_token(self):
        receipt = self.run_cleanup(None, status="cancelled")
        self.assertTrue(receipt["input_releases_verified_empty"])

    def test_cancelled_admitted_input_requires_matching_owner_release_receipt(self):
        admission = {
            "event": "input_admission",
            "id": "source-refresh-0",
            "intent_token": "accepted-lease",
        }
        released = {
            "event": "input_released",
            "id": "source-refresh-0",
            "intent_token": "accepted-lease",
            "owner_release": {
                "verified": True,
                "keys_down": [],
                "buttons_down": [],
                "keys_unknown": [],
                "key_state_errors": [],
                "intent_token": "accepted-lease",
            },
        }
        receipt = self.run_cleanup(None, [admission, released], status="cancelled")
        self.assertTrue(receipt["input_releases_verified_empty"])

    def test_cancelled_admitted_input_without_matching_release_is_not_certified(self):
        admission = {
            "event": "input_admission",
            "id": "source-refresh-0",
            "intent_token": "accepted-lease",
        }
        receipt = self.run_cleanup(None, [admission], status="cancelled")
        self.assertFalse(receipt["input_releases_verified_empty"])

    def test_cancelled_admitted_input_rejects_wrong_release_token(self):
        admission = {
            "event": "input_admission",
            "id": "source-refresh-0",
            "intent_token": "accepted-lease",
        }
        released = {
            "event": "input_released",
            "id": "source-refresh-0",
            "intent_token": "other-lease",
            "owner_release": {
                "verified": True,
                "keys_down": [],
                "buttons_down": [],
                "keys_unknown": [],
                "key_state_errors": [],
                "intent_token": "other-lease",
            },
        }
        receipt = self.run_cleanup(None, [admission, released], status="cancelled")
        self.assertFalse(receipt["input_releases_verified_empty"])

    def test_stdout_reader_failure_stops_controller_wait(self):
        with self.assertRaisesRegex(RuntimeError, "stdout capture failed: OSError"):
            reject_stdout_reader_failure({
                "event": "controller_stdout_reader_failed",
                "error_type": "OSError",
            })
        reject_stdout_reader_failure({"event": "observation", "sequence": 1})

    def test_raw_stdout_capture_preserves_exact_bytes_and_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            final_path = Path(directory) / "child-stdout.jsonl"
            raw = (b'{"event":"observation","sequence":1}\r\n'
                   b'{"event":"terminal","id":"cover-0"}\n')
            captured = []
            metadata = {}
            capture_raw_stdout_events(
                io.BytesIO(raw), final_path, metadata, captured.append)

            self.assertEqual(final_path.read_bytes(), raw)
            self.assertEqual(captured, [raw.splitlines(keepends=True)[0],
                                        raw.splitlines(keepends=True)[1]])
            self.assertEqual(metadata["status"], "complete")
            self.assertEqual(metadata["line_count"], 2)
            self.assertEqual(metadata["byte_count"], len(raw))
            self.assertEqual(metadata["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertFalse(Path(str(final_path) + ".partial").exists())

    def test_raw_stdout_capture_reads_text_process_binary_buffer(self):
        with tempfile.TemporaryDirectory() as directory:
            final_path = Path(directory) / "child-stdout.jsonl"
            raw = b'{"event":"ready"}\n'
            script = "import sys; sys.stdout.buffer.write(" + repr(raw) + ")"
            process = subprocess.Popen(
                [sys.executable, "-c", script],
                stdout=subprocess.PIPE,
                text=True,
            )
            try:
                metadata = {}
                capture_raw_stdout_events(
                    process.stdout.buffer, final_path, metadata, lambda line: None)
                self.assertEqual(process.wait(timeout=5), 0)
                self.assertEqual(final_path.read_bytes(), raw)
                self.assertEqual(metadata["status"], "complete")
            finally:
                process.stdout.close()
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=5)

    def test_raw_stdout_capture_retains_bad_line_before_parse_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            final_path = Path(directory) / "child-stdout.jsonl"
            raw = b'{"event":"ok"}\n{not-json}\n'
            captured = {}
            def consume(line):
                if line.startswith(b"{not-json}"):
                    raise ValueError("malformed event")
            with self.assertRaisesRegex(ValueError, "malformed event"):
                capture_raw_stdout_events(
                    io.BytesIO(raw),
                    final_path,captured,consume)

            partial = Path(captured["path"])
            self.assertEqual(partial.read_bytes(), raw)
            self.assertEqual(captured["status"], "incomplete")
            self.assertEqual(captured["line_count"], 2)
            self.assertEqual(captured["byte_count"], len(raw))
            self.assertEqual(captured["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertFalse(final_path.exists())

    def test_failure_preserves_completed_decisions_refreshes_and_controller_events(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            events = [
                {"event": "typed_observation", "sequence": 12, "health": 48},
                {"event": "terminal", "id": "cover-0", "status": "completed"},
            ]
            decisions = [{"iteration": 0, "model_ns": 1500000000,
                          "cover_policy": {"state": "active"}}]
            source_refreshes = [{"iteration": 1, "status": "refused",
                                 "reason": "invalid_observed_health"}]
            scope = ControllerFailureCleanup(Planner(), output)
            scope.observe_output(events, RetiredReader(), None, None, [])
            scope.observe_progress(decisions, source_refreshes)
            raw_capture = {"path": "child-stdout.jsonl",
                           "status": "complete", "byte_count": 20,
                           "line_count": 1, "sha256": "abc123"}
            scope.observe_raw_stdout(raw_capture)
            with self.assertRaisesRegex(RuntimeError, "source refresh refused"):
                with scope:
                    scope.set_stage("source_refresh")
                    raise RuntimeError("source refresh refused")

            progress_path = output / "controller-failure-progress.json"
            progress_bytes = progress_path.read_bytes()
            progress = json.loads(progress_bytes)
            receipt = json.loads((output / "controller-failure.json").read_text())

            self.assertEqual(progress["format"], "map01-controller-failure-progress-v1")
            self.assertEqual(progress["failed_stage"], "source_refresh")
            self.assertEqual(progress["decisions"], decisions)
            self.assertEqual(progress["decision_count"], 1)
            self.assertEqual(progress["source_refreshes"], source_refreshes)
            self.assertEqual(progress["controller_events"], events)
            self.assertEqual(progress["raw_stdout_capture"], raw_capture)
            self.assertEqual(receipt["raw_stdout_capture"], raw_capture)
            self.assertEqual(progress["event_capture_status"], "complete")
            self.assertIn("exact child stdout bytes",
                          progress["controller_event_capture_scope"])
            self.assertEqual(
                receipt["diagnostic_progress"]["sha256"],
                hashlib.sha256(progress_bytes).hexdigest(),
            )
            self.assertFalse((output / "controller-failure-progress.json.tmp").exists())

if __name__ == "__main__":
    unittest.main()
