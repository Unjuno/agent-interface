"""EOF must not synchronously drain another transport diagnostic stream."""
import io
import json
import threading
import unittest

from codex_app_server_client_v2 import AppServerError, CodexAppServerClient


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


if __name__ == '__main__':
    unittest.main()
