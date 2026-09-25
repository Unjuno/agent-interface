import copy
import json
from pathlib import Path
import tempfile
import unittest

from research.integration.event_inbox_reader_v1.reader import read_pending
from research.live_control.delivery_ledger_v2 import DeliveryLedger


class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'delivered.jsonl'
        self.ledger = DeliveryLedger()

    def line(self, event):
        return (json.dumps(self.ledger.prepare(event))+'\n').encode()

    def read(self, **kw):
        return read_pending(self.path, stream_id='owned-run-1', **kw)

    def test_existing_producer_pagination_repeated_read_and_no_ack(self):
        data = b''.join(self.line({'event': name, 'detail': name})
                        for name in ('observation', 'accepted', 'terminal'))
        self.path.write_bytes(data)
        first = self.read(max_records=2)
        self.assertEqual(first, self.read(max_records=2))
        self.assertEqual(first['tail_state'], 'limit')
        cursor = copy.deepcopy(first['next_cursor'])
        second = self.read(cursor=cursor)
        self.assertEqual([r['event'] for r in first['records']+second['records']],
                         ['observation', 'accepted', 'terminal'])
        self.assertEqual(cursor, first['next_cursor'])
        self.assertEqual(second['tail_state'], 'end')
        self.assertFalse(second['acknowledged'])
        self.assertEqual(second['authority'], 'none')
        self.assertEqual(self.path.read_bytes(), data)

    def test_valid_json_without_newline_waits_until_append(self):
        line = self.line({'event': 'terminal', 'detail': '保存済み'})
        self.path.write_bytes(line[:-1])
        partial = self.read()
        self.assertEqual(partial['records'], [])
        self.assertEqual(partial['tail_state'], 'incomplete')
        self.assertEqual(partial['next_cursor']['offset'], 0)
        with self.path.open('ab') as stream:
            stream.write(b'\n')
        self.assertEqual(len(self.read(cursor=partial['next_cursor'])['records']), 1)

    def test_restart_duplicate_and_gap_do_not_skip_or_advance(self):
        first = self.line({'event': 'accepted'})
        for bad in (b'{"event":"terminal","delivery_id":"delivery:1"}\n',
                    b'{"event":"terminal","delivery_id":"delivery:3"}\n', b'bad\n',
                    b'{"event":"terminal","delivery_id":"delivery:9","delivery_id":"delivery:2"}\n',
                    b'{"event":"terminal","delivery_id":"delivery:2","value":NaN}\n'):
            self.path.write_bytes(first+bad)
            result = self.read()
            self.assertEqual(len(result['records']), 1)
            self.assertEqual(result['tail_state'], 'blocked')
            self.assertEqual(result['next_cursor']['offset'], len(first))
            again = self.read(cursor=result['next_cursor'])
            self.assertEqual(again['records'], [])
            self.assertEqual(again['next_cursor'], result['next_cursor'])

    def test_changed_prefix_and_wrong_stream_rejected(self):
        data = self.line({'event': 'accepted'})
        self.path.write_bytes(data)
        cursor = self.read()['next_cursor']
        wrong = dict(cursor, stream_id='other-run')
        with self.assertRaisesRegex(ValueError, 'INVALID_CURSOR'):
            self.read(cursor=wrong)
        with self.assertRaisesRegex(ValueError, 'CURSOR_POSITION_MISMATCH'):
            self.read(cursor=dict(cursor, next_sequence=8))
        for replacement in (b'', data.replace(b'accepted', b'rejected')):
            self.path.write_bytes(replacement)
            with self.assertRaisesRegex(ValueError, 'CURSOR_PREFIX_CHANGED'):
                self.read(cursor=cursor)

    def test_bounds_are_explicit(self):
        self.path.write_bytes(self.line({'event':'terminal'}))
        for options in ({'max_records':True}, {'max_bytes':0}, {'max_records':129}):
            with self.assertRaisesRegex(ValueError, 'INVALID_READ_BOUND'):
                self.read(**options)
        with self.assertRaisesRegex(ValueError, 'STREAM_READ_BOUND_EXCEEDED'):
            self.read(max_bytes=1)


if __name__ == '__main__':
    unittest.main()
