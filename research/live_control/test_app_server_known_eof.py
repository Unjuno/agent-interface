"""Sequential known-EOF admission; fake processes and owned pipes only."""
from contextlib import contextmanager
import io
import os
import queue
import time
import unittest
from unittest.mock import patch

from research.live_control import codex_app_server_client_v2 as module


class ReceiveLane:
    def __init__(self):
        self.rows = queue.Queue()

    def __iter__(self):
        return self

    def __next__(self):
        row = self.rows.get(timeout=2)
        if row is None:
            raise StopIteration
        return row

    def close(self):
        self.rows.put(None)


@contextmanager
def client_fixture(closed=False):
    read_fd, write_fd = os.pipe()

    class Process:
        stdin = os.fdopen(write_fd, 'w', encoding='utf-8')
        stdout = ReceiveLane()
        stderr = io.StringIO()
        exited = False

        def poll(self):
            return 0 if self.exited else None

        def terminate(self):
            self.exited = True
            self.stdout.close()

        def wait(self, timeout=None):
            return 0

    process = Process()
    client = module.CodexAppServerClient([], process_factory=lambda *_a, **_k: process)
    if closed:
        process.stdout.close()
        client._reader.join(timeout=1)
        if client._reader.is_alive() or not client._closed:
            raise AssertionError('fixture did not reach actual reader EOF')
    try:
        yield client, read_fd
    finally:
        client.close(timeout=1)
        if client._reader.is_alive():
            raise AssertionError('fixture reader leaked')
        process.stdin.close()
        process.stderr.close()
        os.close(read_fd)


class KnownEofTests(unittest.TestCase):
    def refuse(self, operation):
        with client_fixture(closed=True) as (client, read_fd):
            with patch.object(client, '_record') as record, patch.object(module.os, 'set_blocking') as mode:
                with self.assertRaises(module.AppServerError):
                    operation(client)
                record.assert_not_called()
                mode.assert_not_called()
            os.set_blocking(read_fd, False)
            with self.assertRaises(BlockingIOError):
                os.read(read_fd, 4096)
            self.assertIsNone(client._stdin_fd)
            self.assertFalse(client._send_uncertain)

    def test_known_eof_request_has_no_send_or_journal(self):
        self.refuse(lambda c: c.request('closed/request', timeout=.1))

    def test_known_eof_notify_has_no_send_or_journal(self):
        self.refuse(lambda c: c.notify('closed/notify', timeout=.1))

    def test_live_notify_preserves_wire(self):
        with client_fixture() as (client, read_fd):
            client.notify('live/notify', timeout=.1)
            self.assertEqual(os.read(read_fd, 4096), b'{"method":"live/notify"}\n')

    def test_solicited_reply_then_eof_remains_consumable(self):
        with client_fixture() as (client, read_fd):
            original = client._write

            def send_then_reply(message, **kwargs):
                original(message, **kwargs)
                self.assertEqual(os.read(read_fd, 4096), b'{"method":"live/request","id":1}\n')
                client.process.stdout.rows.put('{"id":1,"result":{"usable":true}}\n')
                client.process.stdout.close()
                client._reader.join(timeout=1)
                self.assertTrue(client._closed)
                self.assertFalse(client._reader.is_alive())

            with patch.object(client, '_write', send_then_reply):
                self.assertEqual(client.request('live/request', timeout=1), {'usable': True})
            self.assertEqual(client._responses, {})

    def test_uncertain_state_retains_precedence(self):
        with client_fixture(closed=True) as (client, _fd):
            client._send_uncertain = True
            with self.assertRaises(module.AppServerWriteUncertain):
                client.notify('closed', timeout=1)

    def test_invalid_and_expired_budget_retains_precedence(self):
        with client_fixture(closed=True) as (client, _fd):
            with self.assertRaises(ValueError):
                client.notify('closed', timeout=True)
            with self.assertRaises(TimeoutError):
                client._write({'method': 'closed'}, deadline=time.monotonic()-1)
