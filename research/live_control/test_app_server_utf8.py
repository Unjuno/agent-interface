"""Valid UTF8 replies/notifications survive a locale-default text transport."""
import io
import json
import unittest
import threading

from codex_app_server_client_v2 import CodexAppServerClient


class EncodingAwareProcess:
    """Real TextIO decoding with a deterministic CP932 factory default."""
    def __init__(self, wire, encoding):
        admitted = threading.Event()
        class RequestWriter(io.StringIO):
            def flush(self):
                super().flush()
                request = json.loads(self.getvalue().strip())
                if request.get("id") != 1 or request.get("method") != "fixture/utf8":
                    raise ValueError("unexpected fixture request")
                admitted.set()
        class SolicitedReader(io.TextIOWrapper):
            def __next__(self):
                if not admitted.wait(timeout=1):
                    raise TimeoutError("fixture received no complete request")
                return super().__next__()
        self.stdin = RequestWriter()
        self.stdout = SolicitedReader(io.BytesIO(wire), encoding=encoding, errors="strict")
        self.stderr = io.StringIO()

    def poll(self):
        return 0


class Utf8ReceiveRegression(unittest.TestCase):
    def client(self, messages):
        wire = ("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in messages)).encode("utf-8")
        def factory(_command, **kwargs):
            return EncodingAwareProcess(wire, kwargs.get("encoding", "cp932"))
        client = CodexAppServerClient([], process_factory=factory)
        self.addCleanup(client.close)
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
