"""Characterize the separate-process LockMask barrier controller on real Xvfb."""
from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest

from Xlib import X, display


class LockActorTest(unittest.TestCase):
    def test_actor_ack_follows_observed_caps_lock_transition(self):
        display_name = os.environ["DISPLAY"]
        observer = display.Display(display_name)
        root = observer.screen().root
        before = int(bool(root.query_pointer().mask & X.LockMask))
        self.assertEqual(before, 0, "fresh Xvfb must begin with Caps Lock off")

        with tempfile.TemporaryDirectory(prefix="lock-actor-") as tmp:
            path = Path(tmp) / "barrier.sock"
            actor_path = Path(__file__).with_name("lock_actor.py")
            actor = subprocess.Popen(
                [sys.executable, "-B", str(actor_path), str(path), display_name],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            try:
                deadline = time.monotonic() + 4
                while not path.exists() and actor.poll() is None and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(path.exists(), "actor must bind its private Unix socket")
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                    client.settimeout(3)
                    client.connect(str(path))
                    client.sendall(b"LOCK_ON\n")
                    raw = client.makefile("rb").readline()
                payload = json.loads(raw)
                self.assertEqual(payload["request"], "LOCK_ON")
                self.assertEqual(payload["pre_lock"], 0)
                self.assertEqual(payload["post_lock"], 1)
                self.assertLessEqual(payload["mutation_sync_ns"], payload["ack_ns"])
                self.assertGreaterEqual(payload["actor_pid"], 1)
                actor.wait(timeout=4)
                self.assertEqual(actor.returncode, 0, actor.stderr.read())
                after = int(bool(root.query_pointer().mask & X.LockMask))
                self.assertEqual(after, 1)
            finally:
                if actor.poll() is None:
                    actor.terminate()
                    actor.wait(timeout=2)
                observer.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
