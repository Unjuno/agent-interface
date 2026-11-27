import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runtime.guarded_x11_v1.receipt_journal import ReceiptJournal, ReceiptJournalError


class ReceiptJournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'retention.jsonl'

    def test_append_fsyncs_and_reopen_resolves_exact_payload(self):
        payload = {'status': 'completed', 'release': {'verified': True}}
        with patch('runtime.guarded_x11_v1.receipt_journal.os.fsync', wraps=os.fsync) as sync:
            with ReceiptJournal(self.path) as journal:
                reference = journal.append('result-action-1', 'result', payload)
                self.assertEqual(journal.lookup(reference), payload)
            self.assertEqual(sync.call_count, 1)
        self.assertEqual(ReceiptJournal.read(self.path, 'result-action-1'), payload)
        row = json.loads(self.path.read_text(encoding='utf-8').splitlines()[0])
        self.assertEqual(row['sequence'], 1)
        self.assertEqual(row['reference'], 'result-action-1')

    def test_duplicate_reference_does_not_append_or_replace_receipt(self):
        with ReceiptJournal(self.path) as journal:
            journal.append('observation-1', 'observation', {'sequence': 1})
            before = self.path.read_bytes() if os.name != 'nt' else b''
            with self.assertRaises(ReceiptJournalError):
                journal.append('observation-1', 'observation', {'sequence': 2})
            if os.name != 'nt':
                self.assertEqual(self.path.read_bytes(), before)
            self.assertEqual(journal.lookup('observation-1'), {'sequence': 1})

    def test_torn_final_record_refuses_reopen(self):
        with ReceiptJournal(self.path) as journal:
            journal.append('event-1', 'event', {'ok': True})
        with self.path.open('ab') as stream:
            stream.write(b'{"schema":"partial')
        with self.assertRaisesRegex(ReceiptJournalError, 'torn'):
            ReceiptJournal(self.path)

    def test_fsync_failure_marks_writer_uncertain_and_blocks_replay(self):
        journal = ReceiptJournal(self.path)
        self.addCleanup(journal.close)
        with patch('runtime.guarded_x11_v1.receipt_journal.os.fsync', side_effect=OSError('injected')):
            with self.assertRaisesRegex(ReceiptJournalError, 'append or fsync'):
                journal.append('execution-1', 'execution', {'released': True})
        with self.assertRaisesRegex(ReceiptJournalError, 'uncertain'):
            journal.lookup('execution-1')
        with self.assertRaisesRegex(ReceiptJournalError, 'uncertain'):
            journal.append('execution-2', 'execution', {'released': True})

    def test_reopen_continues_sequence_and_hash_chain(self):
        with ReceiptJournal(self.path) as journal:
            journal.append('event-1', 'event', {'step': 1})
        with ReceiptJournal(self.path) as journal:
            journal.append('event-2', 'event', {'step': 2})
            self.assertEqual(journal.lookup('event-1'), {'step': 1})
            self.assertEqual(journal.lookup('event-2'), {'step': 2})
        rows = [json.loads(line) for line in self.path.read_text(encoding='utf-8').splitlines()]
        self.assertEqual([row['sequence'] for row in rows], [1, 2])
        self.assertEqual(rows[1]['previous_sha256'], rows[0]['record_sha256'])

    def test_lookup_detects_external_payload_tampering_and_fails_closed(self):
        with ReceiptJournal(self.path) as journal:
            journal.append('event-1', 'event', {'step': 1})
        self.path.write_bytes(self.path.read_bytes().replace(b'"step":1', b'"step":2'))
        with self.assertRaises(ReceiptJournalError):
            ReceiptJournal.read(self.path, 'event-1')

    def test_external_append_is_detected_before_next_write(self):
        journal = ReceiptJournal(self.path)
        self.addCleanup(journal.close)
        journal.append('event-1', 'event', {'step': 1})
        # Simulate a process that ignores the OS writer lock. On Windows it
        # cannot reopen an exclusively locked handle, so use an OS-level
        # position/write through the existing stream handle.
        journal._stream.seek(0, os.SEEK_END)
        journal._stream.write(b'{}\n')
        journal._stream.flush()
        with self.assertRaisesRegex(ReceiptJournalError, 'changed outside'):
            journal.append('event-2', 'event', {'step': 2})

    def test_second_process_cannot_open_writer_while_owner_is_active(self):
        journal = ReceiptJournal(self.path)
        self.addCleanup(journal.close)
        code = '''
from runtime.guarded_x11_v1.receipt_journal import ReceiptJournal, ReceiptJournalError
import sys
try:
    ReceiptJournal(sys.argv[1])
except ReceiptJournalError:
    print("LOCKED")
    sys.exit(0)
print("UNLOCKED")
sys.exit(2)
'''
        result = subprocess.run([sys.executable, '-c', code, str(self.path)],
                                text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn('LOCKED', result.stdout)


if __name__ == '__main__':
    unittest.main()
