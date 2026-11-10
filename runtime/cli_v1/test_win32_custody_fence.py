from __future__ import annotations

from contextlib import contextmanager
import multiprocessing
import tempfile
import os
import subprocess
import sys
import threading
import unittest
import uuid
from pathlib import Path

from runtime.cli_v1.win32_custody_fence import (
    CustodyFenceError, Win32CustodyFence,
    _WindowsCustodyAcl,
    _terminate_or_confirm_process_absent,
)


OPERATION = "1" * 32
NEXT_OPERATION = "2" * 32
GENERATION = "a" * 64
NEXT_GENERATION = "b" * 64
OBLIGATIONS = ["key:VK_A"]


class _FakeMutex:
    _locks = {}
    _guard = threading.Lock()
    abandon_next = False

    def __init__(self, name):
        with self._guard:
            self._lock = self._locks.setdefault(name, threading.Lock())

    @contextmanager
    def hold(self):
        with self._lock:
            abandoned = type(self).abandon_next
            type(self).abandon_next = False
            yield abandoned


class _FakeInitializationStore:
    def __init__(self):
        self.present = False

    def exists(self):
        return self.present

    def create(self):
        self.present = True


class _FakeAcl:
    def __init__(self):
        self.directories = []
        self.files = []
        self.registry_keys = []

    def protect_directory(self, path):
        self.directories.append(Path(path))

    def protect_file(self, path):
        self.files.append(Path(path))

    def protect_registry_key(self, key):
        self.registry_keys.append(key)


def _custody_test_sleep_child():
    import time
    time.sleep(30)


