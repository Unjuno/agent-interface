"""Win32 process-tree tests using locally generated, finite dummy processes."""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
import unittest
from unittest.mock import patch

from research.live_control import native_preflight_job_v1 as job
from research.live_control.codex_app_server_client_v2 import CodexAppServerClient


DUMMY = """
import os, pathlib, subprocess, sys, time
marker = sys.argv[1]
grandchild = (
    "import os, pathlib, sys, time; "
    "pathlib.Path(sys.argv[1]).write_text(str(os.getpid())); time.sleep(8)"
)
subprocess.Popen([sys.executable, "-B", "-c", grandchild, marker])
if sys.argv[2] == "wait":
    time.sleep(8)
"""


@unittest.skipUnless(os.name == "nt", "requires the Windows Job Object APIs")
class NativePreflightJobTests(unittest.TestCase):
    def test_normal_exit_receipt(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            report = job.run_owned([sys.executable, "-B", "-c", "print('dummy')"],
                                   root / "out", root / "err", timeout=3)
            owner = {"run_nonce": "a" * 32, "owner_sha256": "b" * 64}
            self.assertTrue(job.completed_receipt({**report, **owner}, 0, minimum_processes=1, **owner))
            self.assertFalse(job.completed_receipt(
                {**report, **owner, "total_processes": 1}, 0, **owner))
            self.assertGreaterEqual(report["total_processes"], 1)
            self.assertEqual((root / "out").read_text().strip(), "dummy")

    def test_empty_observation_after_deadline_cannot_pass(self):
        wait_empty = job.wait_empty
        with TemporaryDirectory() as directory:
            root = Path(directory)

            def slow_proof(*args):
                time.sleep(.4)
                return wait_empty(*args)

            with patch.object(job, "wait_empty", side_effect=slow_proof):
                report = job.run_owned([sys.executable, "-B", "-c", "pass"],
                                       root / "out", root / "err", timeout=.25)
            self.assertEqual(report["status"], "TIMED_OUT")
            self.assertTrue(report["job_empty"])

    def test_timeout_and_premature_root_exit_retire_the_descendant(self):
        for child_mode, status in (("wait", "TIMED_OUT"), ("exit", "DESCENDANTS_ACTIVE")):
            with self.subTest(child_mode=child_mode), TemporaryDirectory() as directory:
                root = Path(directory)
                report = job.run_owned([sys.executable, "-B", "-c", DUMMY,
                                        str(root / "grandchild.pid"), child_mode],
                                       root / "out", root / "err", timeout=2)
                self.assertEqual(report["status"], status)
                self.assertGreaterEqual(report["total_processes"], 2)
                self.assertEqual(report["active_processes"], 0)
                self.assertTrue(report["job_empty"])
                owner = {"run_nonce": "a" * 32, "owner_sha256": "b" * 64}
                self.assertFalse(job.completed_receipt({**report, **owner}, report["exit_code"], **owner))

    def test_close_releases_local_handles_even_when_retirement_fails(self):
        expected = RuntimeError("synthetic peer exit 42")

        class Owner:
            def launch(self, _command, options, _journal):
                return subprocess.Popen([sys.executable, "-B", "-c", "raise SystemExit(42)"],
                                        **options)

            def retire(self, process, timeout):
                process.wait(timeout=timeout)
                raise expected

        with TemporaryDirectory() as directory:
            root = Path(directory)
            client = CodexAppServerClient(["unused"], journal_path=root / "protocol.jsonl",
                                          windows_owner=Owner())
            with self.assertRaises(RuntimeError) as stopped:
                client.close()
            self.assertIs(stopped.exception, expected)
            self.assertTrue(all(stream.closed for stream in
                                (client.process.stdin, client.process.stdout, client.process.stderr)))
            self.assertTrue(client._journal.closed)

    def test_owner_death_closes_the_job_and_only_the_owned_tree(self):
        owner_code = """
import sys
from pathlib import Path
from research.live_control.native_preflight_job_v1 import run_owned
root = Path(sys.argv[1])
run_owned([sys.executable, "-B", "-c", sys.argv[2], str(root / "grandchild.pid"), "wait"],
          root / "out", root / "err", timeout=8)
"""
        api = job.kernel()
        api.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        api.OpenProcess.restype = wintypes.HANDLE
        with TemporaryDirectory() as directory:
            root = Path(directory)
            marker = root / "grandchild.pid"
            with subprocess.Popen([sys.executable, "-B", "-c", owner_code, str(root), DUMMY],
                                  creationflags=subprocess.CREATE_NO_WINDOW) as owner:
                handle = None
                try:
                    deadline = time.monotonic() + 4
                    while not marker.is_file() and owner.poll() is None and time.monotonic() < deadline:
                        time.sleep(.02)
                    # The dummy is the only writer of this exclusively created marker.
                    pid = int(marker.read_text())
                    handle = job.check(api.OpenProcess(0x00100000, False, pid))
                    self.assertEqual(api.WaitForSingleObject(handle, 0), job.WAIT_TIMEOUT)
                    owner.terminate()
                    owner.wait(timeout=3)
                    self.assertEqual(api.WaitForSingleObject(handle, 3000), job.WAIT_OBJECT_0)
                finally:
                    if handle is not None:
                        api.CloseHandle(handle)
                    if owner.poll() is None:
                        owner.terminate()
                        owner.wait(timeout=3)


if __name__ == "__main__":
    unittest.main()
