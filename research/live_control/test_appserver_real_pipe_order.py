"""Bounded owned-child pipe check; no App Server or model is launched."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

from research.live_control.codex_app_server_client_v2 import CodexAppServerClient

PEER = r'''
import json, sys
for line in sys.stdin:
    request = json.loads(line)
    print(json.dumps({"id": request["id"], "result": request["params"]}), flush=True)
'''


class RealPipeOrderTests(unittest.TestCase):
    def test_immediate_replies_follow_their_sent_markers(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / "journal.jsonl"
            client = CodexAppServerClient([sys.executable, "-B", "-c", PEER],
                                          journal_path=journal)
            try:
                for index in range(20):
                    self.assertEqual(client.request("fixture", {"index": index}, timeout=3),
                                     {"index": index})
            finally:
                client.close(timeout=3)
            self.assertFalse(client._reader.is_alive())
            self.assertIsNotNone(client.process.poll())
            rows = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(rows), 60)
            for index in range(20):
                prepared, sent, received = rows[index * 3:index * 3 + 3]
                self.assertEqual([row["direction"] for row in (prepared, sent, received)],
                                 ["send_prepared", "sent", "received"])
                self.assertEqual(prepared["message"]["id"], index + 1)
                self.assertEqual(sent["message"]["id"], index + 1)
                self.assertEqual(received["message"]["id"], index + 1)
                self.assertEqual(received["message"]["result"], {"index": index})


if __name__ == "__main__":
    unittest.main()
