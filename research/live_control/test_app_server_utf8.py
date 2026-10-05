"""Valid UTF8 replies/notifications survive a locale-default text transport."""
import io
import json
import threading
import unittest

from codex_app_server_client_v2 import CodexAppServerClient


class EncodingAwareProcess:
    """Real TextIO decoding with a deterministic CP932 factory default."""
    def __init__(self, wire, encoding, submitted):
        self.stdin = SignalingInput(submitted)
        self.stdout = GatedTextStream(wire, encoding, submitted)
        self.stderr = io.StringIO()

    def poll(self):
        return 0


class SignalingInput:
    def __init__(self, submitted):
        self._stream = io.StringIO()
        self._submitted = submitted
    def write(self, value):
        self._submitted.set()
        return self._stream.write(value)
    def flush(self):
        return self._stream.flush()
    def close(self):
        return self._stream.close()


class GatedTextStream:
    """Keep the finite reply unread until the client has issued its request."""
    def __init__(self, wire, encoding, submitted):
        self._wire = wire
        self._encoding = encoding
        self._submitted = submitted
    def __iter__(self):
        self._submitted.wait(timeout=2)
        text = io.TextIOWrapper(io.BytesIO(self._wire), encoding=self._encoding, errors="strict")
        yield from text
    def close(self):
        return None


class Utf8ReceiveRegression(unittest.TestCase):
    def client(self, messages):
        submitted = threading.Event()
        wire = ("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in messages)).encode("utf-8")
        def factory(_command, **kwargs):
            return EncodingAwareProcess(wire, kwargs.get("encoding", "cp932"), submitted)
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
        client._reader.join(timeout=1)
        self.assertFalse(client._reader.is_alive())
        client._reader.join(timeout=1)
        self.assertFalse(client._reader.is_alive())

    def test_literal_accented_utf8_reply_remains_exact(self):
        expected = {"text": "caf\u00e9"}
        client = self.client([{"id": 1, "result": expected}])
        self.assertEqual(client.request("fixture/utf8", timeout=1), expected)
        client._reader.join(timeout=1)
        self.assertFalse(client._reader.is_alive())

    def test_literal_japanese_reply_and_notification_remain_exact(self):
        expected = {"text": "\u65e5\u672c\u8a9e"}
        notification = {"method": "fixture/notice", "params": expected}
        client = self.client([notification, {"id": 1, "result": expected}])
        self.assertEqual(client.request("fixture/utf8", timeout=1), expected)
        client._reader.join(timeout=1)
        self.assertFalse(client._reader.is_alive())
        self.assertEqual(client.wait_notification(lambda row: row.get("method") == "fixture/notice", timeout=1), notification)


if __name__ == "__main__":
    unittest.main()
