"""Construction-only fabricated transcripts; never imports the runtime or runner."""
import copy
import json
import unittest
from oracle import audit


def returned(row):
    return {'kind': 'return', 'value': {'isError': False,
        'content': [{'type': 'text', 'text': json.dumps(row)}]}}


def fixture(recovered=False):
    closed = {'status': 'closed', 'authority_granted': False, 'restart_allowed': False,
              'release_attempted': False, 'connection_close_attempted': False,
              'session': {'state': 'closed'}}
    busy = {'kind': 'return', 'value': {'isError': True, 'content': [
        {'type': 'text', 'text': json.dumps({'status': 'busy', 'operation_invoked': False})}]}}
    def inv(n):
        return {} if not n else {p: {'bytes': 2, 'sha256': 'a' * 64}
             for p in ('session-x-close.json', 'x/request.json', 'x/report.json')}
    def ledger(n):
        return returned({'status': 'call_list', 'scope': 'current_server', 'total_calls': n,
            'calls': [] if n == 0 else [{'call_id': 'x', 'operation': 'close', 'state': 'finished'}],
            'next_before_call_id': None, 'operation_invoked': False})
    vals = [returned(closed), {'kind': 'exception', 'type': 'ToolError',
        'message': 'cannot schedule new futures after shutdown'}, returned(closed) if recovered else busy,
        returned(closed)]
    counts = [1, 0, int(recovered), 1]
    labels = ['healthy_close', 'rejected_close', 'recovered_close', 'fresh_close']
    rows = []
    for label, value, n in zip(labels, vals, counts):
        rows.append({'label': label, 'tool': 'interface_close', 'arguments': {}, 'result': value,
                     'invoke_entries': n, 'inventory': inv(n), 'ledger': ledger(n)})
    profile = [{'label': label, 'function': 'invoke', 'operation': 'close'}
               for label, n in zip(labels, counts) for _ in range(n)]
    return {'schema': 'mcp-preworker-original-v1', 'synthetic': True, 'rows': rows, 'profile_events': profile,
            'health_probe': {'value': 'healthy-executor', 'completed': True},
            'tripwire_calls': [], 'source_unchanged': True, 'public_close_calls': 4,
            'public_list_calls': 4, 'executor_probe_calls': 1}


class OracleTests(unittest.TestCase):
    def test_named_controls_on_both_valid_dispositions(self):
        from controls import controls
        for recovered in (False, True):
            result = controls(fixture(recovered))
            self.assertEqual(len(result['records']), 12)
            self.assertTrue(result['passed'])

    def test_accepts_honest_failure(self):
        r = audit(fixture())
        self.assertEqual(r['errors'], [])
        self.assertEqual(r['disposition'], 'FAIL_PREWORKER_CAPACITY_RELEASE')

    def test_accepts_coherent_recovery(self):
        r = audit(fixture(True))
        self.assertEqual(r['errors'], [])
        self.assertEqual(r['disposition'], 'PASS_PREWORKER_CAPACITY_RELEASE_SCOPED')

    def test_corruption_controls(self):
        edits = [
            lambda x: x['rows'].pop(),
            lambda x: x['rows'][1].update(invoke_entries=1),
            lambda x: x['rows'][1].update(inventory={'unexpected': {'bytes': 1, 'sha256': 'a'*64}}),
            lambda x: x['health_probe'].update(completed=False),
            lambda x: x['tripwire_calls'].append('native'),
            lambda x: x.update(source_unchanged=False),
            lambda x: x.update(public_close_calls=5),
            lambda x: x['rows'][2]['result']['value']['content'][0].update(text=json.dumps({'status':'closed'})),
            lambda x: x['rows'][0]['result']['value']['content'][0].update(text=json.dumps({'status':'closed','authority_granted':1})),
            lambda x: x['rows'][1]['result'].update(message='unrelated error'),
            lambda x: x.pop('profile_events'),
            lambda x: x['profile_events'][0].update(operation='dispatch'),
        ]
        for edit in edits:
            x = fixture(); edit(x)
            with self.subTest(value=x):
                self.assertNotEqual(audit(x)['errors'], [])


if __name__ == '__main__':
    unittest.main()