class Win32CustodyFenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.digest = "c" * 64
        self.fence = Win32CustodyFence(self.directory, self.digest,
            mutex_factory=_FakeMutex)

    def tearDown(self):
        self.fence.close()
        self.temp.cleanup()

    def reopen(self):
        return Win32CustodyFence(self.directory, self.digest,
            mutex_factory=_FakeMutex)

    def test_unresolved_action_survives_a_new_owner_instance(self):
        self.fence.admit(OPERATION, GENERATION, OBLIGATIONS)
        self.fence.update(OPERATION, GENERATION, phase="unknown",
                          input_dispatched=True)
        reopened = self.reopen()
        try:
            state = reopened.snapshot()["state"]
            self.assertEqual(state["status"], "unresolved")
            self.assertEqual(state["pending"]["operation_id"], OPERATION)
            self.assertEqual(state["pending"]["phase"], "unknown")
            with self.assertRaisesRegex(CustodyFenceError,
                    "ORPHAN_RECOVERY_UNRESOLVED"):
                reopened.admit(NEXT_OPERATION, NEXT_GENERATION, OBLIGATIONS)
            self.assertEqual(reopened.require_recovery_source(
                OPERATION, GENERATION, OBLIGATIONS)["pending"]["input_dispatched"], True)
            with self.assertRaisesRegex(CustodyFenceError,
                    "OBLIGATIONS_MISMATCH"):
                reopened.require_recovery_source(OPERATION, GENERATION, ["key:VK_B"])
        finally:
            reopened.close()

    def test_release_and_required_late_horizon_gate_resolution(self):
        self.fence.admit(OPERATION, GENERATION, OBLIGATIONS)
        with self.assertRaisesRegex(CustodyFenceError,
                "HORIZON_REQUIREMENT_MISMATCH"):
            self.fence.resolve(OPERATION, GENERATION,
                release_confirmed=True, late_input_horizon_verified=True)
        self.assertEqual(self.fence.snapshot()["state"]["status"], "unresolved")
        with self.assertRaisesRegex(CustodyFenceError,
                "LATE_INPUT_HORIZON_UNVERIFIED"):
            self.fence.resolve(OPERATION, GENERATION, release_confirmed=True,
                late_input_horizon_required=True,
                late_input_horizon_verified=False)
        with self.assertRaisesRegex(CustodyFenceError,
                "RELEASE_UNCONFIRMED"):
            self.fence.resolve(OPERATION, GENERATION, release_confirmed=False)
        self.assertEqual(self.fence.snapshot()["state"]["status"], "unresolved")
        self.fence.resolve(OPERATION, GENERATION, release_confirmed=True,
            late_input_horizon_required=True,
            late_input_horizon_verified=True)
        self.assertEqual(self.fence.snapshot()["state"]["status"], "clear")
        self.fence.admit(NEXT_OPERATION, NEXT_GENERATION, OBLIGATIONS)

    def test_unstarted_abort_requires_closed_gate_and_no_emission(self):
        self.fence.admit(OPERATION, GENERATION, OBLIGATIONS)
        self.fence.update(OPERATION, GENERATION, phase="starting")
        with self.assertRaisesRegex(CustodyFenceError, "UNSTARTED_PROOF_REQUIRED"):
            self.fence.abort_unstarted(OPERATION, GENERATION,
                start_gate_verified_closed=True, input_dispatched=True)
        self.fence.abort_unstarted(OPERATION, GENERATION,
            start_gate_verified_closed=True, input_dispatched=False)
        self.assertEqual(self.fence.snapshot()["state"]["status"], "clear")

    def test_missing_or_corrupt_state_with_marker_fails_closed(self):
        self.fence.admit(OPERATION, GENERATION, OBLIGATIONS)
        self.fence._state_path.unlink()
        with self.assertRaisesRegex(CustodyFenceError, "MARKER_STATE_MISMATCH"):
            self.fence.snapshot()

    def test_external_initialization_anchor_detects_deleted_journal(self):
        anchor = _FakeInitializationStore()
        anchored = Win32CustodyFence(self.directory, self.digest,
            mutex_factory=_FakeMutex, initialization_store=anchor)
        anchored.admit(OPERATION, GENERATION, OBLIGATIONS)
        anchored._state_path.unlink()
        with self.assertRaisesRegex(CustodyFenceError, "MARKER_STATE_MISMATCH"):
            anchored.snapshot()
        anchored.close()

    def test_injected_acl_covers_directory_marker_and_every_journal_write(self):
        acl = _FakeAcl()
        secured = Win32CustodyFence(self.directory, self.digest,
            mutex_factory=_FakeMutex, acl=acl)
        secured.snapshot()
        secured.admit(OPERATION, GENERATION, OBLIGATIONS)

        self.assertGreaterEqual(acl.directories.count(self.directory), 2)
        self.assertIn(secured._marker_path, acl.files)
        self.assertGreaterEqual(acl.files.count(secured._state_path), 2)
        secured.close()

    def test_acl_failure_prevents_mutex_or_custody_initialization(self):
        class DeniedAcl:
            def protect_directory(self, _path):
                raise PermissionError("DACL write denied")

        mutex_constructed = []
        def mutex_factory(name):
            mutex_constructed.append(name)
            return _FakeMutex(name)

        with self.assertRaisesRegex(PermissionError, "DACL write denied"):
            Win32CustodyFence(self.directory / "denied", self.digest,
                mutex_factory=mutex_factory, acl=DeniedAcl())
        self.assertEqual(mutex_constructed, [])
        self.assertFalse((self.directory / "denied" /
                          (self.digest + ".json")).exists())

    @unittest.skipUnless(os.name == "nt", "native custody ACL requires Windows")
    def test_native_acl_sets_protected_filesystem_and_registry_dacls(self):
        import ctypes
        import winreg

        acl = _WindowsCustodyAcl()
        directory = Path(self.temp.name) / "native-acl"
        directory.mkdir()
        file_path = directory / "journal.json"
        file_path.write_text("{}", encoding="utf-8")
        acl.protect_directory(directory)
        acl.protect_file(file_path)
        listing = subprocess.run(["icacls.exe", str(file_path)],
            text=True, capture_output=True, timeout=5, check=False)
        self.assertEqual(listing.returncode, 0, listing.stderr)
        self.assertIn("NT AUTHORITY\\SYSTEM:(F)", listing.stdout)
        self.assertIn("BUILTIN\\Administrators:(F)", listing.stdout)

        registry_path = (r"Software\Unjuno\AgentInterface\CustodyAclTest_"
                         + uuid.uuid4().hex)
        advapi = ctypes.WinDLL("advapi32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        advapi.RegGetKeySecurity.argtypes = [ctypes.c_void_p, ctypes.c_uint32,
            ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
        advapi.RegGetKeySecurity.restype = ctypes.c_long
        advapi.ConvertSecurityDescriptorToStringSecurityDescriptorW.argtypes = [
            ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_wchar_p), ctypes.POINTER(ctypes.c_uint32)]
        advapi.ConvertSecurityDescriptorToStringSecurityDescriptorW.restype = ctypes.c_int
        kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        try:
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, registry_path, 0,
                    winreg.KEY_SET_VALUE | 0x00040000 | 0x00020000) as key:
                acl.protect_registry_key(key)
                needed = ctypes.c_uint32()
                security_information = 0x00000004 | 0x80000000
                status = advapi.RegGetKeySecurity(ctypes.c_void_p(key.handle),
                    security_information, None, ctypes.byref(needed))
                self.assertEqual(status, 122)
                descriptor = ctypes.create_string_buffer(needed.value)
                status = advapi.RegGetKeySecurity(ctypes.c_void_p(key.handle),
                    security_information, descriptor, ctypes.byref(needed))
                self.assertEqual(status, 0)
                sddl = ctypes.c_wchar_p()
                self.assertTrue(advapi.ConvertSecurityDescriptorToStringSecurityDescriptorW(
                    descriptor, 1, security_information, ctypes.byref(sddl), None))
                try:
                    self.assertTrue(sddl.value.startswith("D:P"), sddl.value)
                    self.assertIn("A;;KA;;;SY", sddl.value)
                    self.assertIn("A;;KA;;;BA", sddl.value)
                    self.assertIn(acl._sid, sddl.value)
                finally:
                    kernel32.LocalFree(ctypes.cast(sddl, ctypes.c_void_p))
        finally:
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, registry_path)
            except FileNotFoundError:
                pass

    @unittest.skipUnless(os.name == "nt", "native process retirement requires Windows")
    def test_native_recovery_terminates_only_exact_child_process_identity(self):
        from runtime.guarded_win32_v1.win32_process_identity import (
            Win32ProcessIdentityReader,
        )

        context = multiprocessing.get_context("spawn")
        process = context.Process(target=_custody_test_sleep_child)
        process.start()
        try:
            identity = Win32ProcessIdentityReader()(process)
            self.assertTrue(_terminate_or_confirm_process_absent(identity,
                wait_timeout_ms=2000))
            process.join(timeout=2)
            self.assertFalse(process.is_alive())
            self.assertIsInstance(process.exitcode, int)
        finally:
            if process.is_alive():
                process.terminate()
                process.join(timeout=2)
            process.close()

        reused_pid_candidate = context.Process(target=_custody_test_sleep_child)
        reused_pid_candidate.start()
        try:
            exact = Win32ProcessIdentityReader()(reused_pid_candidate)
            stale = {"pid": exact["pid"],
                     "creation_time_100ns": exact["creation_time_100ns"] + 1}
            self.assertTrue(_terminate_or_confirm_process_absent(stale,
                wait_timeout_ms=2000))
            self.assertTrue(reused_pid_candidate.is_alive())
        finally:
            if reused_pid_candidate.is_alive():
                reused_pid_candidate.terminate()
                reused_pid_candidate.join(timeout=2)
            reused_pid_candidate.close()

    @unittest.skipUnless(os.name == "nt", "native custody ACL requires Windows")
    def test_native_acl_fence_survives_reopen_and_journal_transition(self):
        directory = Path(self.temp.name) / "native-fence"
        anchor = _FakeInitializationStore()
        first = Win32CustodyFence(directory, "8" * 64,
            mutex_factory=_FakeMutex, initialization_store=anchor,
            acl=_WindowsCustodyAcl())
        first.admit(OPERATION, GENERATION, OBLIGATIONS)
        first.close()

        reopened = Win32CustodyFence(directory, "8" * 64,
            mutex_factory=_FakeMutex, initialization_store=anchor,
            acl=_WindowsCustodyAcl())
        try:
            pending = reopened.snapshot()["state"]["pending"]
            self.assertEqual(pending["operation_id"], OPERATION)
            self.assertEqual(pending["gate_state"], "closed")
            reopened.abort_unstarted(OPERATION, GENERATION,
                start_gate_verified_closed=True, input_dispatched=False)
            self.assertEqual(reopened.snapshot()["state"]["status"], "clear")
        finally:
            reopened.close()

    def test_abandoned_mutex_refuses_admission(self):
        self.fence.snapshot()  # create the known-clear journal first
        _FakeMutex.abandon_next = True
        with self.assertRaisesRegex(CustodyFenceError, "MUTEX_ABANDONED"):
            self.fence.admit(OPERATION, GENERATION, OBLIGATIONS)
        self.fence.admit(OPERATION, GENERATION, OBLIGATIONS)

    def test_exact_producer_is_terminated_and_waited_with_a_finite_bound(self):
        class Process:
            creation_time_100ns = 77
            def __init__(self):
                self.running = True
                self.waits = []
                self.terminated = False
                self.closed = False
            def wait(self, timeout_ms):
                self.waits.append(timeout_ms)
                return 0 if not self.running else 0x102
            def terminate(self):
                self.terminated = True
                self.running = False
                return True
            def close(self):
                self.closed = True

        process = Process()
        identity = {"pid": 4022, "creation_time_100ns": 77}
        self.assertTrue(_terminate_or_confirm_process_absent(identity,
            process_opener=lambda _pid: process, wait_timeout_ms=23))
        self.assertTrue(process.terminated)
        self.assertEqual(process.waits, [0, 23])
        self.assertTrue(process.closed)

    def test_live_process_with_unverifiable_or_mismatched_identity_is_not_terminated(self):
        class Process:
            creation_time_100ns = 78
            def __init__(self):
                self.terminated = False
                self.closed = False
            def wait(self, _timeout_ms):
                return 0x102
            def terminate(self):
                self.terminated = True
                return True
            def close(self):
                self.closed = True

        process = Process()
        self.assertTrue(_terminate_or_confirm_process_absent(
            {"pid": 4023, "creation_time_100ns": 77},
            process_opener=lambda _pid: process))
        self.assertFalse(process.terminated)
        self.assertTrue(process.closed)

    def test_process_absence_wait_times_out_without_claiming_success(self):
        class Process:
            creation_time_100ns = 79
            def wait(self, _timeout_ms):
                return 0x102
            def terminate(self):
                return True
            def close(self):
                pass

        self.assertFalse(_terminate_or_confirm_process_absent(
            {"pid": 4024, "creation_time_100ns": 79},
            process_opener=lambda _pid: Process(), wait_timeout_ms=10))

    def test_native_access_denial_is_not_misclassified_as_process_absence(self):
        def denied(_pid):
            raise PermissionError("access denied")
        with self.assertRaisesRegex(OSError, "could not be verified"):
            _terminate_or_confirm_process_absent(
                {"pid": 4025, "creation_time_100ns": 80},
                process_opener=denied)

    @unittest.skipUnless(os.name == "nt", "native named mutex requires Windows")
    def test_native_mutex_and_journal_block_a_separate_process(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Win32CustodyFence(directory, self.digest)
            first.admit(OPERATION, GENERATION, OBLIGATIONS)
            script = (
                "from runtime.cli_v1.win32_custody_fence import Win32CustodyFence, CustodyFenceError; "
                "import sys; f=Win32CustodyFence(sys.argv[1], sys.argv[2]); "
                "\ntry: f.admit('" + NEXT_OPERATION + "', '" + NEXT_GENERATION + "', ['key:VK_A'])"
                "\nexcept CustodyFenceError as e: print(str(e)); sys.exit(0)"
                "\nraise SystemExit('fresh process admission was not blocked')"
            )
            result = subprocess.run([sys.executable, "-c", script,
                directory, self.digest], text=True, capture_output=True,
                timeout=10, check=False)
            first.close()
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertIn("ORPHAN_RECOVERY_UNRESOLVED", result.stdout)


if __name__ == "__main__":
    unittest.main()
