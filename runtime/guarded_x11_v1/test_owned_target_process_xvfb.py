"""Real XRes/pidfd boundary for explicit disposable target ownership.

The test creates its own private Xvfb and target child. It is opt-in so the
ordinary unit suite never signals an ambient X server or application.
"""
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from Xlib import display

from runtime.guarded_x11_v1.owned_target_process import (
    OwnedTargetProcess, _prestarted_target_identity_worker)
from runtime.guarded_x11_v1.cancel_supervisor import PrestartedCancellationSupervisor
from runtime.cli_v1.owned_guarded_session import OwnedGuardedSessionOwner
from runtime.cli_v1.owned_target_session import OwnedTargetGuardedSessionOwner


def _proc_state(pid):
    stat = Path('/proc', str(pid), 'stat').read_text(encoding='ascii')
    close = stat.rfind(')')
    return stat[close + 1:].split()[0]


@unittest.skipUnless(
    sys.platform.startswith('linux')
    and os.environ.get('AGENT_INTERFACE_OWNED_TARGET_XVFB_TEST') == '1',
    'requires opt-in private Xvfb and disposable target processes',
)
class OwnedTargetProcessXvfbTests(unittest.TestCase):
    def test_xres_binding_allows_exact_child_retirement_while_x_server_is_stopped(self):
        display_name = ':91'
        xvfb = subprocess.Popen(
            ['Xvfb', display_name, '-screen', '0', '800x600x24', '-nolisten', 'tcp'],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, close_fds=True)
        xvfb_pidfd = None
        connection = None
        owner = None
        identity_supervisor = None
        watchdog = None
        try:
            xvfb_pidfd = os.pidfd_open(xvfb.pid, 0)
            deadline = time.monotonic() + 3.0
            socket_path = f'/tmp/.X11-unix/X{display_name[1:]}'
            while time.monotonic() < deadline:
                if xvfb.poll() is not None:
                    self.fail('private Xvfb exited before accepting a connection')
                probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                try:
                    probe.connect(socket_path)
                except OSError:
                    time.sleep(0.02)
                    continue
                finally:
                    probe.close()
                connection = display.Display(display_name)
                break
            self.assertIsNotNone(connection, 'private Xvfb did not become ready')

            with tempfile.TemporaryDirectory(prefix='owned-x11-target-') as root:
                root = Path(root)
                script = root/'target.py'
                xid_file = root/'xid.txt'
                script.write_text(
                    'import os, sys, time\n'
                    'from Xlib import X, display\n'
                    'd=display.Display(os.environ["DISPLAY"])\n'
                    'w=d.screen().root.create_window(10,10,80,60,0,\n'
                    '  d.screen().root_depth,X.InputOutput,X.CopyFromParent)\n'
                    'w.map(); d.sync()\n'
                    'open(sys.argv[1],"w").write(str(w.id))\n'
                    'time.sleep(30)\n', encoding='utf-8')
                target_env = dict(os.environ)
                target_env['DISPLAY'] = display_name
                owner = OwnedTargetProcess.launch(
                    [sys.executable, str(script), str(xid_file)],
                    disposable=True, env=target_env)
                target_deadline = time.monotonic() + 3.0
                while time.monotonic() < target_deadline and not xid_file.exists():
                    if not owner.running:
                        self.fail('launched target exited before creating its X resource')
                    time.sleep(0.01)
                self.assertTrue(xid_file.exists(), 'target XID was not published')
                xid = int(xid_file.read_text(encoding='ascii'))

                binding = owner.bind_x11_target_supervised(display_name, xid)
                self.assertEqual(binding['status'], 'bound', binding)
                self.assertEqual(binding['pid'], owner.pid)

                identity_supervisor = PrestartedCancellationSupervisor(
                    _prestarted_target_identity_worker)

                signal.pidfd_send_signal(xvfb_pidfd, signal.SIGSTOP)
                stop_deadline = time.monotonic() + 1.0
                while time.monotonic() < stop_deadline and _proc_state(xvfb.pid) not in ('T', 't'):
                    time.sleep(0.005)
                self.assertIn(_proc_state(xvfb.pid), ('T', 't'),
                              'private Xvfb did not stop')

                def resume_exact_xvfb():
                    try:
                        signal.pidfd_send_signal(xvfb_pidfd, signal.SIGCONT)
                    except OSError:
                        pass

                watchdog = threading.Timer(1.5, resume_exact_xvfb)
                watchdog.daemon = True
                watchdog.start()
                query_started = time.monotonic()
                prestarted_binding = owner.bind_x11_target_prestarted(
                    identity_supervisor, 'test-child-session', display_name,
                    xid, timeout_s=0.2)
                self.assertEqual(prestarted_binding['status'], 'refused', prestarted_binding)
                self.assertEqual(prestarted_binding['reason'], 'target_identity_unavailable')
                self.assertEqual(prestarted_binding['identity_query']['reason'],
                                 'transaction_deadline')
                self.assertTrue(prestarted_binding['identity_query']['worker_retired'])
                self.assertLess(time.monotonic() - query_started, 1.0)
                query_started = time.monotonic()
                blocked_binding = owner.bind_x11_target_supervised(
                    display_name, xid, timeout_s=0.2)
                self.assertEqual(blocked_binding['status'], 'refused', blocked_binding)
                self.assertEqual(blocked_binding['reason'], 'target_identity_unavailable')
                self.assertTrue(blocked_binding['identity_query']['worker_retired'])
                self.assertLess(time.monotonic() - query_started, 1.0)
                self.assertIn(_proc_state(xvfb.pid), ('T', 't'))
                session = object.__new__(OwnedTargetGuardedSessionOwner)
                session._target_retirement_lock = threading.RLock()
                session._owned_target_process = owner
                session._owned_target_binding = binding
                session._owned_target_retirement = None
                session._retirement = {'retired':True}
                session._target_identity_supervisor = None
                with patch('runtime.guarded_x11_v1.owned_target_process.signal.pidfd_send_signal',
                           side_effect=PermissionError('injected')):
                    session._attempt_target_retirement()
                self.assertEqual(session._owned_target_retirement['reason'], 'pidfd_signal_failed')
                self.assertTrue(owner.running)
                started = time.monotonic()
                with patch.object(OwnedGuardedSessionOwner, 'close', return_value={
                        'status':'cleanup_failed', 'cleanup_status':'UNKNOWN',
                        'replay_allowed':False}):
                    close_report = session.close()
                retirement = close_report['owned_target_retirement']
                elapsed = time.monotonic() - started
                resume_exact_xvfb()
                self.assertEqual(retirement['status'], 'retired', retirement)
                self.assertTrue(retirement['process_exit_verified'], retirement)
                self.assertEqual(retirement['target_xid'], xid)
                self.assertEqual(retirement['previous_attempt']['reason'], 'pidfd_signal_failed')
                self.assertEqual(close_report['cleanup_status'], 'UNKNOWN')
                self.assertFalse(close_report['replay_allowed'])
                self.assertLess(elapsed, 1.0)
                self.assertFalse(owner.running)
        finally:
            if identity_supervisor is not None:
                identity_supervisor.close()
            if watchdog is not None:
                watchdog.cancel()
            if xvfb_pidfd is not None and xvfb.poll() is None:
                try:
                    signal.pidfd_send_signal(xvfb_pidfd, signal.SIGCONT)
                except OSError:
                    pass
            if owner is not None:
                if owner.running:
                    signal.pidfd_send_signal(owner._pidfd, signal.SIGKILL)
                    owner._process.wait(timeout=1.0)
                owner.close()
            if connection is not None:
                connection.close()
            if xvfb.poll() is None:
                xvfb.terminate()
                xvfb.wait(timeout=1.0)
            if xvfb_pidfd is not None:
                os.close(xvfb_pidfd)


if __name__ == '__main__':
    unittest.main()
