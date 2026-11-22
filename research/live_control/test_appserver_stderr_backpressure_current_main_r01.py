"""Exercise App Server RPC progress while the child emits large stderr bytes."""
import json
import os
import sys
import tempfile
import unittest

from research.live_control.codex_app_server_client_v2 import CodexAppServerClient


CHILD = r'''
import json, sys
sys.stderr.buffer.write(bytes(range(256)) * 4096)
sys.stderr.flush()
request = json.loads(sys.stdin.buffer.readline())
response = {"id": request["id"], "result": {"ok": True}}
sys.stdout.buffer.write((json.dumps(response) + "\n").encode("utf-8"))
sys.stdout.buffer.flush()
'''


class AppServerStderrBackpressureCurrentMainTest(unittest.TestCase):
    @unittest.skipIf(os.name == "nt" and sys.version_info[:2] < (3, 12),
                     "bounded Windows pipe sends require Python 3.12+")
    def test_large_invalid_stderr_does_not_block_rpc_and_keeps_bounded_raw_tail(self):
        with tempfile.TemporaryDirectory(prefix="appserver-stderr-backpressure-") as cwd:
            client = CodexAppServerClient([sys.executable, "-B", "-c", CHILD], cwd=cwd)
            closed = False
            try:
                result = client.request("stderr/probe", {}, timeout=2.0)
                self.assertEqual(result, {"ok": True})
                client.close(timeout=3.0)
                closed = True

                snapshot = client.stderr_snapshot()
                self.assertEqual(snapshot["bytes_received"], 1_048_576)
                self.assertTrue(snapshot["complete"])
                self.assertIsNone(snapshot["error"])
                self.assertEqual(snapshot["tail"], bytes(range(256)) * 256)
            finally:
                if not closed:
                    client.close(timeout=3.0)


if __name__ == "__main__":
    unittest.main()
