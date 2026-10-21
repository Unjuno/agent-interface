import json
import tempfile
import time
import unittest
from pathlib import Path

from runtime.guarded_x11_v1.cancel_supervisor import (
    PrestartedCancellationSupervisor, x11_cancel_worker,
)


def _fake_effect_worker(request):
    time.sleep(request.get('delay_s', 0))
    now_ns = time.monotonic_ns()
    accepted = (now_ns <= request['deadline_monotonic_ns']
                and request.get('owner_generation')
                    == request.get('current_generation'))
    state_path = Path(request['state_path'])
    state = json.loads(state_path.read_text(encoding='utf-8'))
    if accepted:
        state['down'] = []
        state['accepted'].append({'operation_id': request['operation_id'],
                                  'session_id': request['session_id'],
                                  'accepted_ns': now_ns})
    else:
        state['refused'].append({'operation_id': request['operation_id'],
                                 'reason': ('expired' if now_ns > request[
                                     'deadline_monotonic_ns'] else 'stale_generation'),
                                 'observed_ns': now_ns})
    state_path.write_text(json.dumps(state), encoding='utf-8')
    return {'status': 'accepted' if accepted else 'refused',
            'operation_id': request['operation_id'],
            'session_id': request['session_id'],
            'effect_accepted': accepted}


class PrestartedCancellationSupervisorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.state_path = Path(self.temp.name) / 'fake-x.json'
        self.state_path.write_text(json.dumps({'down': ['a'], 'accepted': [],
                                               'refused': []}), encoding='utf-8')
        self.supervisor = PrestartedCancellationSupervisor(_fake_effect_worker)

    def tearDown(self):
        self.supervisor.close()
        self.temp.cleanup()

    def request(self, **updates):
        row = {'operation_id': 'op-1', 'session_id': 'session-1',
               'owner_generation': 'generation-1',
               'current_generation': 'generation-1',
               'state_path': str(self.state_path)}
        row.update(updates)
        return row

    def state(self):
        return json.loads(self.state_path.read_text(encoding='utf-8'))

    def test_ready_supervisor_accepts_one_current_generation_effect(self):
        deadline = time.monotonic_ns() + 2_000_000_000
        result = self.supervisor.run(self.request(), deadline_monotonic_ns=deadline)
        self.assertEqual(result['status'], 'accepted', result)
        self.assertTrue(result.get('worker_retired'), result)
        self.assertEqual(result['operation_id'], 'op-1')
        self.assertEqual(self.state()['down'], [])
        self.assertEqual(len(self.state()['accepted']), 1)

    def test_stale_generation_is_refused_without_fake_effect(self):
        result = self.supervisor.run(
            self.request(current_generation='generation-2'),
            deadline_monotonic_ns=time.monotonic_ns() + 2_000_000_000)
        self.assertEqual(result['status'], 'refused', result)
        self.assertFalse(result['effect_accepted'])
        self.assertEqual(self.state()['down'], ['a'])
        self.assertEqual(self.state()['accepted'], [])
        self.assertEqual(self.state()['refused'][0]['reason'], 'stale_generation')

    def test_blocked_worker_is_terminated_at_absolute_deadline(self):
        result = self.supervisor.run(
            self.request(delay_s=0.5),
            deadline_monotonic_ns=time.monotonic_ns() + 100_000_000)
        self.assertEqual(result['status'], 'unknown', result)
        self.assertEqual(result['reason'], 'transaction_deadline')
        self.assertTrue(result.get('worker_retired'), result)
        self.assertEqual(self.state()['down'], ['a'])
        self.assertEqual(self.state()['accepted'], [])

    def test_expired_before_admission_consumes_supervisor_without_effect(self):
        result = self.supervisor.run(
            self.request(), deadline_monotonic_ns=time.monotonic_ns() - 1)
        self.assertEqual(result['reason'], 'deadline_expired_before_admission')
        self.assertEqual(self.state()['down'], ['a'])
        duplicate = self.supervisor.run(
            self.request(operation_id='op-2'),
            deadline_monotonic_ns=time.monotonic_ns() + 1_000_000_000)
        self.assertEqual(duplicate['reason'], 'supervisor_unavailable')

    def test_x11_worker_rejects_mismatched_generation_before_platform_io(self):
        request = {'operation_id':'op-1', 'session_id':'session-1',
                   'deadline_monotonic_ns':time.monotonic_ns() + 1_000_000_000,
                   'x_resource_base':123, 'owner_pid':456,
                   'binding_revision':'binding-1',
                   'owner_generation':{'session_id':'stale-session',
                       'child_pid':456, 'x_resource_base':123,
                       'binding_revision':'binding-1'},
                   'keys':{'CTRL':37}, 'buttons':[], 'display_name':None}
        result = x11_cancel_worker(request)
        self.assertEqual(result['status'], 'unknown')
        self.assertEqual(result['reason'], 'invalid_cleanup_request')
        self.assertEqual(result['invalid_fields'], ['owner_generation.session_id'])
        self.assertFalse(result['release_confirmed'])
        self.assertIsNone(result['task_success'])
        self.assertFalse(result['replay_allowed'])


if __name__ == '__main__':
    unittest.main()
