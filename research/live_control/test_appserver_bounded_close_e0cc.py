"""Native descriptor custody and unsupported custom-stream boundaries."""
import io
import os
import subprocess
import sys
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import codex_app_server_client_v2 as module


class BoundedCloseTests(unittest.TestCase):
    def test_write_only_custom_stream_fails_before_journal_or_admission(self):
        client = object.__new__(module.CodexAppServerClient)
        client.process = SimpleNamespace(stdin=io.StringIO())
        client._write_lock = threading.Lock()
        client._condition = threading.Condition()
        client._closed = client._closing = client._send_uncertain = False
        client._stdin_fd = None
        client._pending = set()
        client._record = Mock()
        with self.assertRaises(module.AppServerUnsupportedRuntime):
            client._write({'id': 1, 'method': 'fixture'}, request_id=1)
        client._record.assert_not_called()
        self.assertEqual(client._pending, set())
        self.assertEqual(client.process.stdin.getvalue(), '')
        self.assertFalse(client._send_uncertain)

    @unittest.skipUnless(os.name == 'posix', 'owned POSIX process/pipe retirement')
    def test_active_writer_keeps_descriptor_until_bounded_close_can_own_it(self):
        # A controlled critical-section hold represents a suspended writer;
        # no actual input or outside process is involved.
        peer = "import time; print('{\"method\":\"fixture/ready\"}', flush=True); time.sleep(30)"
        client = module.CodexAppServerClient([sys.executable, '-B', '-c', peer])
        try:
            client.wait_notification(lambda row: row.get('method') == 'fixture/ready', timeout=2)
            fd = client.process.stdin.fileno()
            identity = os.fstat(fd)
            client._stdin_fd = fd
            client._write_lock.acquire()
            try:
                with self.assertRaisesRegex(TimeoutError, 'writer close timed out'):
                    client.close(timeout=.05)
                self.assertIsNotNone(client.process.poll())
                self.assertFalse(client._reader.is_alive())
                for name in ('stdin', 'stdout', 'stderr'):
                    self.assertFalse(getattr(client.process, name).closed)
                self.assertEqual(os.fstat(fd), identity)
                self.assertEqual(client._stdin_fd, fd)
            finally:
                client._write_lock.release()
            before = client._next_id
            with self.assertRaisesRegex(module.AppServerError, 'closed before send'):
                client.request('fixture/after-close', timeout=.1)
            self.assertEqual(client._next_id, before + 1)
            self.assertEqual(client._pending, set())
            client.close(timeout=1)
            self.assertIsNone(client._stdin_fd)
            for name in ('stdin', 'stdout', 'stderr'):
                self.assertTrue(getattr(client.process, name).closed)
        finally:
            if client.process.poll() is None:
                client.process.kill()
                client.process.wait(timeout=2)
            client.close(timeout=1)


if __name__ == '__main__':
    unittest.main()
