import json
import tempfile
import unittest
from pathlib import Path

from event_accounting import KNOWN_WARNING, account_events


class EventAccountingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "events.jsonl"
        raw = (Path(__file__).parent / "prior-event-fixture.jsonl").read_text(encoding="utf-8")
        self.rows = [json.loads(line) for line in raw.splitlines() if line.strip()]

    def tearDown(self):
        self.temp.cleanup()

    def evaluate(self, rows):
        self.path.write_text("".join(json.dumps(row) + "\n" for row in rows),
                             encoding="utf-8")
        return account_events(self.path)

    def test_archived_real_stream_classifies_warning_and_accepts_message(self):
        result = self.evaluate(self.rows)
        self.assertEqual("PASS", result["status"])
        self.assertEqual(1, result["assistant_message_count"])
        self.assertEqual("known_skills_context_budget_warning",
                         result["auxiliary_items"][0]["classification"])

    def test_unknown_auxiliary_error_fails_closed(self):
        rows = [dict(row) for row in self.rows]
        rows[2] = {"type": "item.completed", "item": {
            "type": "error", "message": "unrecognized warning"}}
        self.assertEqual("STOP_UNKNOWN_COMPLETED_ITEM",
                         self.evaluate(rows)["status"])

    def test_duplicate_assistant_message_fails_closed(self):
        rows = self.rows + [self.rows[3]]
        self.assertEqual("STOP_ASSISTANT_MESSAGE_COUNT",
                         self.evaluate(rows)["status"])

    def test_missing_turn_fails_closed(self):
        rows = [row for row in self.rows if row.get("type") != "turn.completed"]
        self.assertEqual("STOP_COMPLETED_TURN_OR_USAGE",
                         self.evaluate(rows)["status"])

    def test_missing_usage_fails_closed(self):
        rows = [dict(row) for row in self.rows]
        rows[-1] = {"type": "turn.completed"}
        self.assertEqual("STOP_COMPLETED_TURN_OR_USAGE",
                         self.evaluate(rows)["status"])

    def test_turn_failure_fails_closed(self):
        self.assertEqual("STOP_FAILURE_EVENT",
                         self.evaluate(self.rows + [{"type": "turn.failed"}])["status"])

    def test_malformed_stream_fails_closed(self):
        self.path.write_text('{not-json}\n', encoding="utf-8")
        self.assertEqual("STOP_MALFORMED_EVENT_STREAM",
                         account_events(self.path)["status"])

    def test_warning_message_is_exact_not_substring(self):
        self.assertTrue(KNOWN_WARNING.startswith("Skill descriptions were shortened"))
        rows = [dict(row) for row in self.rows]
        rows[2] = {"type": "item.completed", "item": {
            "type": "error", "message": KNOWN_WARNING + " extra"}}
        self.assertEqual("STOP_UNKNOWN_COMPLETED_ITEM",
                         self.evaluate(rows)["status"])


if __name__ == "__main__":
    unittest.main()
