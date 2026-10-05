"""A failed bounded finish send must not retain its full child-wait delay."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest


class Planner:
    def __init__(self):
        self.closed = threading.Event()

    def close(self, timeout=1):
        self.closed.set()


def fill_stdin(child):
    fd = child.stdin.fileno()
    os.set_blocking(fd, False)
    total = 0
    try:
        while True:
            total += os.write(fd, b"x" * 65536)
    except BlockingIOError:
        pass
    finally:
        os.set_blocking(fd, True)
    return total


@unittest.skipUnless(os.name == "posix" and hasattr(os, "set_blocking"),
                     "requires POSIX child-pipe semantics")
class FinishFailureWaitTests(unittest.TestCase):
    def test_send_failure_skips_finish_dependent_child_wait(self):
        from doom_controller_failure_cleanup_v1 import ControllerFailureCleanup

        with tempfile.TemporaryDirectory() as directory:
            child = subprocess.Popen(
                [sys.executable, "-u", "-c", "import time; time.sleep(60)"],
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, text=True)
            planner = Planner()
            filled = fill_stdin(child)
            primary = RuntimeError("primary-error")
            observed = {"primary_preserved": False}

            def cleanup():
                try:
                    with ControllerFailureCleanup(planner, Path(directory)) as scope:
                        scope.track(child)
                        raise primary
                except RuntimeError as error:
                    observed["primary_preserved"] = error is primary

            worker = threading.Thread(target=cleanup, daemon=True)
            worker.start()
            worker.join(3.5)
            completed_before_rescue = not worker.is_alive()
            rescue_needed = child.poll() is None
            try:
                if rescue_needed:
                    child.kill()
                    child.wait(timeout=2)
                worker.join(1)
            finally:
                if child.poll() is None:
                    child.kill()
                    child.wait(timeout=2)
                if worker.is_alive():
                    worker.join(1)

            self.assertGreater(filled, 0)
            self.assertTrue(completed_before_rescue,
                            "cleanup waited for the child after finish send failed")
            self.assertFalse(rescue_needed, "probe had to kill the owned child")
            self.assertTrue(observed["primary_preserved"])
            self.assertTrue(planner.closed.is_set())
            receipt = json.loads((Path(directory) / "controller-failure.json").read_text())
            finish = next(row for row in receipt["stages"]
                          if row["stage"] == "finish_send")
            self.assertEqual(finish["status"], "failed")
            self.assertIn("child_exit_code", receipt)


if __name__ == "__main__":
    unittest.main()
