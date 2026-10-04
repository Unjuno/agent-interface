"""Valid UTF8 replies/notifications survive a locale-default text transport."""
import io
import json
import unittest

from codex_app_server_client_v2 import CodexAppServerClient


class EncodingAwareProcess:
    """Real TextIO decoding with a deterministic CP932 factory default."""
    def __init__(self, wire, encoding):
        self.stdin = io.StringIO()
        self.stdout = io.TextIOWrapper(io.BytesIO(wire), encoding=encoding, errors="strict")
        self.stderr = io.StringIO()

    def poll(self):
        return 0


class Utf8ReceiveRegression(unittest.TestCase):
    def client(self, messages):
        wire = ("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in messages)).encode("utf-8")
        def factory(_command, **kwargs):
            return EncodingAwareProcess(wire, kwargs.get("encoding", "cp932"))
        client = CodexAppServerClient([], process_factory=factory)
        client._reader.join(timeout=1)
        self.assertFalse(client._reader.is_alive(), "finite text reader did not stop")
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
