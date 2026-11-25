"""Win32 process-tree tests using locally generated, finite dummy processes."""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import threading
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

    def test_final_lease_io_cannot_move_completion_past_deadline(self):
        read_accounting = job.read_accounting
        observed_empty = False
        with TemporaryDirectory() as directory:
            root = Path(directory)

            def account(*args):
                nonlocal observed_empty
                counts = read_accounting(*args)
                observed_empty = counts.ActiveProcesses == 0
                return counts

            def delayed_lease():
                if observed_empty:
                    time.sleep(.7)
                return False

            with patch.object(job, "read_accounting", side_effect=account):
                report = job.run_owned([sys.executable, "-B", "-c", "pass"],
                                       root / "out", root / "err", timeout=.6,
                                       owner_lost=delayed_lease)
            self.assertTrue(observed_empty)
            self.assertEqual(report["status"], "TIMED_OUT")
            self.assertTrue(report["job_empty"])

    def test_expired_or_rolled_back_lease_cannot_be_renewed(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            writer = job.LeaseWriter(root)
            writer.write(4)
            reader = job.LeaseReader(root, writer.nonce)
            seen = reader.seen
            writer.write(3)
            self.assertFalse(reader.lost())
            self.assertEqual(reader.seen, seen)
            self.assertEqual(reader.last, 4)
            writer.write(5)
            reader.seen = time.monotonic() - job.LEASE_TIMEOUT - .1
            self.assertTrue(reader.lost())
            self.assertEqual(reader.last, 4)

    def test_initial_read_failure_requires_a_fresh_lease_increment_to_launch(self):
        owner_code = """
import sys
from pathlib import Path
from unittest.mock import patch
from research.live_control import native_preflight_job_v1 as job
from research.live_control.native_app_server_job_v1 import own_app_server

root = Path(sys.argv[1])
writer = job.LeaseWriter(root)
writer.write(14400)
read_text = Path.read_text
lease_reads = 0

def read_with_initial_failure(path, *args, **kwargs):
    global lease_reads
    if path == writer.path:
        lease_reads += 1
        if lease_reads == 1:
            raise PermissionError("lease file temporarily unavailable")
        if lease_reads == 3 and sys.argv[2] == "renew":
            writer.write(14401)
    return read_text(path, *args, **kwargs)

child = "import sys; from pathlib import Path; Path(sys.argv[1]).write_text('ran')"
with patch.object(Path, "read_text", read_with_initial_failure), patch.object(job, "LEASE_TIMEOUT", 1):
    try:
        result = own_app_server(root, writer.nonce,
                                [sys.executable, "-B", "-c", child, str(root / "ran")], timeout=2)
    except TimeoutError:
        result = 124
raise SystemExit(result)
"""
        for mode, expected_code in (("stale", 124), ("renew", 0)):
            with self.subTest(mode=mode), TemporaryDirectory() as directory:
                root = Path(directory)
                owner = subprocess.run([sys.executable, "-B", "-c", owner_code, str(root), mode],
                                       creationflags=subprocess.CREATE_NO_WINDOW,
                                       capture_output=True, timeout=5)
                self.assertEqual(owner.returncode, expected_code, owner.stderr)
                self.assertEqual((root / "ran").is_file(), mode == "renew")

    def test_initial_lease_reads_share_one_deadline(self):
        with TemporaryDirectory() as directory:
            elapsed = 0
            observations = iter(((.25, None), (.75, 8), (1.125, 9)))

            def read():
                nonlocal elapsed
                elapsed, value = next(observations)
                return value

            with patch.object(job, "LEASE_TIMEOUT", 1), \
                 patch.object(job.LeaseReader, "read", side_effect=read), \
                 patch.object(job.time, "monotonic", side_effect=lambda: elapsed), \
                 patch.object(job.time, "sleep"):
                reader = job.LeaseReader(Path(directory), "a" * 32)
                with self.assertRaises(TimeoutError):
                    reader.await_owner()

    def test_lease_read_returning_after_expiry_cannot_renew(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            writer = job.LeaseWriter(root)
            writer.write(4)
            reader = job.LeaseReader(root, writer.nonce)
            watermark = reader.seen
            before, after = watermark + job.LEASE_TIMEOUT - .1, watermark + job.LEASE_TIMEOUT + .1
            with patch.object(job.time, "monotonic", side_effect=[before, after]), \
                 patch.object(reader, "read", return_value=5):
                self.assertTrue(reader.lost())
            self.assertEqual((reader.last, reader.seen), (4, watermark))

    def test_lease_read_blocks_only_the_monitor(self):
        entered = threading.Event()
        release = threading.Event()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            writer = job.LeaseWriter(root)
            writer.write(0)
            reader = job.LeaseReader(root, writer.nonce)

            def blocked_read():
                entered.set()
                release.wait(4)
                return 1

            with patch.object(reader, "read", side_effect=blocked_read), job.LeaseMonitor(reader) as monitor:
                try:
                    self.assertTrue(entered.wait(1))
                    report = job.run_owned([sys.executable, "-B", "-c", "from time import sleep; sleep(4)"],
                                           root / "out", root / "err", timeout=.4,
                                           owner_lost=monitor.retired)
                    self.assertTrue(entered.is_set())
                    self.assertFalse(release.is_set())
                    self.assertEqual(report["status"], "TIMED_OUT")
                    self.assertTrue(report["job_empty"])
                finally:
                    release.set()

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

    @unittest.skipIf(sys.version_info[:2] < (3, 12), "App Server Windows pipes require Python 3.12")
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
