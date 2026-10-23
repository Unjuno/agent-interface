import ctypes
import multiprocessing
import sys
import time
import unittest
from unittest.mock import Mock


class Process:
    pid = 4201
    sentinel = 0x123456


class FileTime(ctypes.Structure):
    _fields_ = [("low", ctypes.c_uint32), ("high", ctypes.c_uint32)]


def _identity_child():
    time.sleep(0.2)


class Win32ProcessIdentityTests(unittest.TestCase):
    def setUp(self):
        try:
            from runtime.guarded_win32_v1.win32_process_identity import (
                Win32ProcessIdentityReader,
            )
        except ModuleNotFoundError:
            self.fail("retained-handle Win32 process identity reader is missing")
        self.reader_type = Win32ProcessIdentityReader

    def test_reads_creation_time_from_the_exact_retained_process_handle(self):
        kernel32 = Mock()

        def get_times(handle, creation, _exit, _kernel, _user):
            self.assertEqual(handle, Process.sentinel)
            value = ctypes.cast(creation, ctypes.POINTER(FileTime)).contents
            value.low = 0x89ABCDEF
            value.high = 0x12345678
            return True

        kernel32.GetProcessTimes.side_effect = get_times
        reader = self.reader_type(kernel32=kernel32)

        result = reader(Process())

        self.assertEqual(result, {"pid": 4201,
            "creation_time_100ns": 0x1234567889ABCDEF})
        kernel32.GetProcessTimes.assert_called_once()
        kernel32.OpenProcess.assert_not_called()

    def test_refuses_missing_exact_process_handle(self):
        process = Process()
        process.sentinel = None
        reader = self.reader_type(kernel32=Mock())

        with self.assertRaisesRegex(ValueError, "retained process handle"):
            reader(process)

    def test_refuses_failed_or_zero_creation_time(self):
        for returns in (False, "zero"):
            with self.subTest(returns=returns):
                kernel32 = Mock()

                def get_times(_handle, creation, _exit, _kernel, _user):
                    if returns == "zero":
                        value = ctypes.cast(creation,
                            ctypes.POINTER(FileTime)).contents
                        value.low = 0
                        value.high = 0
                    return returns is not False

                kernel32.GetProcessTimes.side_effect = get_times
                reader = self.reader_type(kernel32=kernel32)
                with self.assertRaisesRegex(RuntimeError,
                                             "process creation time unavailable"):
                    reader(Process())

    @unittest.skipUnless(sys.platform == "win32", "requires native Windows process handles")
    def test_reads_creation_time_from_a_real_spawned_process_sentinel(self):
        context = multiprocessing.get_context("spawn")
        process = context.Process(target=_identity_child)
        process.start()
        try:
            identity = self.reader_type()(process)
            self.assertEqual(identity["pid"], process.pid)
            self.assertGreater(identity["creation_time_100ns"], 0)
        finally:
            process.join(2)
            if process.is_alive():
                process.terminate()
                process.join(2)
            process.close()


if __name__ == "__main__":
    unittest.main()
