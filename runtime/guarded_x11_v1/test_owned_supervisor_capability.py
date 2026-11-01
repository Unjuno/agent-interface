"""Opt-in owned display capability on real cancellation supervisor startup."""
import importlib.util
import multiprocessing
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from runtime.guarded_x11_v1.cancel_supervisor import (
    PrestartedCancellationSupervisor, x11_cancel_worker,
)


def _hold_readiness(ready, delay):
    try:
        time.sleep(delay)
    finally:
        ready.close()


def _owner_client(display_name, authority, ready, stop):
    from Xlib import display
    os.environ['XAUTHORITY'] = authority
    connection = display.Display(display_name)
    try:
        ready.send({'pid':os.getpid(),
                    'resource_base':connection.display.info.resource_id_base})
        stop.recv()
    finally:
        connection.close()
        ready.close()
        stop.close()


def _key_down(connection, code):
    bits = connection.query_keymap()
    return bool(bits[code // 8] & (1 << (code % 8)))

@unittest.skipUnless(
    sys.platform.startswith('linux') and hasattr(os, 'pidfd_open')
    and shutil.which('Xvfb') and shutil.which('xauth')
    and importlib.util.find_spec('Xlib'), 'Linux, pidfd, Xvfb and Xlib required')
class OwnedSupervisorCapabilityTests(unittest.TestCase):
    def test_capability_arguments_must_be_paired_before_spawn(self):
        with self.assertRaises(ValueError):
            PrestartedCancellationSupervisor(x11_cancel_worker, owned_server_pidfd=3)
        with self.assertRaises(ValueError):
            PrestartedCancellationSupervisor(x11_cancel_worker, owned_server_pid=10)

    def test_received_fd_close_error_never_retries_numeric_descriptor(self):
        from runtime.guarded_x11_v1.cancel_supervisor import _serve_one_with_server_guard
        fd, write_fd = os.pipe()
        self.addCleanup(os.close, write_fd)
        endpoint = Mock()
        guard = Mock()
        original_close = os.close
        calls = []
        replacement = []
        def close_then_fail(number):
            calls.append(number)
            original_close(number)
            replacement.append(os.open(os.devnull, os.O_RDONLY))
            raise OSError('injected close ambiguity')
        with patch('runtime.guarded_x11_v1.pidfd_transfer.receive_pidfd', return_value=fd), \
             patch('runtime.guarded_x11_v1.owned_xlib_connector.OwnedXlibConnector', return_value=guard), \
             patch('runtime.guarded_x11_v1.cancel_supervisor.os.close', side_effect=close_then_fail):
            with self.assertRaisesRegex(OSError, 'injected close ambiguity'):
                _serve_one_with_server_guard(endpoint, 10)
        try:
            self.assertEqual(calls, [fd])
            self.assertEqual(replacement, [fd])
            os.fstat(replacement[0])
            guard.close.assert_called_once()
        finally:
            for replacement_fd in replacement:
                try:
                    original_close(replacement_fd)
                except OSError:
                    pass
    def test_send_and_spawn_failures_close_endpoints_but_keep_caller_fd(self):
        fd = os.pidfd_open(os.getpid())
        self.addCleanup(os.close, fd)
        options = dict(xauthority='/unused', pinned_display_name=':99',
                       expected_owner={'pid':os.getpid(), 'resource_base':123},
                       owned_server_pidfd=fd, owned_server_pid=os.getpid())
        for phase in ('send', 'spawn'):
            with self.subTest(phase=phase):
                baseline = len(os.listdir('/proc/self/fd'))
                context = multiprocessing.get_context('spawn')
                target = ('runtime.guarded_x11_v1.pidfd_transfer.send_pidfd'
                          if phase == 'send' else
                          'runtime.guarded_x11_v1.cancel_supervisor.multiprocessing.get_context')
                failure = (patch(target, side_effect=OSError('send failed')) if phase == 'send'
                           else patch(target, return_value=context))
                with failure:
                    if phase == 'spawn':
                        with patch.object(context, 'Process', side_effect=OSError('spawn failed')):
                            with self.assertRaises(OSError):
                                PrestartedCancellationSupervisor(x11_cancel_worker, **options)
                    else:
                        with self.assertRaises(OSError):
                            PrestartedCancellationSupervisor(x11_cancel_worker, **options)
                os.fstat(fd)
                self.assertEqual(len(os.listdir('/proc/self/fd')), baseline)
    def test_guarded_supervisor_releases_retired_owner_key(self):
        from Xlib import X, XK, display
        from Xlib.ext import xtest
        from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
        with tempfile.TemporaryDirectory() as tmp:
            owner = PrivateDisplayOwner(Path(tmp) / 'display')
            self.addCleanup(owner.close)
            session = owner.start(timeout_s=5)
            with patch.dict(os.environ, {'XAUTHORITY':str(session.authority)}):
                observer = display.Display(session.display)
            self.addCleanup(observer.close)
            code = observer.keysym_to_keycode(XK.string_to_keysym('a'))
            context = multiprocessing.get_context('spawn')
            ready_recv, ready_send = context.Pipe(False)
            stop_recv, stop_send = context.Pipe(False)
            process = context.Process(target=_owner_client,
                args=(session.display, str(session.authority), ready_send, stop_recv))
            process.start()
            ready_send.close()
            stop_recv.close()
            supervisor = None
            try:
                self.assertTrue(ready_recv.poll(5))
                expected = ready_recv.recv()
                fd, server_pid = owner.duplicate_server_pidfd(timeout_s=1)
                try:
                    supervisor = PrestartedCancellationSupervisor(
                        x11_cancel_worker, xauthority=str(session.authority),
                        pinned_display_name=session.display, expected_owner=expected,
                        owned_server_pidfd=fd, owned_server_pid=server_pid)
                finally:
                    os.close(fd)
                xtest.fake_input(observer, X.KeyPress, code)
                observer.sync()
                self.assertTrue(_key_down(observer, code))
                stop_send.send('stop')
                process.join(3)
                self.assertEqual(process.exitcode, 0)
                request = {'operation_id':'release', 'session_id':'session',
                    'owner_process_retired':True, 'owner_process_exitcode':process.exitcode,
                    'owner_pid':expected['pid'], 'x_resource_base':expected['resource_base'],
                    'binding_revision':0, 'owner_generation':{'session_id':'session',
                        'child_pid':expected['pid'], 'x_resource_base':expected['resource_base'],
                        'binding_revision':0}, 'keys':{'a':code}, 'buttons':[],
                    'display_name':session.display}
                result = supervisor.run(request,
                    deadline_monotonic_ns=time.monotonic_ns()+2_000_000_000)
                observer.sync()
                self.assertFalse(_key_down(observer, code), result)
                self.assertEqual(result['owner_release_attempt']['status'], 'readback_verified')
                self.assertEqual(result['cleanup_status'], 'UNKNOWN')
                self.assertFalse(result['release_confirmed'])
            finally:
                try:
                    xtest.fake_input(observer, X.KeyRelease, code)
                    observer.sync()
                finally:
                    if supervisor is not None:
                        supervisor.close()
                    if process.is_alive():
                        process.terminate()
                        process.join(3)
                    ready_recv.close()
                    stop_send.close()
    def test_readiness_failure_retires_started_child_and_keeps_caller_fd(self):
        fd = os.pidfd_open(os.getpid())
        self.addCleanup(os.close, fd)
        options = dict(xauthority='/unused', pinned_display_name=':99',
                       expected_owner={'pid':os.getpid(), 'resource_base':123},
                       owned_server_pidfd=fd, owned_server_pid=os.getpid(),
                       terminate_grace_s=1.0)
        for delay in (0.0, 5.0):
            with self.subTest(delay=delay):
                context = multiprocessing.get_context('spawn')
                original_process = context.Process
                started = []
                def substitute(*, target, args, name):
                    process = original_process(target=_hold_readiness,
                                               args=(args[4], delay), name=name)
                    started.append(process)
                    return process
                try:
                    with patch('runtime.guarded_x11_v1.cancel_supervisor.multiprocessing.get_context',
                               return_value=context), \
                         patch.object(context, 'Process', side_effect=substitute):
                        if delay == 0.0:
                            with self.assertRaises(EOFError):
                                PrestartedCancellationSupervisor(
                                    x11_cancel_worker, startup_timeout_s=3.0, **options)
                        else:
                            with self.assertRaisesRegex(RuntimeError, 'readiness timed out'):
                                PrestartedCancellationSupervisor(
                                    x11_cancel_worker, startup_timeout_s=0.5, **options)
                    self.assertEqual(len(started), 1)
                    started[0].join(3)
                    self.assertFalse(started[0].is_alive())
                    self.assertIsNotNone(started[0].exitcode)
                    os.fstat(fd)
                finally:
                    for process in started:
                        if process.is_alive():
                            process.terminate()
                            process.join(3)
                        if not process.is_alive():
                            process.close()
    def test_owned_server_starts_and_wrong_server_is_refused(self):
        from Xlib import display
        from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
        with tempfile.TemporaryDirectory() as tmp:
            first = PrivateDisplayOwner(Path(tmp) / 'first')
            second = PrivateDisplayOwner(Path(tmp) / 'second')
            self.addCleanup(first.close)
            self.addCleanup(second.close)
            a = first.start(timeout_s=5)
            b = second.start(timeout_s=5)
            with patch.dict(os.environ, {'XAUTHORITY':str(a.authority)}):
                owner = display.Display(a.display)
            self.addCleanup(owner.close)
            expected = {'pid':os.getpid(), 'resource_base':owner.display.info.resource_id_base}
            fd, server_pid = first.duplicate_server_pidfd(timeout_s=1)
            self.addCleanup(os.close, fd)
            good = PrestartedCancellationSupervisor(
                x11_cancel_worker, xauthority=str(a.authority), pinned_display_name=a.display,
                expected_owner=expected, owned_server_pidfd=fd, owned_server_pid=server_pid)
            self.addCleanup(good.close)
            self.assertGreater(good.pid, 0)
            self.assertTrue(good.close()['retired'])
            with self.assertRaises((RuntimeError, EOFError)):
                PrestartedCancellationSupervisor(
                    x11_cancel_worker, xauthority=str(b.authority), pinned_display_name=b.display,
                    expected_owner=expected, owned_server_pidfd=fd, owned_server_pid=server_pid)
