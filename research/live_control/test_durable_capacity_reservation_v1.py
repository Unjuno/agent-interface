import tempfile
import unittest
from pathlib import Path
from unittest import mock

import append_checkpoint_v1 as checkpoint
import durable_submit_v4 as durable
from received_continuation_v1 import start


class DurableCapacityReservationTests(unittest.TestCase):
    def prepare(self, path, count):
        durable.initialize(path, start('owned-test-session'))
        for _ in range(count - 1):
            checkpoint.store(path, checkpoint.load(path))

    def test_one_slot_left_refuses_before_transport_or_journal_change(self):
        with tempfile.TemporaryDirectory() as temp, mock.patch.object(checkpoint, 'MAX_RECORDS', 4):
            path = Path(temp) / 'journal'
            self.prepare(path, 3)
            before = path.read_bytes()
            send = mock.Mock(side_effect=AssertionError('must not transmit'))
            with self.assertRaisesRegex(ValueError, 'capacity'):
                durable.run(path, {'command': {'op': 'submit', 'steps': []}}, call=send)
            send.assert_not_called()
            self.assertEqual(path.read_bytes(), before)
            self.assertIsNone(checkpoint.load(path)['pending'])

    def test_clock_with_one_slot_also_refuses_before_transport(self):
        with tempfile.TemporaryDirectory() as temp, mock.patch.object(checkpoint, 'MAX_RECORDS', 4):
            path = Path(temp) / 'journal'
            self.prepare(path, 3)
            before = path.read_bytes()
            send = mock.Mock(side_effect=AssertionError('must not transmit'))
            with self.assertRaisesRegex(ValueError, 'capacity'):
                durable.run(path, {'command': {'op': 'clock'}}, call=send)
            send.assert_not_called()
            self.assertEqual(path.read_bytes(), before)

    def test_two_slots_left_commits_reply_and_verified_release(self):
        with tempfile.TemporaryDirectory() as temp, mock.patch.object(checkpoint, 'MAX_RECORDS', 4):
            path = Path(temp) / 'journal'
            self.prepare(path, 2)
            def reply(_session, request, timeout):
                command = dict(request['command'], transport_request_id=request['request_id'])
                identifier = command['id']
                records = [{'event': 'command', 'command': command},
                           {'event': 'accepted', 'id': identifier},
                           {'event': 'terminal', 'id': identifier,
                            'release': {'verified': True, 'keys_down': [], 'buttons_down': []}}]
                return {'status': 'boundary', 'cursor': request['after'] + len(records), 'records': records}
            result = durable.run(path, {'command': {'op': 'submit', 'steps': []}}, call=reply)
            self.assertIsNone(result['state']['pending'])
            self.assertTrue(result['state']['last_resolution']['terminal']['release']['verified'])
            self.assertEqual(checkpoint.inspect(path)[1], 4)

    def test_pending_reconciliation_can_use_last_slot(self):
        with tempfile.TemporaryDirectory() as temp, mock.patch.object(checkpoint, 'MAX_RECORDS', 4):
            path = Path(temp) / 'journal'
            self.prepare(path, 2)
            state = checkpoint.load(path)
            command = {'op': 'submit', 'id': 'existing-action', 'steps': []}
            state['pending'] = {'request': {'command': command, 'request_id': 'existing-request'},
                                'write_state': 'may_have_been_sent', 'echo_seen': False,
                                'accepted': False, 'conflict': False}
            checkpoint.store(path, state)
            def reply(_session, request, timeout):
                records = [{'event':'command', 'command': dict(command, transport_request_id='existing-request')},
                           {'event':'accepted', 'id':'existing-action'},
                           {'event':'terminal', 'id':'existing-action',
                            'release':{'verified':True,'keys_down':[],'buttons_down':[]}}]
                return {'status':'boundary','cursor':request['after'] + len(records),'records':records}
            result = durable.run(path, {}, call=reply)
            self.assertIsNone(result['state']['pending'])
            self.assertEqual(checkpoint.inspect(path)[1], 4)

    def test_command_free_recovery_read_can_use_last_slot(self):
        with tempfile.TemporaryDirectory() as temp, mock.patch.object(checkpoint, 'MAX_RECORDS', 4):
            path = Path(temp) / 'journal'
            self.prepare(path, 3)
            def reply(_session, request, timeout):
                return {'status': 'timeout', 'cursor': request['after'], 'records': []}
            durable.run(path, {}, call=reply)
            self.assertEqual(checkpoint.inspect(path)[1], 4)

if __name__ == '__main__':
    unittest.main()
