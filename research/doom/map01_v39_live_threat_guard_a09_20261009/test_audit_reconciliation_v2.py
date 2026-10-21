"""Regression tests for duplicate event-ID rejection in the A09 audit."""
import unittest
import subprocess
import sys
from pathlib import Path

from audit_live_reconciliation_v2 import audit_archive, reconcile_cancellation_custody


def release(reason="cancelled", token="lease-2"):
    return {
        "event": "owner_release",
        "reason": reason,
        "verified": True,
        "keys_down": [],
        "buttons_down": [],
        "keys_unknown": [],
        "intent_token": token,
    }


def valid_guard_rows():
    return [
        {"event": "cancel_requested", "id": "cover-2", "matched": True},
        {"event": "input_released", "id": "cover-2", "intent_token": "lease-2",
         "owner_release": release()},
        {"event": "terminal", "id": "cover-2", "status": "cancelled",
         "release": release("release", None),
         "interruption": {"intent_token": "lease-2", "record": release()}},
    ]


class DuplicateEventIdTests(unittest.TestCase):
    def assert_custody_rejected(self, rows):
        custody = reconcile_cancellation_custody(rows, "cover-2", ["cover-2"])
        self.assertEqual(custody["custody_status"], "FAIL_CUSTODY", custody)

    def test_duplicate_cancel_id_is_rejected(self):
        rows = valid_guard_rows()
        self.assert_custody_rejected(rows + [dict(rows[0])])

    def test_duplicate_terminal_id_is_rejected_in_either_row_order(self):
        valid = valid_guard_rows()[2]
        malformed = {"event": "terminal", "id": "cover-2", "status": "failed"}
        for rows in ([*valid_guard_rows()[:2], malformed, valid],
                     [*valid_guard_rows(), malformed]):
            with self.subTest(rows=rows[-2:]):
                self.assert_custody_rejected(rows)

    def test_observed_cancel_set_must_match_report_bound_expected_ids(self):
        custody = reconcile_cancellation_custody(
            valid_guard_rows(), "cover-2", ["cover-0", "cover-2"])
        self.assertEqual(custody["missing_cancel_ids"], ["cover-0"])
        self.assertEqual(custody["custody_status"], "FAIL_CUSTODY")

    def test_unexpected_cancel_id_is_rejected(self):
        rows = valid_guard_rows()
        rows.extend([
            {"event": "cancel_requested", "id": "cover-3", "matched": True},
            {"event": "terminal", "id": "cover-3", "status": "cancelled",
             "release": release("release", None)},
        ])
        custody = reconcile_cancellation_custody(rows, "cover-2", ["cover-2"])
        self.assertEqual(custody["unexpected_cancel_ids"], ["cover-3"])
        self.assertEqual(custody["custody_status"], "FAIL_CUSTODY")

    def test_unmatched_cancel_is_not_reported_as_matched(self):
        rows = valid_guard_rows()
        rows[0]["matched"] = False
        custody = reconcile_cancellation_custody(rows, "cover-2", ["cover-2"])
        self.assertEqual(custody["custody_status"], "FAIL_CUSTODY")
        self.assertEqual(custody["matched_cancel_count"], 0)
        self.assertEqual(custody["matched_cancel_ids"], [])

    def test_expected_id_list_rejects_duplicates(self):
        custody = reconcile_cancellation_custody(
            valid_guard_rows(), "cover-2", ["cover-2", "cover-2"])
        self.assertEqual(custody["errors"], ["invalid_expected_cancel_ids"])

    def test_duplicate_release_id_is_rejected_in_either_row_order(self):
        valid = valid_guard_rows()[1]
        malformed = {"event": "input_released", "id": "cover-2",
                     "intent_token": "wrong", "owner_release": release(token="wrong")}
        for rows in ([valid_guard_rows()[0], malformed, valid, valid_guard_rows()[2]],
                     valid_guard_rows() + [malformed]):
            with self.subTest(rows=rows[1:4]):
                self.assert_custody_rejected(rows)


class ArchiveBoundCustodyTests(unittest.TestCase):
    def test_public_archive_reconciles_custody_without_classifying_task_effect(self):
        archive = Path(__file__).resolve().parent / "A09_RAW_SANITIZED.tar.gz"
        result = audit_archive(archive)
        self.assertEqual(result["custody_status"], "PASS_CUSTODY")
        self.assertEqual(result["custody"]["expected_cancel_count"], 10)
        self.assertEqual(result["custody"]["matched_cancel_count"], 10)
        self.assertEqual(result["research_gate_status"],
                         "NOT_CLASSIFIED_BY_THIS_CUSTODY_AUDIT")
        self.assertNotIn("useful_feedback_during_pending_model", result)

    def test_cli_does_not_accept_caller_supplied_task_effect_flag(self):
        script = Path(__file__).resolve().parent / "audit_live_reconciliation_v2.py"
        archive = Path(__file__).resolve().parent / "A09_RAW_SANITIZED.tar.gz"
        result = subprocess.run(
            [sys.executable, str(script), "--archive", str(archive),
             "--useful-feedback-during-pending", "true"],
            capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")

if __name__ == "__main__":
    unittest.main()
