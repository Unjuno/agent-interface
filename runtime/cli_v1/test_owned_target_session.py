import signal
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
from runtime.cli_v1.owned_target_session import OwnedTargetGuardedSessionOwner
from runtime.guarded_x11_v1.owned_target_process import OwnedTargetProcess, _identity_digest


class OwnedTargetSessionTests(unittest.TestCase):
    def test_transient_pidfd_error_gets_one_immediate_same_handle_retry(self):
        owner = object.__new__(OwnedTargetGuardedSessionOwner)
        owner._owned_target_process = Mock()
        failed = {'status':'unknown', 'reason':'pidfd_signal_failed',
                  'target_identity_verified':True, 'process_exit_verified':False}
        owner._owned_target_process.retire_bound_target.side_effect = [
            failed, {'status':'retired', 'process_exit_verified':True}]
        owner._attempt_target_retirement()
        self.assertEqual(owner._owned_target_process.retire_bound_target.call_count, 2)
        self.assertTrue(owner._owned_target_retirement['process_exit_verified'])
        self.assertEqual(owner._owned_target_retirement['immediate_previous_attempt'], failed)
        owner._owned_target_process.close.assert_called_once_with()

    def test_repeated_pidfd_error_is_bounded_and_remains_unknown(self):
        owner = object.__new__(OwnedTargetGuardedSessionOwner)
        owner._owned_target_process = Mock()
        failed = {'status':'unknown', 'reason':'pidfd_signal_failed',
                  'target_identity_verified':True, 'process_exit_verified':False}
        owner._owned_target_process.retire_bound_target.return_value = failed
        owner._attempt_target_retirement()
        self.assertEqual(owner._owned_target_process.retire_bound_target.call_count, 2)
        self.assertEqual(owner._owned_target_retirement['status'], 'unknown')
        owner._owned_target_process.close.assert_not_called()

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Linux pidfd contract')
    def test_close_retries_exact_live_child_after_pidfd_signal_error(self):
        target = OwnedTargetProcess.launch(
            [sys.executable, '-c', 'import time; time.sleep(30)'], disposable=True)
        witness = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
        try:
            digest = _identity_digest(77, target.pid, target.start_ticks)
            with patch('runtime.guarded_x11_v1.owned_target_process.read_linux_x11_process_identity',
                       return_value=digest):
                self.assertEqual(target.bind_x11_target(object(), 77)['status'], 'bound')
            owner = object.__new__(OwnedTargetGuardedSessionOwner)
            owner._owned_target_process = target
            owner._owned_target_binding = {'status':'bound'}
            owner._owned_target_retirement = None
            owner._retirement = {'retired':True}
            owner._target_identity_supervisor = None
            with patch('runtime.guarded_x11_v1.owned_target_process.signal.pidfd_send_signal',
                       side_effect=PermissionError('injected')):
                owner._attempt_target_retirement()
            self.assertEqual(owner._owned_target_retirement['reason'], 'pidfd_signal_failed')
            self.assertTrue(target.running)
            with patch.object(OwnedGuardedSessionOwner, 'close', return_value={
                    'status':'cleanup_failed', 'cleanup_status':'UNKNOWN',
                    'replay_allowed':False}):
                report = owner.close()
            self.assertEqual(report['owned_target_retirement']['status'], 'retired')
            self.assertTrue(report['owned_target_retirement']['process_exit_verified'])
            self.assertEqual(report['owned_target_retirement']['previous_attempt']['reason'],
                             'pidfd_signal_failed')
            self.assertFalse(target.running)
            self.assertIsNone(witness.poll())
            self.assertEqual(report['cleanup_status'], 'UNKNOWN')
            self.assertFalse(report['replay_allowed'])
        finally:
            if target.running:
                signal.pidfd_send_signal(target._pidfd, signal.SIGKILL)
                target._process.wait(timeout=1)
            target.close()
            if witness.poll() is None:
                witness.terminate()
            witness.wait(timeout=1)

    def test_close_rechecks_unconfirmed_target_exit_after_verified_release(self):
        owner = object.__new__(OwnedTargetGuardedSessionOwner)
        owner._owned_target_binding = {'status':'bound'}
        owner._owned_target_retirement = {'status':'unknown',
                                          'process_exit_verified':False}
        owner._owned_target_process = Mock()
        owner._owned_target_process.retire_bound_target.return_value = {
            'status':'already_exited', 'process_exit_verified':True}
        owner._retirement = {'retired':True}
        owner._target_identity_supervisor = None
        with patch.object(OwnedGuardedSessionOwner, 'close', return_value={
                'status':'cleanup_failed', 'cleanup_status':'UNKNOWN',
                'owner_release_attempt':{'status':'readback_verified'},
                'replay_allowed':False}):
            result = owner.close()
        owner._owned_target_process.retire_bound_target.assert_called_once_with()
        self.assertTrue(result['owned_target_retirement']['process_exit_verified'])
        self.assertEqual(result['cleanup_status'], 'UNKNOWN')
        self.assertFalse(result['replay_allowed'])
        self.assertEqual(result['owned_target_retirement']['previous_attempt']['status'], 'unknown')

    def test_close_does_not_recheck_target_without_retired_owner(self):
        owner = object.__new__(OwnedTargetGuardedSessionOwner)
        owner._owned_target_binding = {'status':'bound'}
        owner._owned_target_retirement = {'status':'unknown',
                                          'process_exit_verified':False}
        owner._owned_target_process = Mock()
        owner._retirement = {'retired':False}
        owner._target_identity_supervisor = None
        with patch.object(OwnedGuardedSessionOwner, 'close', return_value={
                'status':'cleanup_failed', 'cleanup_status':'UNKNOWN'}):
            result = owner.close()
        owner._owned_target_process.retire_bound_target.assert_not_called()
        self.assertEqual(result['owned_target_retirement']['status'], 'unknown')

    def test_failed_identity_binding_refuses_before_owner_rpc_dispatch(self):
        owner = object.__new__(OwnedTargetGuardedSessionOwner)
        owner._owned_target_binding = None
        owner._target_identity_supervisor = None
        owner._owned_target_xid = 77
        owner.display_name = ':99'
        owner._rpc = Mock()
        owner._owned_target_process = Mock()
        owner._owned_target_process.bind_x11_target_supervised.return_value = {
            'status':'refused', 'reason':'target_process_identity_mismatch'}
        with patch.object(OwnedGuardedSessionOwner, '_ensure_started'):
            with self.assertRaisesRegex(RuntimeError, 'target_process_identity_mismatch'):
                owner._request_locked('guarded_input', {'alias':'field'})
        owner._rpc.send.assert_not_called()
        owner._owned_target_process.retire_bound_target.assert_not_called()

    def test_prestarted_identity_accepts_child_session_after_startup(self):
        target = Mock(spec=__import__('runtime.guarded_x11_v1.owned_target_process',
                                      fromlist=['OwnedTargetProcess']).OwnedTargetProcess)
        target.running = True
        def parent_init(owner, *args, **kwargs):
            owner.session_id = 'parent-session'
            owner.display_name = ':99'
        def start(owner):
            owner.session_id = 'child-session'
        def bind(supervisor, session_id, display, xid):
            self.assertIn(supervisor._expected_session_id, (None, session_id))
            return {'status':'bound'}
        target.bind_x11_target_prestarted.side_effect = bind
        with patch.object(OwnedGuardedSessionOwner, '__init__', parent_init), \
             patch.object(OwnedGuardedSessionOwner, '_ensure_started', start), \
             patch('runtime.cli_v1.owned_target_session.PrestartedCancellationSupervisor') as factory:
            factory.side_effect = lambda worker, expected_session_id=None: Mock(
                _expected_session_id=expected_session_id)
            owner = OwnedTargetGuardedSessionOwner(
                {'app':77}, '/tmp', owned_target_process=target,
                prestarted_target_identity=True)
            owner._ensure_started()
        self.assertEqual(owner._owned_target_binding['status'], 'bound')

    def test_retire_target_precedes_existing_release_cleanup_and_is_cached(self):
        owner = object.__new__(OwnedTargetGuardedSessionOwner)
        target = Mock()
        target.retire_bound_target.return_value = {
            'status':'retired', 'target_identity_verified':True,
            'process_exit_verified':True}
        owner._owned_target_process = target
        owner._owned_target_retirement = None
        order = []

        def base_cleanup(_self, retirement, **kwargs):
            order.append(('base_cleanup', retirement, kwargs))
            return {'status':'disconnected'}, {'status':'readback_verified'}

        retire = target.retire_bound_target
        retire.side_effect = lambda: (order.append(('target_retire',)) or {
            'status':'retired', 'target_identity_verified':True,
            'process_exit_verified':True})
        with patch.object(OwnedGuardedSessionOwner,
                          '_cleanup_after_owner_retirement', base_cleanup):
            first = owner._cleanup_after_owner_retirement(
                {'retired':True}, retry_after_resume=True)
            second = owner._cleanup_after_owner_retirement(
                {'retired':True}, retry_after_resume=True)

        self.assertEqual(order[0], ('target_retire',))
        self.assertEqual(order[1][0], 'base_cleanup')
        self.assertEqual(order[2][0], 'base_cleanup')
        self.assertEqual(first, ({'status':'disconnected'},
                                 {'status':'readback_verified'}))
        self.assertEqual(second, first)
        target.close.assert_called_once_with()
        self.assertEqual(owner._owned_target_retirement['status'], 'retired')

    def test_failed_control_owner_retirement_does_not_signal_target(self):
        owner = object.__new__(OwnedTargetGuardedSessionOwner)
        target = Mock()
        owner._owned_target_process = target
        owner._owned_target_retirement = None
        with patch.object(OwnedGuardedSessionOwner,
                          '_cleanup_after_owner_retirement',
                          return_value=({'status':'unknown'},
                                        {'status':'not_attempted'})):
            owner._cleanup_after_owner_retirement({'retired':False})
        target.retire_bound_target.assert_not_called()
        self.assertIsNone(owner._owned_target_retirement)
        target.retire_bound_target.return_value = {'status':'retired',
                                                  'process_exit_verified':True}
        with patch.object(OwnedGuardedSessionOwner, '_cleanup_after_owner_retirement',
                          return_value=({}, {})):
            owner._cleanup_after_owner_retirement({'retired':True})
        target.retire_bound_target.assert_called_once_with()

    def test_target_retirement_exception_does_not_skip_release_cleanup(self):
        owner = object.__new__(OwnedTargetGuardedSessionOwner)
        owner._owned_target_process = Mock()
        owner._owned_target_process.retire_bound_target.side_effect = OSError('failed')
        owner._owned_target_retirement = None
        with patch.object(OwnedGuardedSessionOwner, '_cleanup_after_owner_retirement',
                          return_value=({'status':'disconnected'},
                                        {'status':'readback_verified'})) as cleanup:
            owner._cleanup_after_owner_retirement({'retired':True})
        cleanup.assert_called_once()
        self.assertEqual(owner._owned_target_retirement['status'], 'unknown')
        self.assertFalse(owner._owned_target_retirement['process_exit_verified'])

    def test_cancel_preserves_unknown_and_attaches_target_receipt(self):
        owner = object.__new__(OwnedTargetGuardedSessionOwner)
        owner._owned_target_binding = {'status':'bound', 'xid':77}
        owner._owned_target_retirement = {'status':'retired',
                                          'process_exit_verified':True}
        with patch.object(OwnedGuardedSessionOwner, 'cancel_guarded',
                          return_value={'status':'cancel_unconfirmed',
                              'cleanup_status':'UNKNOWN', 'release_confirmed':False,
                              'task_success':None, 'replay_allowed':False}):
            result = owner.cancel_guarded('call-1')
        self.assertEqual(result['owned_target_binding']['xid'], 77)
        self.assertEqual(result['owned_target_retirement']['status'], 'retired')
        self.assertEqual(result['cleanup_status'], 'UNKNOWN')
        self.assertFalse(result['release_confirmed'])
        self.assertIsNone(result['task_success'])
        self.assertFalse(result['replay_allowed'])

    def test_close_includes_target_receipt_without_upgrading_unknown(self):
        owner = object.__new__(OwnedTargetGuardedSessionOwner)
        owner._owned_target_binding = {'status':'bound', 'xid':77}
        owner._owned_target_retirement = {'status':'unknown',
                                          'process_exit_verified':False}
        with patch.object(OwnedGuardedSessionOwner, 'close',
                          return_value={'status':'cleanup_failed',
                              'cleanup_status':'UNKNOWN', 'task_success':None,
                              'replay_allowed':False}):
            result = owner.close()
        self.assertEqual(result['owned_target_retirement']['status'], 'unknown')
        self.assertFalse(result['owned_target_retirement']['process_exit_verified'])
        self.assertEqual(result['cleanup_status'], 'UNKNOWN')
        self.assertIsNone(result['task_success'])
        self.assertFalse(result['replay_allowed'])


if __name__ == '__main__':
    unittest.main()
