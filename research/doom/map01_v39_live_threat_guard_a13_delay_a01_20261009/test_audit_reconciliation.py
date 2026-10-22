import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
AUDITOR = HERE / "audit_live_reconciliation.py"


def verified_empty(reason="release"):
    return {
        "event": "owner_release",
        "reason": reason,
        "verified": True,
        "keys_down": [],
        "buttons_down": [],
        "keys_unknown": [],
    }


class CancellationCustodyReconciliationTests(unittest.TestCase):
    def run_audit(self, rows):
        with tempfile.TemporaryDirectory() as temporary:
            events_path = Path(temporary) / "events.json"
            events_path.write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(AUDITOR), "--events", str(events_path),
                 "--guard-id", "cover-2", "--useful-feedback-during-pending", "false"],
                capture_output=True, text=True, check=False)

    def test_terminal_empty_release_accounts_for_cancel_after_input_is_already_empty(self):
        rows = [
            {"event": "cancel_requested", "id": "cover-0", "matched": True},
            {"event": "terminal", "id": "cover-0", "status": "cancelled",
             "release": verified_empty()},
            {"event": "cancel_requested", "id": "cover-2", "matched": True},
            {"event": "input_released", "id": "cover-2",
             "intent_token": "lease-2",
             "owner_release": {**verified_empty("cancelled"),
                               "intent_token": "lease-2"}},
            {"event": "terminal", "id": "cover-2", "status": "cancelled",
             "release": verified_empty(),
             "interruption": {"intent_token": "lease-2",
                              "record": {**verified_empty("cancelled"),
                                         "intent_token": "lease-2"}}},
        ]

        result = self.run_audit(rows)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "HOLD")

    def test_guard_cancel_without_its_explicit_empty_release_is_not_custodied(self):
        rows = [
            {"event": "cancel_requested", "id": "cover-2", "matched": True},
            {"event": "terminal", "id": "cover-2", "status": "cancelled",
             "release": verified_empty(),
             "interruption": {"intent_token": "lease-2",
                              "record": {**verified_empty("cancelled"),
                                         "intent_token": "lease-2"}}},
        ]

        result = self.run_audit(rows)

        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["status"], "FAIL")

    def test_terminal_empty_release_does_not_hide_missing_active_lease_event(self):
        rows = [
            {"event": "cancel_requested", "id": "cover-1", "matched": True},
            {"event": "terminal", "id": "cover-1", "status": "cancelled",
             "release": verified_empty(),
             "interruption": {"intent_token": "lease-1",
                              "record": verified_empty("cancelled")}},
            {"event": "cancel_requested", "id": "cover-2", "matched": True},
            {"event": "input_released", "id": "cover-2",
             "intent_token": "lease-2",
             "owner_release": {**verified_empty("cancelled"),
                               "intent_token": "lease-2"}},
            {"event": "terminal", "id": "cover-2", "status": "cancelled",
             "release": verified_empty(),
             "interruption": {"intent_token": "lease-2",
                              "record": {**verified_empty("cancelled"),
                                         "intent_token": "lease-2"}}},
        ]

        result = self.run_audit(rows)

        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
