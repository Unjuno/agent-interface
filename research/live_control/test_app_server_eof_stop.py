"""EOF must not synchronously drain another transport diagnostic stream."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import threading
import unittest
from unittest.mock import patch

from codex_app_server_client_v2 import AppServerError, CodexAppServerClient
from native_preflight_job_v1 import LeaseWriter


class NoDiagnosticRead:
    def read(self, *_):
        raise AssertionError('EOF caller attempted a diagnostic read')


class InertProcess:
    def __init__(self, messages):
        self.stdin = io.StringIO()
        self.stdout = io.StringIO(''.join(json.dumps(row) + '\n' for row in messages))
        self.stderr = NoDiagnosticRead()

    def poll(self):
        return 0


class BlockingStdout:
    def __init__(self):
        self.stopped = threading.Event()

    def __iter__(self):
        return self

    def __next__(self):
        if not self.stopped.wait(2):
            raise RuntimeError("test process did not close stdout")
        raise StopIteration


class BlockingProcess:
    def __init__(self):
        self.stdin = io.StringIO()
        self.stdout = BlockingStdout()
        self.stderr = NoDiagnosticRead()

    def poll(self):
        return 0 if self.stdout.stopped.is_set() else None

    def terminate(self):
        self.stdout.stopped.set()

    def wait(self, timeout=None):
        if not self.stdout.stopped.wait(timeout):
            raise TimeoutError("test process termination timed out")
        return 0


class EofStopRegression(unittest.TestCase):
    def client(self, messages=()):
        process = InertProcess(messages)
        client = CodexAppServerClient([], process_factory=lambda *args, **kwargs: process)
        client._reader.join(timeout=1)
        self.assertFalse(client._reader.is_alive())
        self.addCleanup(client.close)
        return client

    def test_request_eof_does_not_read_stderr(self):
        client = self.client()
        with self.assertRaisesRegex(AppServerError, 'closed before send'):
            client.request('fixture/request', timeout=1)

    def test_notification_eof_does_not_read_stderr(self):
        client = self.client()
        with self.assertRaisesRegex(AppServerError, 'closed while waiting'):
            client.wait_notification(lambda row: True, timeout=1)

    def test_unissued_reply_is_not_reused_after_stdout_eof(self):
        reply = {'id': 1, 'result': {'usable': True}}
        client = self.client([reply])
        with self.assertRaisesRegex(AppServerError, 'closed before send'):
            client.request('fixture/request')
        self.assertEqual(client._responses, {})
        self.assertEqual(list(client._notifications), [reply])

    def test_queued_notification_survives_stdout_eof(self):
        message = {'method': 'fixture/ready', 'params': {'usable': True}}
        client = self.client([message])
        self.assertEqual(client.wait_notification(lambda row: row.get('method') == 'fixture/ready'), message)
        self.assertEqual(list(client._notifications), [])


    def test_close_unblocks_pending_notification_wait(self):
        process = BlockingProcess()
        client = CodexAppServerClient([], process_factory=lambda *args, **kwargs: process)
        entered = threading.Event()
        errors = []

        def wait_for_turn():
            entered.set()
            try:
                client.wait_notification(lambda row: row.get('method') == 'turn/completed',
                                         timeout=90)
            except Exception as error:
                errors.append(error)

        waiter = threading.Thread(target=wait_for_turn)
        waiter.start()
        self.assertTrue(entered.wait(1))
        client.close(timeout=1)
        waiter.join(timeout=1)
        self.assertFalse(waiter.is_alive())
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], AppServerError)


@unittest.skipUnless(os.name == "posix", "stdio and lease rollback tested with a POSIX dummy")
class StartupRetirementTests(unittest.TestCase):
    def test_owned_reader_start_failure_retires_process_lease_and_streams(self):
        class DummyOwner:
            def __init__(self, root, retirement_error):
                self.lease = LeaseWriter(root)
                self.retirement_error = retirement_error
                self.process = None

            def launch(self, command, options, journal):
                self.lease.__enter__()
                journal("owner_fixture", {})
                self.process = subprocess.Popen(command, **options)
                return self.process

            def retire(self, process, timeout):
                try:
                    if process.poll() is None:
                        process.terminate()
                    process.wait(timeout=timeout)
                    if self.retirement_error is not None:
                        raise self.retirement_error
                finally:
                    self.lease.__exit__()

        cases = (("_drain_stderr", False, None),
                 ("_read", True, OSError("retirement proof unavailable")))
        for method, start_then_fail, retirement_error in cases:
            with self.subTest(reader=method), TemporaryDirectory() as directory:
                root = Path(directory)
                owner = DummyOwner(root, retirement_error)
                error = RuntimeError("synthetic reader startup failure")
                started_clients = []
                thread_start = threading.Thread.start

                def start(thread):
                    target = thread._target
                    if getattr(target, "__name__", None) == method:
                        started_clients.append(target.__self__)
                        if start_then_fail:
                            thread_start(thread)
                        raise error
                    return thread_start(thread)

                try:
                    with patch.object(threading.Thread, "start", start):
                        with self.assertRaises(RuntimeError) as raised:
                            CodexAppServerClient(
                                [sys.executable, "-c", "import time; time.sleep(8)"],
                                journal_path=root / "protocol.jsonl", windows_owner=owner)
                    self.assertIs(raised.exception, error)
                    self.assertIsNotNone(owner.process.poll())
                    self.assertTrue(owner.lease.stop.is_set())
                    self.assertFalse(owner.lease.writer.is_alive())
                    self.assertTrue(all(getattr(owner.process, name).closed
                                        for name in ("stdin", "stdout", "stderr")))
                    self.assertTrue(started_clients[0]._journal.closed)
                    if retirement_error is not None:
                        self.assertIn("app-server startup cleanup failed: OSError", error.__notes__)
                finally:
                    # The pre-fix failure path leaves both owned resources live.
                    owner.lease.__exit__()
                    if owner.process is not None:
                        if owner.process.poll() is None:
                            owner.process.terminate()
                        owner.process.wait(timeout=2)
                        for name in ("stdin", "stdout", "stderr"):
                            getattr(owner.process, name).close()
                    if started_clients:
                        started_clients[0]._journal.close()


if __name__ == '__main__':
    unittest.main()
