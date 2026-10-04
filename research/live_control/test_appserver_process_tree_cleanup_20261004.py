"""Real POSIX Popen descendant ownership/retirement regression."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

from codex_app_server_client_v2 import CodexAppServerClient


class AppServerProcessTreeCleanupTests(unittest.TestCase):
    @staticmethod
    def pid_exists(pid):
        # Linux may retain orphaned grandchildren as zombies after SIGKILL.
        # Zombies cannot execute or keep pipes open, even if kill(pid, 0) succeeds.
        stat_path = Path(f"/proc/{pid}/stat")
        try:
            stat = stat_path.read_text(encoding="ascii")
        except (FileNotFoundError, ProcessLookupError):
            stat = None
        if stat is not None:
            state = stat.rsplit(")", 1)[-1].strip().split(maxsplit=1)[0]
            return state != "Z"
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False

    def assert_pid_stopped(self, pid, timeout=3):
        deadline = time.monotonic() + timeout
        while self.pid_exists(pid) and time.monotonic() < deadline:
            time.sleep(.01)
        self.assertFalse(self.pid_exists(pid))

    @unittest.skipUnless(os.name == 'posix', 'POSIX process-group ownership only')
    def test_close_retires_inherited_stdout_descendant_after_leader_exit(self):
        with tempfile.TemporaryDirectory(prefix='appserver-tree-close-') as temporary:
            root = Path(temporary)
            ready = root / 'grandchild-ready'
            pidfile = root / 'grandchild.pid'
            grandchild_code = (
                'import pathlib,signal,sys,time; '
                'signal.signal(signal.SIGTERM,signal.SIG_IGN); '
                'pathlib.Path(sys.argv[1]).write_text("READY",encoding="ascii"); '
                'time.sleep(30)'
            )
            parent_code = '''import pathlib,subprocess,sys,time
child = subprocess.Popen([sys.executable, "-c", sys.argv[2], sys.argv[3]])
ready = pathlib.Path(sys.argv[3])
deadline = time.monotonic() + 3
while (not ready.exists() or ready.read_text(errors="ignore") != "READY") and time.monotonic() < deadline:
    time.sleep(.005)
if not ready.exists() or ready.read_text(errors="ignore") != "READY":
    raise SystemExit(7)
pathlib.Path(sys.argv[1]).write_text(str(child.pid), encoding="ascii")
'''
            command = [sys.executable, '-X', 'utf8', '-c', parent_code,
                       str(pidfile), grandchild_code, str(ready)]
            client = CodexAppServerClient(command)
            grandchild_pid = None
            try:
                self.assertEqual(client.process.wait(timeout=3), 0)
                deadline = time.monotonic() + 3
                while (not pidfile.exists() or
                       not pidfile.read_text(errors='ignore').strip().isdigit()) and time.monotonic() < deadline:
                    time.sleep(.005)
                self.assertEqual(ready.read_text(), 'READY')
                grandchild_pid = int(pidfile.read_text().strip())
                self.assertTrue(self.pid_exists(grandchild_pid))
                self.assertTrue(client._reader.is_alive())

                client.close(timeout=.1)

                self.assertEqual(client.process.returncode, 0)
                self.assert_pid_stopped(grandchild_pid)
                self.assertFalse(client._reader.is_alive())
                self.assertTrue(client.process.stdin.closed)
                self.assertTrue(client.process.stdout.closed)
                self.assertTrue(client.process.stderr.closed)
            finally:
                if grandchild_pid is not None and self.pid_exists(grandchild_pid):
                    os.kill(grandchild_pid, signal.SIGKILL)
                if client._reader.is_alive():
                    client._reader.join(timeout=3)
                for stream in (client.process.stdin, client.process.stdout, client.process.stderr):
                    if stream is not None and not stream.closed:
                        stream.close()


    @unittest.skipUnless(os.name == 'posix', 'POSIX process-group ownership only')
    def test_close_kills_sigterm_ignoring_descendant_without_inherited_pipes(self):
        with tempfile.TemporaryDirectory(prefix='appserver-detached-tree-close-') as temporary:
            root = Path(temporary)
            ready = root / 'grandchild-ready'
            pidfile = root / 'grandchild.pid'
            heartbeat = root / 'grandchild-heartbeat'
            grandchild_code = (
                'import pathlib,signal,sys,time; '
                'signal.signal(signal.SIGTERM,signal.SIG_IGN); '
                'pathlib.Path(sys.argv[1]).write_text("READY",encoding="ascii"); '
                'counter = 0\n'
                'while True:\n'
                '    pathlib.Path(sys.argv[2]).write_text(str(counter), encoding="ascii")\n'
                '    counter += 1\n'
                '    time.sleep(.01)\n'
            )
            parent_code = '''import pathlib,subprocess,sys,time
child = subprocess.Popen([sys.executable, "-c", sys.argv[2], sys.argv[3], sys.argv[4]],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
ready = pathlib.Path(sys.argv[3])
deadline = time.monotonic() + 3
while (not ready.exists() or ready.read_text(errors="ignore") != "READY") and time.monotonic() < deadline:
    time.sleep(.005)
if not ready.exists() or ready.read_text(errors="ignore") != "READY":
    raise SystemExit(7)
pathlib.Path(sys.argv[1]).write_text(str(child.pid), encoding="ascii")
'''
            command = [sys.executable, '-X', 'utf8', '-c', parent_code,
                       str(pidfile), grandchild_code, str(ready), str(heartbeat)]
            client = CodexAppServerClient(command)
            grandchild_pid = None
            try:
                self.assertEqual(client.process.wait(timeout=3), 0)
                deadline = time.monotonic() + 3
                while (not heartbeat.exists() or
                       not pidfile.exists() or
                       not pidfile.read_text(errors='ignore').strip().isdigit()) and time.monotonic() < deadline:
                    time.sleep(.005)
                self.assertEqual(ready.read_text(), 'READY')
                grandchild_pid = int(pidfile.read_text().strip())
                self.assertTrue(self.pid_exists(grandchild_pid))
                client._reader.join(timeout=2)
                self.assertFalse(client._reader.is_alive())

                client.close(timeout=.1)

                stopped_at = heartbeat.read_text()
                time.sleep(.05)
                self.assertEqual(heartbeat.read_text(), stopped_at)
                self.assertFalse(client._reader.is_alive())
                self.assertTrue(client.process.stdout.closed)
            finally:
                if grandchild_pid is not None and self.pid_exists(grandchild_pid):
                    os.kill(grandchild_pid, signal.SIGKILL)
                if client._reader.is_alive():
                    client._reader.join(timeout=3)
                for stream in (client.process.stdin, client.process.stdout, client.process.stderr):
                    if stream is not None and not stream.closed:
                        stream.close()

    @unittest.skipUnless(os.name == 'posix', 'POSIX process-group ownership only')
    def test_close_kills_sigterm_ignoring_descendant_of_live_leader(self):
        with tempfile.TemporaryDirectory(prefix='appserver-live-tree-close-') as temporary:
            root = Path(temporary)
            ready = root / 'grandchild-ready'
            pidfile = root / 'grandchild.pid'
            grandchild_code = (
                'import pathlib,signal,sys,time; '
                'signal.signal(signal.SIGTERM,signal.SIG_IGN); '
                'pathlib.Path(sys.argv[1]).write_text("READY",encoding="ascii"); '
                'time.sleep(30)'
            )
            parent_code = '''import pathlib,subprocess,sys,time
child = subprocess.Popen([sys.executable, "-c", sys.argv[2], sys.argv[3]])
ready = pathlib.Path(sys.argv[3])
deadline = time.monotonic() + 3
while (not ready.exists() or ready.read_text(errors="ignore") != "READY") and time.monotonic() < deadline:
    time.sleep(.005)
if not ready.exists() or ready.read_text(errors="ignore") != "READY":
    raise SystemExit(7)
pathlib.Path(sys.argv[1]).write_text(str(child.pid), encoding="ascii")
time.sleep(30)
'''
            command = [sys.executable, '-X', 'utf8', '-c', parent_code,
                       str(pidfile), grandchild_code, str(ready)]
            client = CodexAppServerClient(command)
            grandchild_pid = None
            try:
                deadline = time.monotonic() + 3
                while (not ready.exists() or
                       ready.read_text(errors='ignore') != 'READY' or
                       not pidfile.exists() or
                       not pidfile.read_text(errors='ignore').strip().isdigit()) and time.monotonic() < deadline:
                    time.sleep(.005)
                self.assertEqual(ready.read_text(), 'READY')
                grandchild_pid = int(pidfile.read_text().strip())
                self.assertIsNone(client.process.poll())
                self.assertTrue(self.pid_exists(grandchild_pid))
                self.assertTrue(client._reader.is_alive())

                client.close(timeout=.1)

                self.assertEqual(client.process.returncode, -signal.SIGTERM)
                self.assert_pid_stopped(grandchild_pid)
                self.assertFalse(client._reader.is_alive())
                self.assertTrue(client.process.stdin.closed)
                self.assertTrue(client.process.stdout.closed)
                self.assertTrue(client.process.stderr.closed)
            finally:
                if client.process.poll() is None:
                    client.process.kill()
                    client.process.wait(timeout=2)
                if grandchild_pid is not None and self.pid_exists(grandchild_pid):
                    os.kill(grandchild_pid, signal.SIGKILL)
                if client._reader.is_alive():
                    client._reader.join(timeout=3)
                for stream in (client.process.stdin, client.process.stdout, client.process.stderr):
                    if stream is not None and not stream.closed:
                        stream.close()


if __name__ == '__main__':
    unittest.main()
