import json
import tempfile
import unittest
from pathlib import Path

from runtime.guarded_x11_v1.bridge import NativeHandleBridge
from runtime.guarded_x11_v1.receipt_journal import ReceiptJournal


class BridgeRetentionTests(unittest.TestCase):
    def test_close_releases_journal_after_backend_close(self):
        with tempfile.TemporaryDirectory() as directory:
            bridge = object.__new__(NativeHandleBridge)
            bridge.out = Path(directory)
            bridge.retention_mode = 'journal'
            bridge._receipt_journal = None
            bridge._closed = False
            bridge._target_queries = None
            bridge._observations = None
            bridge.backend = type('Backend', (), {'close':lambda self: {'status':'closed'}})()
            bridge._save('result-before.json', {'status':'done'})
            bridge.close()
            self.assertTrue(bridge._closed)
            self.assertTrue(Path(directory, 'retention.jsonl').exists())
            with ReceiptJournal(Path(directory, 'retention.jsonl')) as reopened:
                self.assertEqual(reopened.references(), ('result-before',))

    def test_journal_mode_appends_named_receipt_without_emitting_per_receipt_json(self):
        with tempfile.TemporaryDirectory() as directory:
            bridge = object.__new__(NativeHandleBridge)
            bridge.out = Path(directory)
            bridge.retention_mode = 'journal'
            bridge._receipt_journal = None
            payload = {'status': 'completed', 'release': {'verified': True}}

            reference = bridge._save('result-action-1.json', payload)

            self.assertEqual(reference, 'result-action-1')
            self.assertFalse((Path(directory) / 'result-action-1.json').exists())
            self.assertEqual(bridge.read_retained(reference), payload)
            bridge._receipt_journal.close()
            bridge._receipt_journal = None
            journal_path = Path(directory) / 'retention.jsonl'
            rows = [json.loads(line) for line in journal_path.read_text(encoding='utf-8').splitlines()]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['reference'], 'result-action-1')
            self.assertEqual(rows[0]['kind'], 'result')


if __name__ == '__main__':
    unittest.main()
