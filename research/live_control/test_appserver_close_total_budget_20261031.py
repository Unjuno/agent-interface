"""Total budget for bounded close stages; no process or provider is launched."""
import threading
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from research.live_control.codex_app_server_client_v2 import CodexAppServerClient

class CloseBudgetTests(unittest.TestCase):
    def test_process_wait_spends_budget_before_reader_join(self):
        now = [100.0]
        seen = []
        class Process:
            def poll(self): return None
            def terminate(self): pass
            def wait(self, timeout=None):
                seen.append(("process", timeout))
                now[0] += 2.0
        class Reader:
            def join(self, timeout=None): seen.append(("reader", timeout))
            def is_alive(self): return False
        client = CodexAppServerClient.__new__(CodexAppServerClient)
        client._condition = threading.Condition()
        client.process = Process()
        client._reader = Reader()
        client._journal = None
        with patch("research.live_control.codex_app_server_client_v2.time.monotonic", side_effect=lambda: now[0]):
            client.close(timeout=5)
        self.assertEqual(seen, [("process", 2.5), ("reader", 3.0)])

    def test_journal_lock_receives_only_remaining_time(self):
        now = [200.0]
        seen = []
        class Process:
            def poll(self): return 0
        class Reader:
            def join(self, timeout=None):
                now[0] += 4.0
            def is_alive(self): return False
        class JournalLock:
            def acquire(self, timeout=None):
                seen.append(timeout)
                return False
        client = CodexAppServerClient.__new__(CodexAppServerClient)
        client._condition = threading.Condition()
        client.process = Process()
        client._reader = Reader()
        client._journal = SimpleNamespace(closed=False)
        client._journal_lock = JournalLock()
        with patch("research.live_control.codex_app_server_client_v2.time.monotonic", side_effect=lambda: now[0]):
            with self.assertRaisesRegex(TimeoutError, "journal close timed out"):
                client.close(timeout=5)
        self.assertEqual(seen, [1.0])

if __name__ == "__main__": unittest.main()
