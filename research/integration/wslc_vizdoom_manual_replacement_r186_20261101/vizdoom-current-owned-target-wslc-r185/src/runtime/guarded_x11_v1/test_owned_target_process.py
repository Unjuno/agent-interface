"""Tests for explicitly owned X11 target-process retirement."""
import signal
import subprocess
import sys
import threading
import time
import unittest
from unittest.mock import Mock, patch

from runtime.guarded_x11_v1.owned_target_process import (
    OwnedTargetProcess, _identity_digest)


class _FakeProcess:
    pid = 4242
    returncode = None

    def __init__(self):
        self.kill = Mock()
        self.wait = Mock(side_effect=self._wait)

    def poll(self):
        return self.returncode

    def _wait(self, timeout=None):
        return self.returncode


@unittest.skipUnless(sys.platform.startswith('linux'), 'Linux pidfd contract')
class OwnedTargetProcessTests(unittest.TestCase):
    def test_close_error_does_not_retry_ambiguous_descriptor(self):
        owner = self.launch()
        self.process.returncode = 0
        self.close_fd_mock.side_effect = OSError('injected close error')
        with self.assertRaises(OSError):
            owner.close()
        owner.close()
        self.close_fd_mock.assert_called_once_with(73)
        self.send_signal_mock.assert_not_called()

    def test_retirement_deadline_bounds_handle_lock_wait(self):
        owner = self.launch()
        self.assertEqual(owner.bind_x11_target(self.connection_with_identity(), 100)['status'], 'bound')
        held, release = threading.Event(), threading.Event()
        def hold_lock():
            with owner._handle_lock:
                held.set()
                release.wait(2)
        holder = threading.Thread(target=hold_lock)
        holder.start()
        try:
            self.assertTrue(held.wait(1))
            timer = threading.Timer(.5, release.set)
            timer.start()
            try:
                started = time.monotonic()
                result = owner.retire_bound_target(
                    deadline_monotonic_ns=time.monotonic_ns() + 100_000_000)
                elapsed = time.monotonic() - started
            finally:
                timer.cancel()
            self.assertLess(elapsed, .3)
            self.assertEqual(result['status'], 'unknown')
            self.assertEqual(result['reason'], 'target_retirement_lock_unavailable')
            self.send_signal_mock.assert_not_called()
        finally:
            release.set()
            holder.join(timeout=2)
        self.process.returncode = 0
        owner.close()

    def test_expired_retirement_deadline_refuses_before_signal(self):
        owner = self.launch()
        self.assertEqual(owner.bind_x11_target(self.connection_with_identity(), 100)['status'], 'bound')
        with patch('runtime.guarded_x11_v1.owned_target_process.time.monotonic_ns',
                   return_value=200):
            result = owner.retire_bound_target(deadline_monotonic_ns=100)
        self.assertEqual(result['status'], 'unknown')
        self.assertEqual(result['reason'], 'target_retirement_deadline')
        self.send_signal_mock.assert_not_called()
        self.process.returncode = 0
        owner.close()

    def test_short_deadline_reserves_time_for_kill_escalation(self):
        owner = self.launch()
        self.assertEqual(owner.bind_x11_target(self.connection_with_identity(), 100)['status'], 'bound')
        clock = [1_000_000_000]
        def wait(timeout):
            clock[0] += int(timeout * 1_000_000_000)
            if len(self.send_signal_mock.call_args_list) == 2:
                self.process.returncode = -signal.SIGKILL
                return True
            return False
        with patch('runtime.guarded_x11_v1.owned_target_process.time.monotonic_ns',
                   side_effect=lambda: clock[0]), patch.object(owner, '_wait_for_exit', side_effect=wait):
            result = owner.retire_bound_target(deadline_monotonic_ns=1_200_000_000)
        self.assertTrue(result['process_exit_verified'], result)
        self.assertEqual([call.args for call in self.send_signal_mock.call_args_list],
                         [(73, signal.SIGTERM), (73, signal.SIGKILL)])
        owner.close()

    def test_retirement_does_not_escalate_after_deadline(self):
        owner = self.launch()
        self.assertEqual(owner.bind_x11_target(self.connection_with_identity(), 100)['status'], 'bound')
        clock = [100]
        def wait(_timeout):
            clock[0] = 200
            return False
        with patch('runtime.guarded_x11_v1.owned_target_process.time.monotonic_ns',
                   side_effect=lambda: clock[0]), patch.object(owner, '_wait_for_exit', side_effect=wait):
            result = owner.retire_bound_target(deadline_monotonic_ns=150)
        self.assertEqual(result['status'], 'unknown')
        self.assertEqual(result['reason'], 'target_retirement_deadline')
        self.assertEqual([call.args for call in self.send_signal_mock.call_args_list],
                         [(73, signal.SIGTERM)])
        self.process.returncode = 0
        owner.close()

    def test_direct_retire_rejects_intervening_custody_after_bind(self):
        owner = self.launch()
        entered, release = threading.Event(), threading.Event()
        result = []
        original = owner.bind_x11_target
        def paused_bind(*args, **kwargs):
            binding = original(*args, **kwargs)
            entered.set()
            if not release.wait(2):
                raise RuntimeError('test did not release bind')
            return binding
        with patch('runtime.guarded_x11_v1.owned_target_process.read_linux_x11_process_identity',
                   return_value=_identity_digest(100, self.process.pid, 991)), \
             patch.object(owner, 'bind_x11_target', side_effect=paused_bind):
            thread = threading.Thread(target=lambda: result.append(
                owner.retire_x11_target(object(), 100)))
            thread.start()
            try:
                self.assertTrue(entered.wait(1))
                token = owner.claim_session()
                owner.release_session(token)
                self.assertEqual(original(object(), 100)['status'], 'bound')
            finally:
                release.set()
                thread.join(timeout=2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(result[0]['reason'], 'custody_generation_changed')
        self.send_signal_mock.assert_not_called()
        self.process.returncode = 0
        owner.close()

    def test_unclaimed_binding_rejects_intervening_claim_release_aba(self):
        owner = self.launch()
        entered, release = threading.Event(), threading.Event()
        result = []
        def query(*args):
            entered.set()
            if not release.wait(2):
                raise RuntimeError('test did not release query')
            return _identity_digest(100, self.process.pid, 991)
        with patch('runtime.guarded_x11_v1.owned_target_process.read_linux_x11_process_identity',
                   side_effect=query):
            thread = threading.Thread(target=lambda: result.append(
                owner.bind_x11_target(object(), 100)))
            thread.start()
            try:
                self.assertTrue(entered.wait(1))
                token = owner.claim_session()
                owner.release_session(token)
            finally:
                release.set()
                thread.join(timeout=2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(result[0]['status'], 'refused')
        self.assertEqual(result[0]['reason'], 'custody_generation_changed')
        self.process.returncode = 0
        owner.close()

    def test_exclusive_custody_revokes_old_token_and_requires_new_binding(self):
        owner = self.launch()
        first = owner.claim_session()
        with self.assertRaisesRegex(RuntimeError, 'already claimed'):
            owner.claim_session()
        with patch('runtime.guarded_x11_v1.owned_target_process.read_linux_x11_process_identity',
                   return_value=_identity_digest(100, self.process.pid, 991)):
            self.assertEqual(owner.bind_x11_target(object(), 100, _custody=first)['status'], 'bound')
        with self.assertRaises(PermissionError):
            owner.retire_bound_target()
        self.send_signal_mock.assert_not_called()
        owner.release_session(first)
        second = owner.claim_session()
        with self.assertRaises(PermissionError):
            owner.retire_bound_target(_custody=first)
        with self.assertRaises(PermissionError):
            owner._bind_supervised_observation(100, {
                'status':'observed', 'worker_retired':True, 'worker_exitcode':0,
                'identity_digest':_identity_digest(100, self.process.pid, 991)},
                _custody=first)
        self.assertEqual(owner.retire_bound_target(_custody=second)['reason'],
                         'target_binding_unavailable')
        self.send_signal_mock.assert_not_called()
        owner.release_session(second)
        self.process.returncode = 0
        owner.close()

    def test_concurrent_claim_has_exactly_one_winner(self):
        owner = self.launch()
        barrier = threading.Barrier(3)
        tokens, errors = [], []
        def claim():
            barrier.wait()
            try:
                tokens.append(owner.claim_session())
            except RuntimeError as error:
                errors.append(str(error))
        threads = [threading.Thread(target=claim) for _ in range(2)]
        for thread in threads: thread.start()
        barrier.wait()
        for thread in threads: thread.join(timeout=2)
        self.assertEqual(len(tokens), 1)
        self.assertEqual(len(errors), 1)
        owner.release_session(tokens[0])
        self.process.returncode = 0
        owner.close()

    def test_stalled_identity_query_does_not_block_close_or_bind_after_close(self):
        owner = self.launch()
        entered, release, close_done = threading.Event(), threading.Event(), threading.Event()
        result = []
        def query(*args):
            entered.set()
            if not release.wait(2):
                raise RuntimeError('test did not release identity query')
            return _identity_digest(100, self.process.pid, 991)
        def bind():
            result.append(owner.bind_x11_target(object(), 100))
        def close():
            owner.close()
            close_done.set()
        with patch('runtime.guarded_x11_v1.owned_target_process.read_linux_x11_process_identity',
                   side_effect=query):
            binding = threading.Thread(target=bind)
            closing = threading.Thread(target=close)
            binding.start()
            try:
                self.assertTrue(entered.wait(1))
                self.process.returncode = 0
                closing.start()
                self.assertTrue(close_done.wait(.2), 'close blocked on identity query')
            finally:
                release.set()
                binding.join(timeout=2)
                if closing.ident is not None:
                    closing.join(timeout=2)
        self.assertFalse(binding.is_alive())
        self.assertFalse(closing.is_alive())
        self.assertNotEqual(result[0]['status'], 'bound')

    def test_close_cannot_release_pidfd_during_inflight_signal(self):
        owner = self.launch()
        with patch('runtime.guarded_x11_v1.owned_target_process.read_linux_x11_process_identity',
                   return_value=_identity_digest(100, self.process.pid, 991)):
            self.assertEqual(owner.bind_x11_target(object(), 100)['status'], 'bound')
        signal_entered = threading.Event()
        signal_continue = threading.Event()
        close_done = threading.Event()
        outcomes = []
        def delayed_signal(fd, sig):
            signal_entered.set()
            if not signal_continue.wait(2):
                raise RuntimeError('test failed to release signal')
            outcomes.append(('signal_after_close', self.close_fd_mock.called))
        self.send_signal_mock.side_effect = delayed_signal
        def retire():
            outcomes.append(('retire', owner.retire_bound_target()))
        def close():
            try:
                owner.close()
            finally:
                close_done.set()
        retiring = threading.Thread(target=retire)
        closing = threading.Thread(target=close)
        retiring.start()
        try:
            self.assertTrue(signal_entered.wait(1))
            self.process.returncode = 0
            closing.start()
            self.assertFalse(close_done.wait(.1), 'pidfd closed while signal was in flight')
        finally:
            signal_continue.set()
            retiring.join(timeout=2)
            if closing.ident is not None:
                closing.join(timeout=2)
        self.assertFalse(retiring.is_alive())
        self.assertFalse(closing.is_alive())
        self.assertIn(('signal_after_close', False), outcomes)
        self.close_fd_mock.assert_called_once_with(73)

    def setUp(self):
        self.process = _FakeProcess()
        self.popen = patch(
            'runtime.guarded_x11_v1.owned_target_process.subprocess.Popen',
            return_value=self.process)
        self.popen_mock = self.popen.start()
        self.addCleanup(self.popen.stop)
        self.pidfd_open = patch(
            'runtime.guarded_x11_v1.owned_target_process.os.pidfd_open',
            return_value=73)
        self.pidfd_open.start()
        self.addCleanup(self.pidfd_open.stop)
        self.start_ticks = patch(
            'runtime.guarded_x11_v1.owned_target_process._linux_process_start_ticks',
            return_value=991)
        self.start_ticks.start()
        self.addCleanup(self.start_ticks.stop)
        self.send_signal = patch(
            'runtime.guarded_x11_v1.owned_target_process.signal.pidfd_send_signal')
        self.send_signal_mock = self.send_signal.start()
        self.addCleanup(self.send_signal.stop)
        self.close_fd = patch(
            'runtime.guarded_x11_v1.owned_target_process.os.close')
        self.close_fd_mock = self.close_fd.start()
        self.addCleanup(self.close_fd.stop)

    def launch(self):
        return OwnedTargetProcess.launch(
            ['/opt/disposable-target'], disposable=True)

    def connection_with_identity(self, xid=100):
        connection = object()
        identity = _identity_digest(xid, self.process.pid, 991)
        patcher = patch(
            'runtime.guarded_x11_v1.owned_target_process.read_linux_x11_process_identity',
            return_value=identity)
        patcher.start()
        self.addCleanup(patcher.stop)
        return connection

    def test_requires_explicit_disposable_target_before_launch(self):
        with self.assertRaises(PermissionError):
            OwnedTargetProcess.launch(['/opt/target'], disposable=False)

    def test_supervised_binding_refuses_unknown_and_mismatched_identity(self):
        owner = self.launch()
        with patch('runtime.guarded_x11_v1.owned_target_process.supervise_xres_worker',
                   return_value={'status':'unknown','reason':'supervision_timeout'}):
            result = owner.bind_x11_target_supervised(':91', 100, timeout_s=0.2)
        self.assertEqual(result['reason'], 'target_identity_unavailable')
        with patch('runtime.guarded_x11_v1.owned_target_process.supervise_xres_worker',
                   return_value={'status':'observed','identity_digest':'wrong',
                                 'worker_retired':True,'worker_exitcode':0}):
            result = owner.bind_x11_target_supervised(':91', 100, timeout_s=0.2)
        self.assertEqual(result['reason'], 'target_process_identity_mismatch')
        self.assertEqual(owner.retire_bound_target()['reason'], 'target_binding_unavailable')
        self.send_signal_mock.assert_not_called()
        self.process.returncode = 0
        owner.close()

    def test_prestarted_binding_requires_clean_worker_and_matching_identity(self):
        owner = self.launch()
        digest = _identity_digest(100, self.process.pid, 991)
        supervisor = Mock()
        supervisor.run.return_value = {'status':'observed','identity_digest':digest,
                                       'worker_retired':False,'worker_exitcode':None}
        refused = owner.bind_x11_target_prestarted(supervisor, 'session', ':91', 100)
        self.assertEqual(refused['reason'], 'target_identity_unavailable')
        self.assertEqual(owner.retire_bound_target()['reason'], 'target_binding_unavailable')
        supervisor.run.return_value.update(worker_retired=True, worker_exitcode=0)
        binding = owner.bind_x11_target_prestarted(supervisor, 'session', ':91', 100)
        self.assertEqual(binding['status'], 'bound')
        request = supervisor.run.call_args.args[0]
        self.assertEqual(request['session_id'], 'session')
        self.assertEqual(request['xid'], 100)
        self.process.returncode = 0
        owner.close()

    def test_rejects_shell_string_and_malformed_argv(self):
        for argv in ('/opt/target', [], ['ok', '\0bad']):
            with self.subTest(argv=argv), self.assertRaises(ValueError):
                OwnedTargetProcess.launch(argv, disposable=True)
        self.popen_mock.assert_not_called()

    def test_identity_mismatch_refuses_without_signaling_any_process(self):
        owner = self.launch()
        patcher = patch(
            'runtime.guarded_x11_v1.owned_target_process.read_linux_x11_process_identity',
            return_value=_identity_digest(100, self.process.pid, 992))
        patcher.start()
        self.addCleanup(patcher.stop)

        result = owner.retire_x11_target(object(), 100)

        self.assertEqual(result['status'], 'refused')
        self.assertEqual(result['reason'], 'target_process_identity_mismatch')
        self.assertEqual(result['signal_attempts'], [])
        self.send_signal_mock.assert_not_called()
        self.process.kill.assert_not_called()
        self.process.returncode = 0
        owner.close()

    def test_matching_target_uses_retained_pidfd_and_confirms_term_exit(self):
        owner = self.launch()
        connection = self.connection_with_identity()

        def wait(timeout):
            self.process.returncode = 0
            return True

        with patch.object(owner, '_wait_for_exit', side_effect=wait) as wait_exit:
            result = owner.retire_x11_target(connection, 100)

        self.assertEqual(result['status'], 'retired')
        self.assertTrue(result['target_identity_verified'])
        self.assertTrue(result['process_exit_verified'])
        self.assertEqual(result['signal_attempts'], [
            {'signal':signal.SIGTERM, 'status':'sent'}])
        self.send_signal_mock.assert_called_once_with(73, signal.SIGTERM)
        wait_exit.assert_called_once_with(0.25)
        owner.close()

    def test_timeout_escalates_only_through_same_pidfd(self):
        owner = self.launch()
        connection = self.connection_with_identity()
        outcomes = iter((False, True))

        def wait(timeout):
            if next(outcomes):
                self.process.returncode = -signal.SIGKILL
                return True
            return False

        with patch.object(owner, '_wait_for_exit', side_effect=wait):
            result = owner.retire_x11_target(
                connection, 100, term_timeout_s=0.1, kill_timeout_s=0.2)

        self.assertEqual(result['status'], 'retired')
        self.assertEqual([row['signal'] for row in result['signal_attempts']],
                         [signal.SIGTERM, signal.SIGKILL])
        self.assertEqual([call.args for call in self.send_signal_mock.call_args_list],
                         [(73, signal.SIGTERM), (73, signal.SIGKILL)])
        owner.close()

    def test_invalid_wait_bound_is_rejected_before_signaling(self):
        owner = self.launch()
        with self.assertRaises(ValueError):
            owner.retire_x11_target(
                self.connection_with_identity(), 100, term_timeout_s=float('inf'))
        self.send_signal_mock.assert_not_called()
        self.process.returncode = 0
        owner.close()

    def test_pidfd_open_failure_cleans_only_the_spawned_popen_child(self):
        self.pidfd_open.stop()
        with patch(
                'runtime.guarded_x11_v1.owned_target_process.os.pidfd_open',
                side_effect=OSError('unavailable')):
            with self.assertRaises(OSError):
                OwnedTargetProcess.launch(
                    ['/opt/disposable-target'], disposable=True)
        self.process.kill.assert_called_once_with()
        self.process.wait.assert_called_once_with(timeout=1.0)
        self.send_signal_mock.assert_not_called()

    def test_close_is_idempotent_and_closed_handle_cannot_retire(self):
        owner = self.launch()
        self.process.returncode = 0
        owner.close()
        owner.close()

        result = owner.retire_x11_target(self.connection_with_identity(), 100)

        self.assertEqual(result['status'], 'refused')
        self.assertEqual(result['reason'], 'ownership_handle_closed')
        self.send_signal_mock.assert_not_called()
        self.close_fd_mock.assert_called_once_with(73)

    def test_prebound_target_can_be_retired_without_reconnecting_to_x_server(self):
        owner = self.launch()
        identity = _identity_digest(100, self.process.pid, 991)
        with patch(
                'runtime.guarded_x11_v1.owned_target_process.read_linux_x11_process_identity',
                return_value=identity) as read_identity:
            binding = owner.bind_x11_target(object(), 100)
            read_identity.reset_mock()

            def wait(timeout):
                self.process.returncode = 0
                return True

            with patch.object(owner, '_wait_for_exit', side_effect=wait):
                result = owner.retire_bound_target()

            read_identity.assert_not_called()
        self.assertEqual(binding['status'], 'bound')
        self.assertEqual(result['status'], 'retired')
        self.assertEqual(result['target_xid'], 100)
        self.process.returncode = 0
        owner.close()

    def test_cannot_drop_the_only_identity_handle_while_target_is_running(self):
        owner = self.launch()
        with self.assertRaisesRegex(RuntimeError, 'target is running'):
            owner.close()
        self.close_fd_mock.assert_not_called()
        self.process.returncode = 0
        owner.close()


@unittest.skipUnless(sys.platform.startswith('linux'), 'Linux pidfd contract')
class OwnedTargetProcessLinuxIntegrationTests(unittest.TestCase):
    def test_matching_identity_retires_the_actual_launched_child(self):
        owner = OwnedTargetProcess.launch(
            [sys.executable, '-c', 'import time; time.sleep(30)'],
            disposable=True)
        try:
            self.assertTrue(owner.running)
            identity = _identity_digest(100, owner.pid, owner.start_ticks)
            with patch(
                    'runtime.guarded_x11_v1.owned_target_process.read_linux_x11_process_identity',
                    return_value=identity):
                result = owner.retire_x11_target(object(), 100)
            self.assertEqual(result['status'], 'retired')
            self.assertEqual(result['exitcode'], -signal.SIGTERM)
            self.assertTrue(result['target_identity_verified'])
            self.assertTrue(result['process_exit_verified'])
            self.assertFalse(owner.running)
        finally:
            if owner.running:
                signal.pidfd_send_signal(owner._pidfd, signal.SIGKILL)
                owner._process.wait(timeout=1.0)
            owner.close()


if __name__ == '__main__':
    unittest.main()
