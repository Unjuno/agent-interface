import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

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


def _blocked_worker_with_start_receipt(request):
    Path(request['started_path']).write_text('started', encoding='utf-8')
    time.sleep(5)
    return {'status':'late', 'operation_id':request['operation_id'],
            'session_id':request['session_id']}


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
        duplicate = self.supervisor.run(
            self.request(operation_id='op-2'),
            deadline_monotonic_ns=time.monotonic_ns() + 1_000_000_000)
        self.assertEqual(duplicate['status'], 'unknown', duplicate)
        self.assertEqual(duplicate['reason'], 'supervisor_unavailable', duplicate)
        self.assertTrue(duplicate['worker_retired'], duplicate)
        self.assertEqual(self.state()['down'], ['a'])
        self.assertEqual(self.state()['accepted'], [])

    def test_close_waits_for_pending_transaction_deadline_and_keeps_one_shot_custody(self):
        started_path = Path(self.temp.name) / 'blocked-worker-started'
        supervisor = PrestartedCancellationSupervisor(
            _blocked_worker_with_start_receipt)
        rows = []
        request = {'operation_id':'close-race-1', 'session_id':'close-race-session',
                   'started_path':str(started_path)}
        deadline = time.monotonic_ns() + 250_000_000
        thread = threading.Thread(target=lambda: rows.append(supervisor.run(
            request, deadline_monotonic_ns=deadline)), daemon=True)
        try:
            thread.start()
            started_by = time.monotonic() + 3
            while not started_path.exists() and time.monotonic() < started_by:
                time.sleep(0.005)
            self.assertTrue(started_path.exists(), 'worker never entered its blocked call')

            close_started = time.monotonic()
            retirement = supervisor.close()
            close_elapsed = time.monotonic() - close_started
            thread.join(1)

            self.assertFalse(thread.is_alive(), 'run did not finish with its transaction')
            self.assertEqual(len(rows), 1, rows)
            self.assertLess(close_elapsed, 2.0, close_elapsed)
            self.assertTrue(retirement['retired'], retirement)
            self.assertEqual(rows[0]['reason'], 'transaction_deadline', rows[0])
            self.assertTrue(rows[0]['worker_retired'], rows[0])
            duplicate = supervisor.run(
                dict(request, operation_id='close-race-2'),
                deadline_monotonic_ns=time.monotonic_ns() + 1_000_000_000)
            self.assertEqual(duplicate['reason'], 'supervisor_unavailable', duplicate)
            self.assertTrue(duplicate['worker_retired'], duplicate)
        finally:
            supervisor.close()

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
                   'owner_process_retired':True, 'owner_process_exitcode':-15,
                   'x_resource_base':123, 'owner_pid':456,
                   'supervisor_pid':os.getpid(),
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

    def _x11_request(self, **updates):
        request = {'operation_id':'op-reuse', 'session_id':'session-reuse',
            'deadline_monotonic_ns':time.monotonic_ns() + 1_000_000_000,
            'owner_process_retired':True, 'owner_process_exitcode':-15,
            'x_resource_base':123, 'owner_pid':456, 'supervisor_pid':os.getpid(),
            'binding_revision':0,
            'owner_generation':{'session_id':'session-reuse', 'child_pid':456,
                'x_resource_base':123, 'binding_revision':0},
            'keys':{'a':38}, 'buttons':[], 'display_name':':88'}
        request.update(updates)
        return request

    def test_x11_worker_releases_once_when_retired_base_is_absent_or_its_own(self):
        from Xlib import X

        cases = ((False, 'owner_pid_absent', None),
                 (os.getpid(), 'resource_base_reused_by_supervisor', os.getpid()))
        for observed_pid, expected_reason, expected_observed_pid in cases:
            with self.subTest(observed_pid=observed_pid):
                xres_display = Mock()
                backend = Mock()
                backend._physical_keys_down.return_value = []
                backend._physical_buttons_down.return_value = []
                with patch('sys.platform', 'linux'), \
                     patch('Xlib.display.Display', return_value=xres_display), \
                     patch('runtime.guarded_x11_v1.xres_client_fence.client_pid_at_base',
                           return_value=observed_pid), \
                     patch('runtime.backends.x11_v1.backend.X11Backend',
                           return_value=backend), \
                     patch('Xlib.ext.xtest.fake_input') as fake_input:
                    result = x11_cancel_worker(self._x11_request())

                self.assertEqual(result['status'], 'completed', result)
                disconnect = result['owner_client_disconnect']
                self.assertEqual(disconnect['status'], 'disconnected', result)
                self.assertEqual(disconnect['reason'], expected_reason, result)
                self.assertEqual(disconnect['observed_pid'], expected_observed_pid, result)
                self.assertEqual(disconnect['observer_pid'], os.getpid(), result)
                self.assertEqual(disconnect['supervisor_pid'], os.getpid(), result)
                self.assertTrue(disconnect['owner_process_retired'], result)
                self.assertEqual(disconnect['owner_process_exitcode'], -15, result)
                self.assertEqual(result['owner_release_attempt']['status'],
                                 'readback_verified', result)
                self.assertFalse(result['release_confirmed'])
                self.assertIsNone(result['task_success'])
                self.assertFalse(result['replay_allowed'])
                fake_input.assert_called_once_with(backend.d, X.KeyRelease, 38)
                backend.d.sync.assert_called_once_with()
                xres_display.close.assert_called_once_with()

    def test_x11_worker_refuses_release_when_retired_base_belongs_to_other_client(self):
        request = self._x11_request()
        xres_display = Mock()
        with patch('sys.platform', 'linux'), \
             patch('Xlib.display.Display', return_value=xres_display), \
             patch('runtime.guarded_x11_v1.xres_client_fence.client_pid_at_base',
                   return_value=999999), \
             patch('runtime.backends.x11_v1.backend.X11Backend') as backend_factory, \
             patch('Xlib.ext.xtest.fake_input') as fake_input:
            result = x11_cancel_worker(request)

        self.assertEqual(result['status'], 'unknown', result)
        self.assertEqual(result['reason'], 'stale_owner_identity', result)
        self.assertEqual(result['owner_client_disconnect']['status'], 'unknown', result)
        self.assertEqual(result['owner_client_disconnect']['reason'],
                         'resource_base_reused_by_unrelated_client', result)
        self.assertEqual(result['owner_client_disconnect']['observed_pid'], 999999)
        self.assertEqual(result['owner_client_disconnect']['observer_pid'], os.getpid())
        self.assertEqual(result['owner_client_disconnect']['supervisor_pid'], os.getpid())
        self.assertEqual(result['owner_release_attempt']['status'], 'not_attempted')
        self.assertFalse(result['release_confirmed'])
        self.assertIsNone(result['task_success'])
        self.assertFalse(result['replay_allowed'])
        backend_factory.assert_not_called()
        fake_input.assert_not_called()

    def test_x11_worker_refuses_a_supervisor_pid_not_bound_to_this_process(self):
        request = self._x11_request(supervisor_pid=os.getpid() + 1)
        with patch('sys.platform', 'linux'), \
             patch('Xlib.display.Display') as display:
            result = x11_cancel_worker(request)

        self.assertEqual(result['status'], 'unknown', result)
        self.assertEqual(result['reason'], 'invalid_cleanup_request', result)
        self.assertEqual(result['invalid_fields'], ['supervisor_pid.current_process'])
        display.assert_not_called()

    def test_x11_worker_refuses_retired_base_without_parent_retirement_receipt(self):
        request = self._x11_request(owner_process_retired=False)
        with patch('sys.platform', 'linux'), \
             patch('Xlib.display.Display') as display:
            result = x11_cancel_worker(request)
        self.assertEqual(result['status'], 'unknown', result)
        self.assertEqual(result['invalid_fields'], ['owner_process_retired'])
        self.assertFalse(result['release_confirmed'])
        display.assert_not_called()

    def test_x11_worker_does_not_release_while_owner_pid_remains_at_base(self):
        request = self._x11_request(deadline_monotonic_ns=10)
        backend = Mock()
        with patch('sys.platform', 'linux'), \
             patch('Xlib.display.Display', return_value=Mock()), \
             patch('runtime.guarded_x11_v1.xres_client_fence.client_pid_at_base',
                   return_value=request['owner_pid']), \
             patch('runtime.guarded_x11_v1.cancel_supervisor.time.monotonic_ns',
                   side_effect=[1, 2, 3, 4, 5, 10]), \
             patch('runtime.guarded_x11_v1.cancel_supervisor.time.sleep'), \
             patch('runtime.backends.x11_v1.backend.X11Backend',
                   return_value=backend) as backend_factory:
            result = x11_cancel_worker(request)

        self.assertEqual(result['status'], 'unknown', result)
        self.assertEqual(result['reason'], 'transaction_deadline_xres', result)
        self.assertEqual(result['owner_client_disconnect']['status'], 'unknown')
        self.assertEqual(result['owner_release_attempt']['status'], 'not_attempted')
        backend_factory.assert_not_called()


if __name__ == '__main__':
    unittest.main()
