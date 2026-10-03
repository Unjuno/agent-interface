"""EOF must not synchronously drain another transport diagnostic stream."""
import io
import json
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
        with self.assertRaisesRegex(AppServerError, 'closed during fixture/request'):
            client.request('fixture/request', timeout=1)

    def test_notification_eof_does_not_read_stderr(self):
        client = self.client()
        with self.assertRaisesRegex(AppServerError, 'closed while waiting'):
            client.wait_notification(lambda row: True, timeout=1)

    def test_queued_reply_survives_stdout_eof(self):
        client = self.client([{'id': 1, 'result': {'usable': True}}])
        self.assertEqual(client.request('fixture/request'), {'usable': True})
        self.assertEqual(client._responses, {})

    def test_queued_notification_survives_stdout_eof(self):
        message = {'method': 'fixture/ready', 'params': {'usable': True}}
        client = self.client([message])
        self.assertEqual(client.wait_notification(lambda row: row.get('method') == 'fixture/ready'), message)
        self.assertEqual(list(client._notifications), [])


if __name__ == '__main__':
    unittest.main()
