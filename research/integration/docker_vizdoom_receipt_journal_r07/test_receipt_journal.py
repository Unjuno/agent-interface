import json
import tempfile
import unittest
import io
from pathlib import Path
from unittest.mock import patch

from receipt_journal import JournalError, ReceiptJournal


class ReceiptJournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "receipts.jsonl"
        self.journals = []

    def tearDown(self):
        for journal in reversed(self.journals):
            journal.close()

    def open_journal(self):
        journal = ReceiptJournal(self.path)
        self.journals.append(journal)
        return journal

    def test_round_trip_lookup_order_and_reopen(self):
        journal = self.open_journal()
        first = {"status": "completed", "release": {"verified": True}}
        second = {"position": [4.5, -2], "passed": True}
        journal.append("compiled-run-1-execution", "execution", first)
        journal.append("compiled-run-2-effect", "effect", second)
        first["status"] = "changed after append"
        journal.close()
        reopened = self.open_journal()
        self.assertEqual(reopened.references(),
                         ("compiled-run-1-execution", "compiled-run-2-effect"))
        self.assertEqual(reopened.lookup("compiled-run-1-execution"),
                         {"status": "completed", "release": {"verified": True}})
        self.assertEqual(reopened.lookup("compiled-run-2-effect"), second)

    def test_writer_lock_refuses_second_writer_and_releases_on_close(self):
        first = self.open_journal()
        with self.assertRaisesRegex(JournalError, "another journal writer"):
            ReceiptJournal(self.path)
        first.close()
        second = self.open_journal()
        second.append("event-1", "event", {"ok": True})

    def test_duplicate_reference_is_refused_without_new_record(self):
        journal = self.open_journal()
        journal.append("execution-1", "execution", {"n": 1})
        size = self.path.stat().st_size
        with self.assertRaises(JournalError):
            journal.append("execution-1", "execution", {"n": 2})
        self.assertEqual(self.path.stat().st_size, size)
        self.assertEqual(journal.lookup("execution-1"), {"n": 1})

    def test_non_json_and_nan_payloads_are_refused_before_append(self):
        journal = self.open_journal()
        for value in (object(), {"x": float("nan")}):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(JournalError):
                    journal.append("bad", "event", value)
        self.assertEqual(self.path.read_bytes(), b"")

    def test_torn_final_line_rejects_entire_journal(self):
        journal = self.open_journal()
        journal.append("valid-prefix", "event", {"ok": True})
        journal.close()
        with self.path.open("ab") as stream:
            stream.write(b'{"schema":"partial')
        with self.assertRaisesRegex(JournalError, "torn journal line"):
            ReceiptJournal(self.path)

    def test_payload_tamper_rejects_entire_journal(self):
        journal = self.open_journal()
        journal.append("event-1", "event", {"value": 1})
        journal.close()
        row = json.loads(self.path.read_text(encoding="utf-8"))
        row["payload"]["value"] = 2
        self.path.write_text(json.dumps(row, separators=(",", ":")) + "\n",
                             encoding="utf-8")
        with self.assertRaisesRegex(JournalError, "payload hash mismatch"):
            ReceiptJournal(self.path)

    def test_hash_chain_and_sequence_are_checked(self):
        journal = self.open_journal()
        journal.append("event-1", "event", {"value": 1})
        journal.append("event-2", "event", {"value": 2})
        journal.close()
        rows = [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines()]
        rows[1]["sequence"] = 3
        self.path.write_text("\n".join(json.dumps(row, separators=(",", ":"))
                                       for row in rows) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(JournalError, "sequence gap"):
            ReceiptJournal(self.path)

    def test_external_change_freezes_live_writer(self):
        journal = self.open_journal()
        journal.append("event-1", "event", {"value": 1})
        with self.path.open("ab") as stream:
            stream.write(b"foreign")
        with self.assertRaisesRegex(JournalError, "changed outside locked writer"):
            journal.append("event-2", "event", {"value": 2})
        with self.assertRaisesRegex(JournalError, "uncertain"):
            journal.lookup("event-1")

    def test_append_write_failure_freezes_live_writer(self):
        journal = self.open_journal()
        original = journal._stream
        class FailingWrite:
            def __getattr__(self, name):
                return getattr(original, name)
            def write(self, data):
                raise OSError("injected write failure")
        journal._stream = FailingWrite()
        try:
            with self.assertRaisesRegex(JournalError, "append or flush failed"):
                journal.append("event-1", "event", {"value": 1})
            with self.assertRaisesRegex(JournalError, "uncertain"):
                journal.lookup("event-1")
        finally:
            journal._stream = original

    def test_open_failure_is_refused(self):
        with patch.object(Path, "open", side_effect=OSError("injected open failure")):
            with self.assertRaisesRegex(JournalError, "open or scan failed"):
                ReceiptJournal(self.path)

    def test_flush_failure_freezes_live_writer(self):
        journal = self.open_journal()
        original = journal._stream
        class FailingFlush:
            def __getattr__(self, name):
                return getattr(original, name)
            def flush(self):
                raise OSError("injected flush failure")
        journal._stream = FailingFlush()
        try:
            with self.assertRaisesRegex(JournalError, "append or flush failed"):
                journal.append("event-1", "event", {"value": 1})
            with self.assertRaisesRegex(JournalError, "uncertain"):
                journal.lookup("event-1")
        finally:
            journal._stream = original

    def test_missing_reference_does_not_change_journal(self):
        journal = self.open_journal()
        with self.assertRaises(KeyError):
            journal.lookup("missing")
        self.assertEqual(self.path.read_bytes(), b"")


if __name__ == "__main__":
    unittest.main()
