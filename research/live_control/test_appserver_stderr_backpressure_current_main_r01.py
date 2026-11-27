"""Exercise App Server RPC progress while the child emits large stderr bytes."""
import json
import os
import signal
import sys
import tempfile
import threading
import time
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

HOLDING_CHILD = r'''
import sys, time
with open(sys.argv[1], "w", encoding="ascii") as stream:
    stream.write(str(__import__("os").getpid()))
time.sleep(60)
'''

ORPHANING_PARENT = r'''
import os, subprocess, sys
options = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL,
           "close_fds": True}
if os.name == "posix":
    options["start_new_session"] = True
subprocess.Popen([sys.executable, "-B", "-c", sys.argv[2], sys.argv[1]], **options)
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

    @unittest.skipIf(os.name == "nt" and sys.version_info[:2] < (3, 12),
                     "bounded Windows pipe sends require Python 3.12+")
    def test_close_timeout_keeps_stderr_open_until_orphaned_writer_retires(self):
        with tempfile.TemporaryDirectory(prefix="appserver-stderr-orphan-") as cwd:
            pid_path = os.path.join(cwd, "writer.pid")
            client = CodexAppServerClient(
                [sys.executable, "-B", "-c", ORPHANING_PARENT,
                 pid_path, HOLDING_CHILD], cwd=cwd)
            child_pid = None
            close_result = {}
            close_thread = None
            try:
                self.assertEqual(client.process.wait(timeout=3.0), 0)
                deadline = time.monotonic() + 3.0
                while not os.path.exists(pid_path) and time.monotonic() < deadline:
                    time.sleep(0.005)
                self.assertTrue(os.path.exists(pid_path), "stderr holder did not start")
                with open(pid_path, encoding="ascii") as stream:
                    child_pid = int(stream.read())
                client._reader.join(timeout=1.0)
                self.assertFalse(client._reader.is_alive(),
                                 "parent stdout reader must retire before close-boundary check")

                def bounded_close():
                    try:
                        client.close(timeout=0.1)
                        close_result["return"] = "returned"
                    except BaseException as error:
                        close_result["error"] = error
                    close_result["stderr_closed_at_return"] = client.process.stderr.closed

                close_thread = threading.Thread(target=bounded_close)
                close_thread.start()
                close_thread.join(timeout=0.3)
                returned_before_release = not close_thread.is_alive()
            finally:
                if child_pid is not None:
                    try:
                        os.kill(child_pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                if close_thread is not None:
                    close_thread.join(timeout=3.0)
                    self.assertFalse(close_thread.is_alive(), "close did not finish after stderr EOF")
                client.close(timeout=3.0)

            self.assertTrue(returned_before_release,
                            "close blocked while closing a stream still owned by its reader")
            self.assertIsInstance(close_result.get("error"), TimeoutError)
            self.assertEqual(str(close_result["error"]),
                             "app-server stderr reader close timed out")
            self.assertFalse(close_result["stderr_closed_at_return"],
                             "timed-out close must leave the stderr stream intact")
            self.assertTrue(client.stderr_snapshot()["complete"])


if __name__ == "__main__":
    unittest.main()
