"""Bounded stderr-reader retirement for detached pipe descendants."""
import os
from pathlib import Path
import signal
import sys
import tempfile
import threading
import time
import unittest

from codex_app_server_client_v2 import CodexAppServerClient


class StderrCloseOrderTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "posix", "owned process-group behavior is POSIX-only")
    def test_close_times_out_before_closing_stderr_held_by_detached_child(self):
        with tempfile.TemporaryDirectory(prefix="appserver-stderr-close-order-") as temporary:
            root = Path(temporary)
            ready = root / "stderr-held"
            pidfile = root / "detached.pid"
            child_code = (
                "import pathlib,sys,time; "
                "pathlib.Path(sys.argv[1]).write_text('READY',encoding='ascii'); "
                "time.sleep(30)"
            )
            parent_code = '''import pathlib,subprocess,sys,time
child = subprocess.Popen([sys.executable, "-c", sys.argv[2], sys.argv[3]],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         start_new_session=True)
ready = pathlib.Path(sys.argv[3])
deadline = time.monotonic() + 3
while (not ready.exists() or ready.read_text(errors="ignore") != "READY") and time.monotonic() < deadline:
    time.sleep(.005)
if not ready.exists() or ready.read_text(errors="ignore") != "READY":
    raise SystemExit(7)
pathlib.Path(sys.argv[1]).write_text(str(child.pid), encoding="ascii")
'''
            client = CodexAppServerClient(
                [sys.executable, "-X", "utf8", "-c", parent_code,
                 str(pidfile), child_code, str(ready)])
            detached_pid = None
            closer = None
            result = {}
            returned_before_cleanup = False
            try:
                self.assertEqual(client.process.wait(timeout=3), 0)
                deadline = time.monotonic() + 3
                while not pidfile.exists() and time.monotonic() < deadline:
                    time.sleep(.005)
                self.assertTrue(pidfile.exists(), "detached stderr holder did not start")
                detached_pid = int(pidfile.read_text(encoding="ascii"))
                self.assertEqual(ready.read_text(encoding="ascii"), "READY")
                client._reader.join(timeout=1)
                self.assertFalse(client._reader.is_alive(), "stdout reader should see parent EOF")
                self.assertTrue(client._stderr_reader.is_alive(), "detached child should retain stderr")

                def close_client():
                    try:
                        client.close(timeout=.05)
                        result["return"] = "returned"
                    except BaseException as error:
                        result["error"] = error
                    result["stderr_closed_at_return"] = client.process.stderr.closed

                closer = threading.Thread(target=close_client)
                closer.start()
                returned_before_cleanup = closer.join(timeout=.3) is None and not closer.is_alive()
            finally:
                if detached_pid is not None:
                    try:
                        os.kill(detached_pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                if closer is not None:
                    closer.join(timeout=2)
                    if closer.is_alive():
                        raise AssertionError("close did not retire after the owned fixture released stderr")
                client.close(timeout=1)
                for stream in (client.process.stdin, client.process.stdout, client.process.stderr):
                    if stream is not None and not stream.closed:
                        stream.close()

            self.assertTrue(returned_before_cleanup, "close hung while closing stderr before joining its reader")
            self.assertIsInstance(result.get("error"), TimeoutError)
            self.assertEqual(str(result["error"]), "app-server stderr close timed out")
            self.assertFalse(result["stderr_closed_at_return"], "timed-out close must leave the reader's stream intact")


if __name__ == "__main__":
    unittest.main()
