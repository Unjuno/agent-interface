"""Valid UTF8 replies/notifications survive a locale-default text transport."""
import json
import subprocess
import sys
import unittest

from codex_app_server_client_v2 import CodexAppServerClient


class Utf8ReceiveRegression(unittest.TestCase):
    def client(self, messages):
        # Removing the client's explicit UTF-8 transport encoding must break
        # non-ASCII replies even with a CP932 locale-default process factory.
        # The child only replies after observing an actual JSONL request.
        server = (
            "import json,sys; "
            "request=json.loads(sys.stdin.buffer.readline()); "
            "assert request == {'method':'fixture/utf8','id':1}; "
            "rows=json.loads(sys.argv[1]); "
            "sys.stdout.buffer.write((''.join(json.dumps(row,ensure_ascii=False)+'\\n' "
            "for row in rows)).encode('utf-8')); sys.stdout.buffer.flush()"
        )
        def factory(_command, **kwargs):
            kwargs.setdefault("encoding", "cp932")
            return subprocess.Popen(
                [sys.executable, "-c", server, json.dumps(messages)], **kwargs)
        client = CodexAppServerClient([], process_factory=factory)
        self.addCleanup(client.close)
        self.addCleanup(client.process.stdin.close)
        self.addCleanup(client.process.stdout.close)
        self.addCleanup(client.process.stderr.close)
        return client

    def test_ascii_reply_remains_exact(self):
        expected = {"text": "ASCII_OK"}
        client = self.client([{"id": 1, "result": expected}])
        self.assertEqual(client.request("fixture/utf8", timeout=1), expected)

    def test_literal_accented_utf8_reply_remains_exact(self):
        expected = {"text": "caf\u00e9"}
        client = self.client([{"id": 1, "result": expected}])
        self.assertEqual(client.request("fixture/utf8", timeout=1), expected)

    def test_literal_japanese_reply_and_notification_remain_exact(self):
        expected = {"text": "\u65e5\u672c\u8a9e"}
        notification = {"method": "fixture/notice", "params": expected}
        client = self.client([notification, {"id": 1, "result": expected}])
        self.assertEqual(client.request("fixture/utf8", timeout=1), expected)
        self.assertEqual(client.wait_notification(lambda row: row.get("method") == "fixture/notice", timeout=1), notification)


if __name__ == "__main__":
    unittest.main()
