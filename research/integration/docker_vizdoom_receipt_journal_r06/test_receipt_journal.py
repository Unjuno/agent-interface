import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from receipt_journal import JournalError, ReceiptJournal


class ReceiptJournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "receipts.jsonl"

    def test_round_trip_lookup_order_and_reopen(self):
        journal = ReceiptJournal(self.path)
        first = {"status": "completed", "release": {"verified": True}}
        second = {"position": [4.5, -2], "passed": True}
        journal.append("compiled-run-1-execution", "execution", first)
        journal.append("compiled-run-2-effect", "effect", second)
        first["status"] = "changed after append"
        reopened = ReceiptJournal(self.path)
        self.assertEqual(reopened.references(),
                         ("compiled-run-1-execution", "compiled-run-2-effect"))
        self.assertEqual(reopened.lookup("compiled-run-1-execution"),
                         {"status": "completed", "release": {"verified": True}})
        self.assertEqual(reopened.lookup("compiled-run-2-effect"), second)

    def test_duplicate_reference_is_refused_without_new_record(self):
        journal = ReceiptJournal(self.path)
        journal.append("execution-1", "execution", {"n": 1})
        size = self.path.stat().st_size
        with self.assertRaises(JournalError):
            journal.append("execution-1", "execution", {"n": 2})
        self.assertEqual(self.path.stat().st_size, size)
        self.assertEqual(journal.lookup("execution-1"), {"n": 1})

    def test_non_json_and_nan_payloads_are_refused_before_append(self):
        journal = ReceiptJournal(self.path)
        for value in (object(), {"x": float("nan")}):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(JournalError):
                    journal.append("bad", "event", value)
        self.assertFalse(self.path.exists())

    def test_torn_final_line_rejects_entire_journal(self):
        journal = ReceiptJournal(self.path)
        journal.append("valid-prefix", "event", {"ok": True})
        with self.path.open("ab") as stream:
            stream.write(b'{"schema":"partial')
        with self.assertRaisesRegex(JournalError, "torn journal line"):
            ReceiptJournal(self.path)

    def test_payload_tamper_rejects_entire_journal(self):
        journal = ReceiptJournal(self.path)
        journal.append("event-1", "event", {"value": 1})
        row = json.loads(self.path.read_text(encoding="utf-8"))
        row["payload"]["value"] = 2
        self.path.write_text(json.dumps(row, separators=(",", ":")) + "\n",
                             encoding="utf-8")
        with self.assertRaisesRegex(JournalError, "payload hash mismatch"):
            ReceiptJournal(self.path)

    def test_hash_chain_and_sequence_are_checked(self):
        journal = ReceiptJournal(self.path)
        journal.append("event-1", "event", {"value": 1})
        journal.append("event-2", "event", {"value": 2})
        rows = [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines()]
        rows[1]["sequence"] = 3
        self.path.write_text("\n".join(json.dumps(row, separators=(",", ":"))
                                       for row in rows) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(JournalError, "sequence gap"):
            ReceiptJournal(self.path)

    def test_external_change_freezes_live_writer(self):
        journal = ReceiptJournal(self.path)
        journal.append("event-1", "event", {"value": 1})
        with self.path.open("ab") as stream:
            stream.write(b"foreign")
        with self.assertRaisesRegex(JournalError, "changed outside"):
            journal.append("event-2", "event", {"value": 2})
        with self.assertRaisesRegex(JournalError, "uncertain"):
            journal.lookup("event-1")

    def test_open_failure_freezes_live_writer_and_refuses_lookup(self):
        journal = ReceiptJournal(self.path)
        with patch.object(Path, "open", side_effect=OSError("injected open failure")):
            with self.assertRaisesRegex(JournalError, "append or flush failed"):
                journal.append("event-1", "event", {"value": 1})
        with self.assertRaisesRegex(JournalError, "uncertain"):
            journal.lookup("event-1")
        self.assertFalse(self.path.exists())

    def test_missing_reference_does_not_change_journal(self):
        journal = ReceiptJournal(self.path)
        with self.assertRaises(KeyError):
            journal.lookup("missing")
        self.assertFalse(self.path.exists())


if __name__ == "__main__":
    unittest.main()
