import copy
import json
import unittest
from pathlib import Path

from .audit_result_v3 import (
    has_per_key_release_timestamps, load_pinned_inputs, validate_result,
)


HERE = Path(__file__).resolve().parent


class CompleteResultAuditV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (cls.freeze, cls.events, cls.owner, cls.report,
         cls.prior, cls.prereg) = load_pinned_inputs()
        cls.result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))

    def test_original_result_matches_all_pinned_claims(self):
        self.assertTrue(validate_result(
            self.result, self.events, self.owner, self.report, self.prior,
            self.prereg, self.freeze))

    def test_independent_loader_checks_and_reads_exact_frozen_inputs(self):
        freeze, events, owner, report, prior, prereg = load_pinned_inputs()
        self.assertEqual(freeze["frozen_main"], "6149fc1856ce86de41b168de8ca12690347f524d")
        self.assertEqual(prereg["allocation_id"], freeze["allocation_id"])
        self.assertEqual(len(events), 634)
        self.assertEqual(len(owner), 13)
        self.assertTrue(prior["formal_pass"])

    def test_each_previously_unchecked_result_claim_is_rejected_when_changed(self):
        mutations = {
            "main_commit": "0" * 40,
            "allocation_id": "other-allocation",
            "prior_audit_formal_pass": False,
            "all_cancellation_rows": [],
            "per_key_release_measurement_events": 999,
            "independent_useful_feedback_timestamp": True,
            "decision": "PASS_ALL",
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                result = copy.deepcopy(self.result)
                result[field] = value
                with self.assertRaisesRegex(ValueError, field):
                    validate_result(
                        result, self.events, self.owner, self.report,
                        self.prior, self.prereg, self.freeze)

    def test_terminal_release_before_cancel_is_rejected_even_without_interruption(self):
        events = copy.deepcopy(self.events)
        cancel = next(row for row in events if row.get("event") == "cancel_requested"
                      and row.get("id") == "cover-0")
        terminal = next(row for row in events if row.get("event") == "terminal"
                        and row.get("id") == "cover-0")
        self.assertIsNone((terminal.get("interruption") or {}).get("record"))
        cancel["requested_ns"] = terminal["release"]["verified_ns"] + 1
        with self.assertRaisesRegex(ValueError, "chronology"):
            validate_result(
                self.result, events, self.owner, self.report, self.prior,
                self.prereg, self.freeze)

    def test_freeze_allocation_must_match_preregistration(self):
        prereg = copy.deepcopy(self.prereg)
        prereg["allocation_id"] = "different-allocation"
        with self.assertRaisesRegex(ValueError, "preregistration allocation"):
            validate_result(
                self.result, self.events, self.owner, self.report, self.prior,
                prereg, self.freeze)

    def test_current_v12_per_key_field_names_are_recognized(self):
        attempts = [{"attempt": 1, "keyrelease_started_ns": 10,
                     "sync_returned_ns": 12, "keymap_sampled_ns": 13}]
        self.assertTrue(has_per_key_release_timestamps([{
            "event": "owner_release",
            "key_release_attempts": {"65": {"attempts": attempts}},
            "key_release_intervals_ns": [{"keycode": 65, "interval_ns": [10, 13]}],
        }]))
        self.assertTrue(has_per_key_release_timestamps([{
            "event": "owner_explicit_keyup",
            "server_keyup_attempt_count": 1,
            "server_keyup_attempts": attempts,
        }]))

    def test_empty_or_malformed_receipts_are_not_counted_as_measurements(self):
        rows = [
            {"key_release_attempts": {"65": {"attempts": []}}},
            {"key_release_attempts": {"65": {"attempts": [
                {"keyrelease_started_ns": None, "sync_returned_ns": 12,
                 "keymap_sampled_ns": 13}
            ]}}},
            {"server_keyup_attempts": [
                {"keyrelease_started_ns": 10, "sync_returned_ns": "12",
                 "keymap_sampled_ns": 13}
            ]},
            {"key_release_intervals_ns": [{"interval_ns": [10, None]}]},
        ]
        self.assertFalse(has_per_key_release_timestamps(rows))


if __name__ == "__main__":
    unittest.main(verbosity=2)
