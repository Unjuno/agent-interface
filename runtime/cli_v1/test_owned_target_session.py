import asyncio
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch

from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
from runtime.cli_v1.owned_target_session import OwnedTargetGuardedSessionOwner
from runtime.cli_v1.mcp_server import create_server
from runtime.guarded_x11_v1.owned_target_process import OwnedTargetProcess, _identity_digest


class ExclusiveServerCustodyTests(unittest.IsolatedAsyncioTestCase):
    async def test_two_servers_cannot_share_target_and_clean_close_allows_new_owner(self):
        target = OwnedTargetProcess.launch(
            [sys.executable, '-c', 'import time; time.sleep(30)'], disposable=True)
        first = None
        second = None
        try:
            with tempfile.TemporaryDirectory() as root:
                options = dict(session_mode='guarded-x11', guarded_process_identity=True,
                               guarded_query_worker=True, guarded_owned_process=True,
                               _guarded_owned_target_process=target)
                first = create_server({'app':77}, root + '/first', **options)
                with patch('runtime.cli_v1.mcp_server.ThreadPoolExecutor') as executor:
                    with self.assertRaisesRegex(RuntimeError, 'already claimed'):
                        create_server({'app':77}, root + '/conflict', **options)
                    executor.return_value.shutdown.assert_called_once_with(
                        wait=False, cancel_futures=True)
                before = sum(t.name.startswith('guarded-cancel')
                             for t in threading.enumerate())
                retained_errors = []
                for index in range(3):
                    try:
                        create_server({'app':77}, root + '/conflict-' + str(index), **options)
                    except RuntimeError as error:
                        retained_errors.append(error)
                self.assertEqual(len(retained_errors), 3)
                deadline = time.monotonic() + 2
                while time.monotonic() < deadline:
                    current = sum(t.name.startswith('guarded-cancel')
                                  for t in threading.enumerate())
                    if current <= before:
                        break
                    await asyncio.sleep(.01)
                self.assertLessEqual(current, before)
                await first.call_tool('interface_close', {})
                second = create_server({'app':77}, root + '/second', **options)
                await second.call_tool('interface_close', {})
        finally:
            if first is not None:
                try: await first.call_tool('interface_close', {})
                except Exception: pass
            if second is not None:
                try: await second.call_tool('interface_close', {})
                except Exception: pass
            if target.running:
                signal.pidfd_send_signal(target._pidfd, signal.SIGKILL)
                target._process.wait(timeout=1)
            target.close()


class OwnedTargetSessionTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform.startswith('linux'), 'Linux pidfd contract')
    def test_deadline_retirement_closes_real_owned_handle(self):
        target = OwnedTargetProcess.launch(
            [sys.executable, '-c', 'import time; time.sleep(30)'], disposable=True)
        token = target.claim_session()
        try:
            digest = _identity_digest(77, target.pid, target.start_ticks)
            with patch('runtime.guarded_x11_v1.owned_target_process.read_linux_x11_process_identity',
                       return_value=digest):
                self.assertEqual(target.bind_x11_target(object(), 77, _custody=token)['status'], 'bound')
            owner = object.__new__(OwnedTargetGuardedSessionOwner)
            owner._target_retirement_lock = threading.RLock()
            owner._target_custody = token
            owner._owned_target_process = target
            owner._attempt_target_retirement(deadline_monotonic_ns=time.monotonic_ns()+2_000_000_000)
            self.assertTrue(owner._owned_target_retirement['process_exit_verified'])
            self.assertNotIn('handle_close_error', owner._owned_target_retirement)
            self.assertTrue(target._closed)
        finally:
            if target.running:
                signal.pidfd_send_signal(target._pidfd, signal.SIGKILL)
                target._process.wait(timeout=1)
            target.close(_custody=token)

    def test_concurrent_direct_cancel_cannot_overwrite_active_deadline(self):
        owner = object.__new__(OwnedTargetGuardedSessionOwner)
        owner._target_retirement_lock = threading.RLock()
        owner._target_cancel_guard = threading.Lock()
        owner._target_cancel_context = threading.local()
        owner._owned_target_retirement = None
        owner._owned_target_binding = None
        entered, release = threading.Event(), threading.Event()
        results = []
        def base(*args, **kwargs):
            entered.set()
            release.wait(2)
            return {'status':'cancel_requested', 'cleanup_status':'UNKNOWN',
                    'replay_allowed':False}
        def invoke(token):
            results.append(owner.cancel_guarded(token, deadline_monotonic_ns=10**18))
        with patch.object(OwnedGuardedSessionOwner, 'cancel_guarded', side_effect=base) as mocked:
            first = threading.Thread(target=invoke, args=('first',))
            second = threading.Thread(target=invoke, args=('second',))
            first.start()
            try:
                self.assertTrue(entered.wait(1))
                second.start()
                second.join(timeout=.2)
                self.assertFalse(second.is_alive(), 'second cancellation was not rejected promptly')
                self.assertEqual(mocked.call_count, 1)
            finally:
                release.set()
                first.join(timeout=2)
                if second.ident is not None:
                    second.join(timeout=2)
        self.assertTrue(any(row.get('reason') == 'concurrent_cancel_in_progress'
                            and row.get('replay_allowed') is False for row in results))

    def test_later_close_retries_retirement_skipped_for_lock_contention(self):
        owner = object.__new__(OwnedTargetGuardedSessionOwner)
        owner._target_retirement_lock = threading.RLock()
        owner._target_retirement_deferred = threading.Event()
        owner._target_cancel_context = threading.local()
        owner._active_cancel_deadline_ns = time.monotonic_ns() + 350_000_000
        owner._owned_target_retirement = None
        owner._owned_target_binding = {'status':'bound'}
        owner._owned_target_process = Mock()
        owner._owned_target_process.retire_bound_target.return_value = {
            'status':'retired', 'process_exit_verified':True}
        owner._retirement = {'retired':True}
        owner._target_identity_supervisor = None
        entered = threading.Event()
        def base(*args, **kwargs):
            entered.set()
            return {}, {'status':'readback_verified'}
        def run():
            owner._target_cancel_context.active = True
            owner._target_cancel_context.deadline_ns = owner._active_cancel_deadline_ns
            owner._cleanup_after_owner_retirement({'retired':True})
        with patch.object(OwnedGuardedSessionOwner, '_cleanup_after_owner_retirement', base):
            owner._target_retirement_lock.acquire()
            thread = threading.Thread(target=run)
            thread.start()
            try:
                self.assertTrue(entered.wait(.3))
            finally:
                owner._target_retirement_lock.release()
                thread.join(timeout=2)
        owner._owned_target_process.retire_bound_target.assert_not_called()
        with patch.object(OwnedGuardedSessionOwner, 'close', return_value={
                'status':'cleanup_failed', 'cleanup_status':'UNKNOWN',
                'owner_release_attempt':{'status':'readback_verified'},
                'replay_allowed':False}):
            result = owner.close()
        owner._owned_target_process.retire_bound_target.assert_called_once_with()
        self.assertTrue(result['owned_target_retirement']['process_exit_verified'])
        self.assertEqual(result['cleanup_status'], 'UNKNOWN')

    def test_cancel_lock_contention_does_not_consume_release_reserve(self):
        owner = object.__new__(OwnedTargetGuardedSessionOwner)
        owner._target_retirement_lock = threading.RLock()
        owner._target_cancel_context = threading.local()
        owner._active_cancel_deadline_ns = time.monotonic_ns() + 350_000_000
        owner._owned_target_retirement = None
        owner._owned_target_binding = None
        owner._owned_target_process = Mock()
        base_entered = threading.Event()
        completed = threading.Event()
        receipts = []
        def base(*args, **kwargs):
            base_entered.set()
            return {}, {}
        def run():
            owner._target_cancel_context.active = True
            owner._target_cancel_context.deadline_ns = owner._active_cancel_deadline_ns
            owner._cleanup_after_owner_retirement({'retired':True})
            receipts.append(owner._with_target_receipts({'status':'cancel_requested'}))
            completed.set()
        with patch.object(OwnedGuardedSessionOwner, '_cleanup_after_owner_retirement', base):
            owner._target_retirement_lock.acquire()
            thread = threading.Thread(target=run)
            thread.start()
            try:
                self.assertTrue(base_entered.wait(.3), 'target lock blocked independent release')
                self.assertTrue(completed.wait(.1), 'receipt blocked after release')
            finally:
                owner._target_retirement_lock.release()
                thread.join(timeout=2)
        self.assertFalse(thread.is_alive())
        owner._owned_target_process.retire_bound_target.assert_not_called()
        self.assertEqual(receipts[0]['owned_target_retirement']['status'], 'unknown')

    def test_cancel_target_attempt_reserves_time_for_release(self):
        owner = object.__new__(OwnedTargetGuardedSessionOwner)
        owner._target_retirement_lock = threading.RLock()
        owner._target_cancel_context = threading.local()
        owner._target_cancel_context.active = True
        owner._target_cancel_context.deadline_ns = 2_000_000_000
        owner._active_cancel_deadline_ns = 9_000_000_000
        owner._owned_target_retirement = None
        owner._owned_target_process = Mock()
        owner._owned_target_process.retire_bound_target.return_value = {
            'status':'unknown', 'reason':'target_retirement_deadline',
            'process_exit_verified':False}
        with patch.object(OwnedGuardedSessionOwner, '_cleanup_after_owner_retirement',
                          return_value=({}, {})) as cleanup, \
             patch('runtime.cli_v1.owned_target_session.time.monotonic_ns',
                   return_value=1_000_000_000):
            owner._cleanup_after_owner_retirement({'retired':True})
        owner._owned_target_process.retire_bound_target.assert_called_once_with(
            deadline_monotonic_ns=1_750_000_000)
        cleanup.assert_called_once()

    def test_cancel_context_does_not_apply_to_later_explicit_close(self):
        owner = object.__new__(OwnedTargetGuardedSessionOwner)
        owner._target_retirement_lock = threading.RLock()
        owner._target_cancel_context = threading.local()
        owner._active_cancel_deadline_ns = 2_000_000_000
        owner._owned_target_retirement = None
        owner._owned_target_process = Mock()
        owner._owned_target_process.retire_bound_target.return_value = {
            'status':'unknown', 'reason':'target_retirement_deadline',
            'process_exit_verified':False}
        with patch.object(OwnedGuardedSessionOwner, '_cleanup_after_owner_retirement',
                          return_value=({}, {})):
            owner._cleanup_after_owner_retirement({'retired':True})
        owner._owned_target_process.retire_bound_target.assert_called_once_with()

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Linux pidfd contract')
    def test_closed_old_owner_cannot_retire_new_custodian_target(self):
        target = OwnedTargetProcess.launch(
            [sys.executable, '-c', 'import time; time.sleep(30)'], disposable=True)
        new_token = None
        try:
            with tempfile.TemporaryDirectory() as root:
                owner = OwnedTargetGuardedSessionOwner({'app':77}, root,
                    owned_target_process=target)
                self.assertTrue(owner.close()['verified'])
                digest = _identity_digest(77, target.pid, target.start_ticks)
                with patch('runtime.guarded_x11_v1.owned_target_process.read_linux_x11_process_identity',
                           return_value=digest):
                    self.assertEqual(target.bind_x11_target(object(), 77)['status'], 'bound')
                owner._attempt_target_retirement()
                self.assertEqual(owner._owned_target_retirement['status'], 'unknown')
                self.assertEqual(owner._owned_target_retirement['error_type'], 'PermissionError')
                self.assertTrue(target.running)
                new_token = target.claim_session()
                owner._attempt_target_retirement()
                self.assertEqual(owner._owned_target_retirement['status'], 'unknown')
                self.assertEqual(owner._owned_target_retirement['error_type'], 'PermissionError')
                self.assertTrue(target.running)
        finally:
            if new_token is not None:
                target.release_session(new_token)
            if target.running:
                signal.pidfd_send_signal(target._pidfd, signal.SIGKILL)
                target._process.wait(timeout=1)
            target.close()

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Linux pidfd contract')
    def test_unconfirmed_close_retains_custody(self):
        target = OwnedTargetProcess.launch(
            [sys.executable, '-c', 'import time; time.sleep(30)'], disposable=True)
        owner = None
        try:
            with tempfile.TemporaryDirectory() as root:
                owner = OwnedTargetGuardedSessionOwner({'app':77}, root,
                    owned_target_process=target)
                with patch.object(OwnedGuardedSessionOwner, 'close', return_value={
                        'status':'cleanup_failed', 'cleanup_status':'UNKNOWN',
                        'verified':False}):
                    result = owner.close()
                self.assertEqual(result['cleanup_status'], 'UNKNOWN')
                with self.assertRaisesRegex(RuntimeError, 'already claimed'):
                    target.claim_session()
        finally:
            if owner is not None and owner._target_custody is not None:
                # This test never started a control process or dispatched input.
                target.release_session(owner._target_custody)
                owner._target_custody = None
            if target.running:
                signal.pidfd_send_signal(target._pidfd, signal.SIGKILL)
                target._process.wait(timeout=1)
            target.close()

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Linux pidfd contract')
    def test_failed_prestarted_worker_construction_releases_unstarted_claim(self):
        target = OwnedTargetProcess.launch(
            [sys.executable, '-c', 'import time; time.sleep(30)'], disposable=True)
        try:
            with tempfile.TemporaryDirectory() as root:
                with patch('runtime.cli_v1.owned_target_session.PrestartedCancellationSupervisor',
                           side_effect=RuntimeError('startup failed')):
                    with self.assertRaisesRegex(RuntimeError, 'startup failed'):
                        OwnedTargetGuardedSessionOwner({'app':77}, root,
                            owned_target_process=target, prestarted_target_identity=True)
                token = target.claim_session()
                target.release_session(token)
        finally:
            if target.running:
                signal.pidfd_send_signal(target._pidfd, signal.SIGKILL)
                target._process.wait(timeout=1)
            target.close()

    def test_concurrent_retirement_cleanup_attempts_target_only_once(self):
        owner = object.__new__(OwnedTargetGuardedSessionOwner)
        owner._target_retirement_lock = threading.RLock()
        owner._owned_target_retirement = None
        owner._owned_target_process = Mock()
        entered = threading.Event()
        release = threading.Event()
        second_entered = threading.Event()
        count = []
        def retire():
            count.append(1)
            if len(count) == 1:
                entered.set()
                if not release.wait(2):
                    raise RuntimeError('test did not release retirement')
            else:
                second_entered.set()
            return {'status':'retired', 'process_exit_verified':True}
        owner._owned_target_process.retire_bound_target.side_effect = retire
        def cleanup():
            owner._cleanup_after_owner_retirement({'retired':True})
        with patch.object(OwnedGuardedSessionOwner, '_cleanup_after_owner_retirement',
                          return_value=({}, {})):
            first = threading.Thread(target=cleanup)
            second = threading.Thread(target=cleanup)
            first.start()
            try:
                self.assertTrue(entered.wait(1))
                second.start()
                self.assertFalse(second_entered.wait(.1), 'duplicate target retirement')
            finally:
                release.set()
                first.join(timeout=2)
                if second.ident is not None:
                    second.join(timeout=2)
        self.assertEqual(len(count), 1)
        owner._owned_target_process.close.assert_called_once_with()

    def test_transient_pidfd_error_gets_one_immediate_same_handle_retry(self):
        owner = object.__new__(OwnedTargetGuardedSessionOwner)
        owner._target_retirement_lock = threading.RLock()
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
        owner._target_retirement_lock = threading.RLock()
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
            owner._target_retirement_lock = threading.RLock()
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
        owner._target_retirement_lock = threading.RLock()
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
        owner._target_retirement_lock = threading.RLock()
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
        owner._target_retirement_lock = threading.RLock()
        owner._target_custody = None
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
        def bind(supervisor, session_id, display, xid, **kwargs):
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
        owner._target_retirement_lock = threading.RLock()
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
        owner._target_retirement_lock = threading.RLock()
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
        owner._target_retirement_lock = threading.RLock()
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
        owner._target_retirement_lock = threading.RLock()
        owner._target_cancel_context = threading.local()
        owner._target_cancel_guard = threading.Lock()
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
        owner._target_retirement_lock = threading.RLock()
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
