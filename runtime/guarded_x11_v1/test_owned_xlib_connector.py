"""Contract tests for the opt-in disposable Xlib connection guard."""
import inspect
import os
import threading
import time
import socket
import subprocess
import sys
import unittest
from unittest import mock

try:
    from Xlib.support import connect
except ImportError:
    connect = None


@unittest.skipUnless(sys.platform.startswith('linux') and hasattr(os, 'pidfd_open')
                     and connect is not None, 'Linux pidfd and python-xlib required')
class OwnedXlibConnectorTests(unittest.TestCase):
    def setUp(self):
        from runtime.guarded_x11_v1.owned_xlib_connector import OwnedXlibConnector
        self.connector_type = OwnedXlibConnector
        self.saved = connect.get_socket
        self.addCleanup(setattr, connect, 'get_socket', self.saved)

    def test_same_process_socket_is_accepted_before_authentication(self):
        a, b = socket.socketpair()
        self.addCleanup(a.close)
        self.addCleanup(b.close)
        fd = os.pidfd_open(os.getpid())
        self.addCleanup(os.close, fd)
        connect.get_socket = lambda *_: a
        guard = self.connector_type(fd, os.getpid(), disposable=True)
        self.assertIs(connect.get_socket('unused'), a)
        self.assertTrue(guard.close())
        with self.assertRaises(RuntimeError):
            connect.get_socket('unused')

    def test_wrong_peer_is_closed_and_refused(self):
        child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(10)'])
        self.addCleanup(child.wait)
        self.addCleanup(child.terminate)
        fd = os.pidfd_open(child.pid)
        self.addCleanup(os.close, fd)
        a, b = socket.socketpair()
        self.addCleanup(a.close)
        self.addCleanup(b.close)
        connect.get_socket = lambda *_: a
        guard = self.connector_type(fd, child.pid, disposable=True)
        self.addCleanup(guard.close)
        with self.assertRaisesRegex(RuntimeError, 'peer'):
            connect.get_socket('unused')
        self.assertEqual(a.fileno(), -1)

    def test_ambiguous_close_stays_unknown_and_does_not_retry_fd(self):
        fd = os.pidfd_open(os.getpid())
        self.addCleanup(os.close, fd)
        guard = self.connector_type(fd, os.getpid(), disposable=True)
        real_close = os.close
        closed = []
        def close_then_error(number):
            closed.append(number)
            real_close(number)
            raise OSError('ambiguous close')
        with mock.patch('runtime.guarded_x11_v1.owned_xlib_connector.os.close', side_effect=close_then_error):
            with self.assertRaises(OSError):
                guard.close()
        self.assertFalse(guard.close())
        self.assertEqual(len(closed), 1)

    def test_guard_requires_explicit_disposable_intent(self):
        fd = os.pidfd_open(os.getpid())
        self.addCleanup(os.close, fd)
        with self.assertRaises(ValueError):
            self.connector_type(fd, os.getpid(), disposable=False)

    def test_non_pidfd_is_rejected_without_installing_hook(self):
        read_fd, write_fd = os.pipe()
        self.addCleanup(os.close, read_fd)
        self.addCleanup(os.close, write_fd)
        original = connect.get_socket
        with self.assertRaises(RuntimeError):
            self.connector_type(read_fd, os.getpid(), disposable=True)
        self.assertIs(connect.get_socket, original)

    def test_exited_server_pidfd_is_rejected_without_installing_hook(self):
        child = subprocess.Popen([sys.executable, '-c', 'pass'])
        fd = os.pidfd_open(child.pid)
        self.addCleanup(os.close, fd)
        child.wait(timeout=5)
        original = connect.get_socket
        with self.assertRaises(RuntimeError):
            self.connector_type(fd, child.pid, disposable=True)
        self.assertIs(connect.get_socket, original)

    def test_duplicate_installation_is_rejected(self):
        fd = os.pidfd_open(os.getpid())
        self.addCleanup(os.close, fd)
        guard = self.connector_type(fd, os.getpid(), disposable=True)
        self.addCleanup(guard.close)
        with self.assertRaisesRegex(RuntimeError, 'already installed'):
            self.connector_type(fd, os.getpid(), disposable=True)
        self.assertIs(connect.get_socket, guard)
    def test_concurrent_installation_has_exactly_one_winner(self):
        fd = os.pidfd_open(os.getpid())
        self.addCleanup(os.close, fd)
        source, start = inspect.getsourcelines(self.connector_type.__init__)
        pause_line = start + next(i for i, line in enumerate(source)
                                  if 'self._original = connect.get_socket' in line)
        rendezvous = threading.Barrier(2)
        results = []
        def worker():
            def trace(frame, event, arg):
                if event == 'line' and frame.f_code is self.connector_type.__init__.__code__ and frame.f_lineno == pause_line:
                    time.sleep(0.1)
                return trace
            sys.settrace(trace)
            try:
                rendezvous.wait(timeout=3)
                results.append(('ok', self.connector_type(fd, os.getpid(), disposable=True)))
            except Exception as error:
                results.append(('error', error))
            finally:
                sys.settrace(None)
        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=3)
        guards = [value for status, value in results if status == 'ok']
        for guard in guards:
            self.addCleanup(guard.close)
        self.assertEqual(len(results), 2)
        self.assertEqual(len(guards), 1, results)
        self.assertIs(connect.get_socket, guards[0])
