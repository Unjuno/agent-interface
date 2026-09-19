import copy
import json
from pathlib import Path
import tempfile
import unittest
import io
from unittest.mock import patch

from agent_exchange import run
import agent_exchange


class ExchangeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'image.png').write_bytes(b'synthetic image identity, not GUI evidence')
        self.batch = {'cursor': 1, 'records': [{'event': 'observation', 'sequence': 1,
                      'capture_ns': 10, 'delivery_id': 'delivery:1', 'image': str(self.root/'image.png')}]}
        self.calls = []

    def transport(self, socket, request, **kwargs):
        self.calls.append(copy.deepcopy(request))
        # Exercise real cursor validation: request and action scopes cannot mix.
        from event_cursor_v5 import EventCursor
        cursor = EventCursor()
        cursor.read_until(0, request['events'], timeout=0,
                          action_id=request.get('action_id'), request_id=request.get('read_request_id'))
        if request['command']['op'] == 'clock':
            return {'status': 'boundary', 'cursor': request['after'] + 2,
                    'records': [{'event': 'command', 'command': {'op': 'clock',
                                 'transport_request_id': request['request_id']}},
                                {'event': 'clock', 'sequence': 1, 'runtime_ns': 100}]}
        return {'status': 'boundary', 'cursor': request['after'] + 1,
                'records': [{'event': 'terminal', 'id': 'action', 'status': 'completed',
                             'release': {'verified': True, 'keys_down': [], 'buttons_down': []}}]}

    def call(self, **options):
        return run('test.sock', self.batch, self.root, 'action', [{'op': 'key', 'key': 'Return'}],
                   out=self.root/'attempt', transport=options.pop('transport', self.transport), **options)

    def test_composes_clock_and_exact_reviewed_evidence(self):
        result = self.call(lease_ms=5000)
        self.assertEqual(len(self.calls), 2)
        command = self.calls[-1]['command']
        self.assertEqual(command['valid_until_ns'], 5_000_000_100)
        self.assertEqual(command['decision_evidence'], {'delivery_id': 'delivery:1',
                         'observation_sequence': 1, 'producer': 'assistant'})
        self.assertTrue(result['program_attempted'])
        saved = json.loads((self.root/'attempt/program-request.json').read_text())
        self.assertEqual(saved, self.calls[-1])
        self.assertNotIn('finish_after', command)

    def test_changed_sequence_does_not_send_input(self):
        def changed(*args, **kwargs):
            reply = self.transport(*args, **kwargs)
            reply['records'][-1]['sequence'] = 2
            return reply
        result = self.call(transport=changed)
        self.assertFalse(result['program_attempted'])
        self.assertEqual(len(self.calls), 1)
        self.assertIn('mismatch', result['error'])

    def test_interleaved_or_unattributed_clock_does_not_send(self):
        for mode in ('event', 'identity', 'gap'):
            with self.subTest(mode=mode):
                destination = self.root/mode
                def altered(*args, **kwargs):
                    reply = self.transport(*args, **kwargs)
                    if mode == 'event':
                        reply['records'].insert(0, {'event': 'input_stopped'})
                        reply['cursor'] += 1
                    elif mode == 'identity':
                        reply['records'][0]['command']['transport_request_id'] = 'foreign'
                    else:
                        reply['status'] = 'gap'
                    return reply
                result = run('test.sock', self.batch, self.root, 'action', [{'op': 'observe'}],
                             out=destination, transport=altered)
                self.assertFalse(result['program_attempted'])

    def test_lost_program_reply_is_retained_without_retry(self):
        def lost(*args, **kwargs):
            reply = self.transport(*args, **kwargs)
            if args[1]['command']['op'] == 'submit':
                raise TimeoutError('lost reply')
            return reply
        result = self.call(transport=lost)
        self.assertTrue(result['program_attempted'])
        self.assertEqual(result['status'], 'needs_review')
        self.assertEqual(len(self.calls), 2)
        self.assertTrue((self.root/'attempt/program-request.json').exists())
        with self.assertRaises(FileExistsError):
            self.call()
        self.assertEqual(len(self.calls), 2)

    def test_invalid_parameters_and_missing_source_never_reach_transport(self):
        self.batch['records'][0]['image'] = str(self.root/'absent.png')
        result = self.call()
        self.assertFalse(result['program_attempted'])
        self.assertFalse(self.calls)

    def test_outcome_drain_is_one_bounded_read_and_retains_early_evidence(self):
        for mode in ('ready', 'pending', 'lost', 'foreign', 'gap_cursor'):
            with self.subTest(mode=mode):
                calls = []
                def scripted(socket, request, **kwargs):
                    calls.append((copy.deepcopy(request), kwargs))
                    if request.get('command', {}).get('op') == 'clock':
                        return self.transport(socket, request, **kwargs)
                    if 'command' in request:
                        identity = request['request_id']
                        scripted.identity = identity
                        event = {'event': 'effect_evidence', 'final_program': 'action',
                                 'effect': {'status': 'VERIFIED', 'action_id': 'action'},
                                 'admitted_request': {'transport_request_id': identity, 'declared_action_id': 'action'}}
                        return {'status': 'boundary', 'cursor': request['after'] + 1, 'records': [event]}
                    self.assertEqual(request['timeout'], 0)
                    self.assertEqual(kwargs['timeout'], .25)
                    if mode == 'lost':
                        raise TimeoutError('read reply lost')
                    if mode == 'pending':
                        return {'status': 'timeout', 'cursor': request['after'], 'records': []}
                    event = {'event': 'independent_evaluation', 'final_program': 'action', 'success': True,
                             'admitted_request': {'transport_request_id': 'foreign' if mode == 'foreign' else scripted.identity,
                                                  'declared_action_id': 'action'}}
                    return {'status': 'boundary', 'cursor': request['after'] + (2 if mode == 'gap_cursor' else 1), 'records': [event]}
                result = run('test.sock', self.batch, self.root, 'action', [{'op': 'key', 'key': 'Return'}],
                             boundary='outcome', out=self.root/mode, transport=scripted)
                self.assertEqual(len(calls), 3)
                self.assertNotIn('command', calls[-1][0])
                self.assertEqual(sum(q.get('command', {}).get('op') == 'submit' for q, _ in calls), 1)
                self.assertEqual(result['records'][0]['event'], 'effect_evidence')
                self.assertEqual(result['outcome']['task_success'], True if mode == 'ready' else None)
                if mode in ('pending', 'lost', 'gap_cursor'):
                    self.assertEqual(result['outcome']['state'], 'effect_observed')
                    self.assertEqual(result['outcome']['continuation']['after'], 4)

    def test_cli_review_failure_preserves_attempt_and_does_not_repeat_run(self):
        request = {'out': str(self.root/'attempt'), 'run_directory': str(self.root)}
        result = {'status': 'boundary', 'program_attempted': True, 'records': [{'event': 'terminal'}]}
        output = io.StringIO()
        with patch('sys.argv', ['agent_exchange', '--review']), patch('sys.stdin', io.StringIO(json.dumps(request))), \
                patch('sys.stdout', output), patch.object(agent_exchange, 'run', return_value=result) as action, \
                patch('agent_review.review', side_effect=OSError('report temporarily unavailable')):
            self.assertEqual(agent_exchange.main(), 0)
        action.assert_called_once_with(**request)
        displayed = json.loads(output.getvalue())
        self.assertEqual(displayed['report'], result)
        self.assertIsNone(displayed['image'])
        self.assertIn('unavailable', displayed['review_error'])


if __name__ == '__main__':
    unittest.main()
