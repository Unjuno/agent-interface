"""Focused checks for P10's protocol-usage extraction and manifest logic."""

import json
from pathlib import Path
import tempfile
import unittest

from research.integration.current_main_appserver_matched_efficiency_20261026_p10.audit_p10 import protocol_usage


class ProtocolUsageTests(unittest.TestCase):
    def test_usage_is_bound_to_exact_thread_and_turn(self):
        rows = [
            {"direction": "received", "message": {"method": "thread/tokenUsage/updated",
             "params": {"threadId": "other", "turnId": "wanted", "tokenUsage": {"last": {
                 "inputTokens": 999, "outputTokens": 999, "reasoningOutputTokens": 999}}}}},
            {"direction": "received", "message": {"method": "thread/tokenUsage/updated",
             "params": {"threadId": "thread", "turnId": "wanted", "tokenUsage": {"last": {
                 "inputTokens": 10, "outputTokens": 2, "reasoningOutputTokens": 1}}}}},
            {"direction": "received", "message": {"method": "turn/completed",
             "params": {"threadId": "thread", "turn": {"id": "wanted", "status": "completed"}}}},
        ]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "protocol.jsonl"
            path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            usage, completed = protocol_usage(path, "thread", "wanted")
        self.assertEqual(usage, {"input_tokens": 10, "output_tokens": 2,
                                 "reasoning_output_tokens": 1})
        self.assertEqual(completed, ["completed"])

    def test_protocol_usage_does_not_accept_turn_completion_without_usage(self):
        row = {"direction": "received", "message": {"method": "turn/completed",
               "params": {"threadId": "thread", "turn": {"id": "wanted", "status": "completed"}}}}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "protocol.jsonl"
            path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            usage, completed = protocol_usage(path, "thread", "wanted")
        self.assertIsNone(usage)
        self.assertEqual(completed, ["completed"])


if __name__ == "__main__":
    unittest.main()
