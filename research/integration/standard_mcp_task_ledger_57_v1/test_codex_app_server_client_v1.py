import io
import threading
import unittest
from collections import deque

from codex_app_server_client_v1 import CodexAppServerClient


class CodexAppServerLateUsageTests(unittest.TestCase):
    @staticmethod
    def client():
        client = object.__new__(CodexAppServerClient)
        client._journal = io.BytesIO()
        client._journal_lock = threading.Lock()
        client._condition = threading.Condition()
        client._notifications = deque()
        client._closed = False
        return client

    @staticmethod
    def receive(client, message):
        with client._journal_lock:
            client._record_locked("received", message)
            with client._condition:
                client._notifications.append(message)
                client._condition.notify_all()

    def test_usage_wait_ignores_completion_and_marks_atomic_raw_boundary(self):
        client = self.client()
        first = {"method": "thread/tokenUsage/updated", "params": {
            "threadId": "thread-1", "turnId": "turn-1",
            "tokenUsage": {"last": {"inputTokens": 4}}}}
        self.receive(client, first)
        count, offset = client.turn_usage_snapshot("thread-1", "turn-1")
        self.assertEqual(count, 1)
        completion = {"method": "turn/completed", "params": {
            "threadId": "thread-1", "turn": {"id": "turn-1",
            "status": "completed", "items": [{"type": "agentMessage",
                                                   "text": "stale"}]}}}
        second = {"method": "thread/tokenUsage/updated", "params": {
            "threadId": "thread-1", "turnId": "turn-1",
            "tokenUsage": {"last": {"inputTokens": 6}}}}
        sender = threading.Thread(target=lambda: (
            self.receive(client, completion), self.receive(client, second)))
        sender.start()
        usage, next_count = client.wait_turn_usage_updated(
            "thread-1", "turn-1", after_count=count, timeout=1)
        sender.join(timeout=1)
        self.assertFalse(sender.is_alive())
        self.assertEqual(usage, second["params"]["tokenUsage"])
        self.assertEqual(next_count, 2)
        next_cursor, end = client.turn_usage_snapshot("thread-1", "turn-1")
        self.assertEqual(next_cursor, 2)
        journal = client._journal.getvalue()
        self.assertEqual(end, len(journal))
        self.assertIn(b'"method":"turn/completed"', journal[offset:end])
        self.assertIn(b'"method":"thread/tokenUsage/updated"', journal[offset:end])
        self.assertTrue(any(row.get("method") == "turn/completed"
                            for row in client._notifications))

    def test_usage_wait_times_out_on_completion_or_other_turn_only(self):
        client = self.client()
        self.receive(client, {"method": "turn/completed", "params": {
            "threadId": "thread-1", "turn": {"id": "turn-1"}}})
        self.receive(client, {"method": "thread/tokenUsage/updated", "params": {
            "threadId": "thread-1", "turnId": "turn-other",
            "tokenUsage": {"last": {"inputTokens": 9}}}})
        result = client.wait_turn_usage_updated(
            "thread-1", "turn-1", after_count=0, timeout=0.01)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
