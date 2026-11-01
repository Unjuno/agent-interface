"""Experimental owned display capability at the owned-session boundary."""
import importlib.util
import multiprocessing
import os
import socket
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch


@unittest.skipUnless(
    sys.platform.startswith('linux') and hasattr(os, 'pidfd_open')
    and shutil.which('Xvfb') and shutil.which('xauth')
    and importlib.util.find_spec('Xlib'), 'Linux, pidfd, Xvfb and Xlib required')
class OwnedSessionDisplayCapabilityTests(unittest.TestCase):
    def test_requires_prestarted_supervisor_and_explicit_authority(self):
        from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                OwnedGuardedSessionOwner({'app':1}, tmp, ':91',
                    _owned_display_owner=object())

    def test_supervisor_is_retired_if_parent_fd_close_is_ambiguous(self):
        from Xlib import X, display
        from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
        from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
        with tempfile.TemporaryDirectory() as tmp:
            server = PrivateDisplayOwner(Path(tmp) / 'server')
            self.addCleanup(server.close)
            session = server.start(timeout_s=5)
            with patch.dict(os.environ, {'XAUTHORITY':str(session.authority)}):
                app = display.Display(session.display)
            self.addCleanup(app.close)
            window = app.screen().root.create_window(10, 10, 100, 80, 0,
                app.screen().root_depth, X.InputOutput, X.CopyFromParent)
            window.map()
            app.sync()
            owner = OwnedGuardedSessionOwner({'app':window.id}, Path(tmp) / 'owner',
                session.display, process_identity=True, query_worker=True,
                prestarted_cancel_supervisor=True, xauthority=str(session.authority),
                _owned_display_owner=server)
            self.addCleanup(owner.close)
            original_duplicate = server.duplicate_server_pidfd
            original_close = os.close
            duplicates = []
            fired = []
            def duplicate(**kwargs):
                row = original_duplicate(**kwargs)
                duplicates.append(row[0])
                return row
            def close_then_fail(fd):
                if len(duplicates) == 2 and fd == duplicates[1] and not fired:
                    fired.append(fd)
                    original_close(fd)
                    raise OSError('injected supervisor fd close ambiguity')
                return original_close(fd)
            with patch.object(server, 'duplicate_server_pidfd', side_effect=duplicate), \
                 patch('runtime.cli_v1.owned_guarded_session.os.close', side_effect=close_then_fail):
                with self.assertRaisesRegex(OSError, 'supervisor fd close ambiguity'):
                    owner._ensure_started()
            self.assertEqual(len(fired), 1)
            self.assertIsNotNone(owner._process)
            self.assertFalse(owner._process.is_alive())
            self.assertIsNotNone(owner._cleanup_supervisor)
            self.assertFalse(owner._cleanup_supervisor._process.is_alive())
            self.assertTrue(owner._startup_supervisor_retirement['retired'])
    def test_retire_error_closes_pipes_and_retains_unknown(self):
        from Xlib import X, display
        from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
        from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
        with tempfile.TemporaryDirectory() as tmp:
            server = PrivateDisplayOwner(Path(tmp) / 'server')
            self.addCleanup(server.close)
            session = server.start(timeout_s=5)
            with patch.dict(os.environ, {'XAUTHORITY':str(session.authority)}):
                app = display.Display(session.display)
            self.addCleanup(app.close)
            window = app.screen().root.create_window(10, 10, 100, 80, 0,
                app.screen().root_depth, X.InputOutput, X.CopyFromParent)
            window.map()
            app.sync()
            owner = OwnedGuardedSessionOwner({'app':window.id}, Path(tmp) / 'owner',
                session.display, process_identity=True, query_worker=True,
                prestarted_cancel_supervisor=True, xauthority=str(session.authority),
                _owned_display_owner=server)
            self.addCleanup(owner.close)
            original_duplicate = server.duplicate_server_pidfd
            original_close = os.close
            duplicates = []
            fired = []
            def duplicate(**kwargs):
                row = original_duplicate(**kwargs)
                duplicates.append(row[0])
                return row
            def close_then_fail(fd):
                if len(duplicates) == 2 and fd == duplicates[1] and not fired:
                    fired.append(fd)
                    original_close(fd)
                    raise OSError('injected supervisor fd close ambiguity')
                return original_close(fd)
            with patch.object(server, 'duplicate_server_pidfd', side_effect=duplicate), \
                 patch('runtime.cli_v1.owned_guarded_session.os.close', side_effect=close_then_fail), \
                 patch.object(owner, '_retire', side_effect=RuntimeError('retire failure')):
                with self.assertRaisesRegex(OSError, 'supervisor fd close ambiguity'):
                    owner._ensure_started()
            self.assertEqual(len(fired), 1)
            self.assertIsNotNone(owner._process)
            self.assertEqual(owner.state, 'failed')
            self.assertTrue(owner._execution_unknown)
            self.assertIsNone(owner._retirement['retired'])
            self.assertTrue(owner._rpc.closed)
            self.assertTrue(owner._control.closed)
            self.assertIsNotNone(owner._cleanup_supervisor)
            self.assertFalse(owner._cleanup_supervisor._process.is_alive())
            self.assertTrue(owner._startup_supervisor_retirement['retired'])
    def test_child_custody_survives_post_start_receiver_close_error(self):
        from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
        from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
        with tempfile.TemporaryDirectory() as tmp:
            server = PrivateDisplayOwner(Path(tmp) / 'server')
            self.addCleanup(server.close)
            session = server.start(timeout_s=5)
            owner = OwnedGuardedSessionOwner({'app':1}, Path(tmp) / 'owner',
                session.display, process_identity=True, query_worker=True,
                prestarted_cancel_supervisor=True, xauthority=str(session.authority),
                _owned_display_owner=server)
            self.addCleanup(owner.close)
            context = multiprocessing.get_context('spawn')
            original_process = context.Process
            original_pair = socket.socketpair
            original_close = socket.socket.close
            saved = {}
            processes = []
            fired = []
            def pair(*args, **kwargs):
                sender, receiver = original_pair(*args, **kwargs)
                saved['receiver'] = receiver
                return sender, receiver
            def process_factory(*args, **kwargs):
                process = original_process(*args, **kwargs)
                processes.append(process)
                return process
            def close_then_fail(sock):
                if sock is saved.get('receiver') and not fired:
                    fired.append(True)
                    original_close(sock)
                    raise OSError('injected receiver close failure')
                return original_close(sock)
            try:
                with patch('runtime.cli_v1.owned_guarded_session.multiprocessing.get_context', return_value=context), \
                     patch.object(context, 'Process', side_effect=process_factory), \
                     patch('runtime.cli_v1.owned_guarded_session.socket.socketpair', side_effect=pair), \
                     patch.object(socket.socket, 'close', close_then_fail):
                    with self.assertRaisesRegex(OSError, 'receiver close failure'):
                        owner._ensure_started()
                self.assertEqual(fired, [True])
                self.assertEqual(len(processes), 1)
                self.assertIs(owner._process, processes[0])
                self.assertFalse(processes[0].is_alive())
                self.assertTrue(owner._retirement['retired'])
            finally:
                for process in processes:
                    if process.pid is not None and process.is_alive():
                        process.terminate()
                        process.join(3)
    def test_correct_display_starts_and_other_display_is_refused(self):
        from Xlib import X, display
        from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
        from runtime.guarded_x11_v1.private_display_owner import PrivateDisplayOwner
        with tempfile.TemporaryDirectory() as tmp:
            a_owner = PrivateDisplayOwner(Path(tmp) / 'a')
            b_owner = PrivateDisplayOwner(Path(tmp) / 'b')
            self.addCleanup(a_owner.close)
            self.addCleanup(b_owner.close)
            a = a_owner.start(timeout_s=5)
            b = b_owner.start(timeout_s=5)
            with patch.dict(os.environ, {'XAUTHORITY':str(a.authority)}):
                app = display.Display(a.display)
            self.addCleanup(app.close)
            win = app.screen().root.create_window(10, 10, 100, 80, 0,
                app.screen().root_depth, X.InputOutput, X.CopyFromParent)
            win.map()
            app.sync()
            expected = {'app':win.id}
            good = OwnedGuardedSessionOwner(expected, Path(tmp) / 'good', a.display,
                process_identity=True, query_worker=True, prestarted_cancel_supervisor=True,
                xauthority=str(a.authority), _owned_display_owner=a_owner)
            self.addCleanup(good.close)
            good._ensure_started()
            self.assertEqual(good.state, 'open')
            self.assertTrue(good._cleanup_supervisor._process.is_alive())
            result = good.close()
            self.assertEqual(result['status'], 'closed', result)
            wrong = OwnedGuardedSessionOwner(expected, Path(tmp) / 'wrong', b.display,
                process_identity=True, query_worker=True, prestarted_cancel_supervisor=True,
                xauthority=str(b.authority), _owned_display_owner=a_owner)
            self.addCleanup(wrong.close)
            with self.assertRaises((RuntimeError, EOFError)):
                wrong._ensure_started()
            self.assertNotEqual(wrong.state, 'open')
