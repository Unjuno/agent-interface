"""A full real child-stdin pipe must not strand exception cleanup."""
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


class FinishPipeCleanupTests(unittest.TestCase):
    def test_full_child_stdin_does_not_block_bounded_cleanup(self):
        from doom_controller_failure_cleanup_v1 import ControllerFailureCleanup

        with tempfile.TemporaryDirectory() as directory:
            child = subprocess.Popen(
                [sys.executable, "-u", "-c", "import time; time.sleep(60)"],
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                text=True,
                stderr=subprocess.DEVNULL)
            planner = Planner()
            filled = fill_stdin(child)
            primary = RuntimeError("primary-error")
            result = {"primary_preserved": False}

            def cleanup():
                try:
                    with ControllerFailureCleanup(planner, Path(directory)) as scope:
                        scope.track(child)
                        raise primary
                except RuntimeError as error:
                    result["primary_preserved"] = error is primary

            worker = threading.Thread(target=cleanup, daemon=True)
            worker.start()
            worker.join(3.5)
            completed_before_external_cleanup = not worker.is_alive()
            external_kill_needed = child.poll() is None
            try:
                if external_kill_needed:
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
            self.assertTrue(completed_before_external_cleanup,
                            "bounded cleanup remained blocked until probe kill")
            self.assertFalse(external_kill_needed,
                             "test had to kill child to release the finish writer")
            self.assertTrue(result["primary_preserved"])
            self.assertTrue(planner.closed.is_set())
            receipt = json.loads((Path(directory) / "controller-failure.json").read_text())
            finish = next(row for row in receipt["stages"]
                          if row["stage"] == "finish_send")
            self.assertEqual(finish["result"]["status"], "timed_out", repr(finish["result"]))
            self.assertIn("child_exit_code", receipt)


if __name__ == "__main__":
    unittest.main()
