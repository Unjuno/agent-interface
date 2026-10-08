"""Bounded reproduction of stderr-pipe backpressure before a stdout ready event."""
import subprocess
import sys
import threading
import unittest

PAYLOAD_BYTES = 8 * 1024 * 1024
READY_DEADLINE_SECONDS = 2.0
CHILD_EXIT_SECONDS = 3.0


def run_child(*, drain_stderr):
    child_code = (
        "import sys; "
        f"sys.stderr.buffer.write(b'E' * {PAYLOAD_BYTES}); "
        "sys.stderr.buffer.flush(); "
        "sys.stdout.write('READY\\n'); sys.stdout.flush()"
    )
    process = subprocess.Popen(
        [sys.executable, "-c", child_code], stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
    stdout_lines = []
    stderr_bytes = [0]
    ready = threading.Event()

    def read_stdout():
        for line in process.stdout:
            stdout_lines.append(line)
            if line == b"READY\n":
                ready.set()

    def read_stderr():
        while True:
            chunk = process.stderr.read(65536)
            if not chunk:
                return
            stderr_bytes[0] += len(chunk)

    stdout_thread = threading.Thread(target=read_stdout, daemon=True)
    stdout_thread.start()
    stderr_thread = None
    if drain_stderr:
        stderr_thread = threading.Thread(target=read_stderr, daemon=True)
        stderr_thread.start()

    ready_received = ready.wait(READY_DEADLINE_SECONDS)
    child_running_at_deadline = process.poll() is None
    if ready_received:
        process.wait(timeout=CHILD_EXIT_SECONDS)
    else:
        process.terminate()
        process.wait(timeout=CHILD_EXIT_SECONDS)
    stdout_thread.join(timeout=CHILD_EXIT_SECONDS)
    if stderr_thread is not None:
        stderr_thread.join(timeout=CHILD_EXIT_SECONDS)
    process.stdout.close()
    process.stderr.close()
    return {
        "ready_received": ready_received,
        "child_running_at_deadline": child_running_at_deadline,
        "exit_code": process.returncode,
        "stdout": b"".join(stdout_lines),
        "stderr_bytes": stderr_bytes[0],
    }


class PreReadyStderrBackpressureTests(unittest.TestCase):
    def test_stdout_only_drain_blocks_ready_but_concurrent_drain_reaches_ready(self):
        stdout_only = run_child(drain_stderr=False)
        self.assertFalse(stdout_only["ready_received"])
        self.assertTrue(stdout_only["child_running_at_deadline"])

        concurrent = run_child(drain_stderr=True)
        self.assertTrue(concurrent["ready_received"])
        self.assertEqual(concurrent["exit_code"], 0)
        self.assertEqual(concurrent["stdout"], b"READY\n")
        self.assertEqual(concurrent["stderr_bytes"], PAYLOAD_BYTES)


if __name__ == "__main__":
    unittest.main()
