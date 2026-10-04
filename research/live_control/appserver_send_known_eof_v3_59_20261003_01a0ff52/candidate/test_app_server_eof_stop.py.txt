"""EOF must not synchronously drain another transport diagnostic stream."""
import io
import json
import os
from unittest.mock import patch
import unittest

from codex_app_server_client_v2 import AppServerError, CodexAppServerClient


class NoDiagnosticRead:
    def read(self, *_):
        raise AssertionError('EOF caller attempted a diagnostic read')


class InertProcess:
    def __init__(self, messages):
        self._stdin_read_fd, write_fd = os.pipe()
        self.stdin = os.fdopen(write_fd, 'w', encoding='utf-8')
        self.stdout = io.StringIO(''.join(json.dumps(row) + '\n' for row in messages))
        self.stderr = NoDiagnosticRead()

    def poll(self):
        return 0


    def close_streams(self):
        self.stdin.close()
        self.stdout.close()
        os.close(self._stdin_read_fd)


class EofStopRegression(unittest.TestCase):
    def client(self, messages=()):
        process = InertProcess(messages)
        self.addCleanup(process.close_streams)
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

    def test_solicited_reply_survives_stdout_eof(self):
        # The request must be admitted before its solicited response and EOF.
        # An unsolicited future-ID response cannot authorize a new closed send.
        from test_app_server_known_eof import client_fixture
        with client_fixture() as (client, read_fd):
            original = client._write

            def send_then_reply(message, **kwargs):
                original(message, **kwargs)
                self.assertEqual(json.loads(os.read(read_fd, 4096)), message)
                client.process.stdout.rows.put(json.dumps({"id": message["id"], "result": {"usable": True}})+"\n")
                client.process.stdout.close()
                client._reader.join(timeout=1)
                self.assertFalse(client._reader.is_alive())
                self.assertTrue(client._closed)

            with patch.object(client, '_write', send_then_reply):
                self.assertEqual(client.request('fixture/request'), {'usable': True})
            self.assertEqual(client._responses, {})

    def test_queued_notification_survives_stdout_eof(self):
        message = {'method': 'fixture/ready', 'params': {'usable': True}}
        client = self.client([message])
        self.assertEqual(client.wait_notification(lambda row: row.get('method') == 'fixture/ready'), message)
        self.assertEqual(list(client._notifications), [])


if __name__ == '__main__':
    unittest.main()
