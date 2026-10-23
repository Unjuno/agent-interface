import hashlib
import json
import unittest
from unittest.mock import Mock

from runtime.backends.win32_v1.backend import (
    Win32Backend, Win32BackendError,
)


class ProcessIdentityTests(unittest.TestCase):
    def backend(self):
        backend = object.__new__(Win32Backend)
        backend.targets = {'fixture': 42}
        backend.user32 = Mock()
        backend.kernel32 = Mock()
        backend.user32.IsWindow.return_value = True
        return backend

    @staticmethod
    def set_pid(out, value):
        out._obj.value = value
        return 1

    def test_returns_owner_pid_and_process_creation_time(self):
        backend = self.backend()
        pids = iter([51, 51])
        backend.user32.GetWindowThreadProcessId.side_effect = (
            lambda hwnd, out: self.set_pid(out, next(pids)))
        backend.kernel32.OpenProcess.return_value = 99

        def process_times(handle, creation, exited, kernel, user):
            creation._obj.dwLowDateTime = 0x12345678
            creation._obj.dwHighDateTime = 0x9ABCDEF0
            return 1

        backend.kernel32.GetProcessTimes.side_effect = process_times
        identity = backend.process_identity('fixture')

        self.assertEqual(identity, {
            'pid': 51,
            'creation_time_100ns': 0x9ABCDEF012345678,
        })
        backend.kernel32.OpenProcess.assert_called_once_with(0x1000, False, 51)
        backend.kernel32.CloseHandle.assert_called_once_with(99)

    def test_target_generation_binds_hwnd_and_process_creation_identity(self):
        backend = self.backend()
        pids = iter([51, 51])
        backend.user32.GetWindowThreadProcessId.side_effect = (
            lambda hwnd, out: self.set_pid(out, next(pids)))
        backend.kernel32.OpenProcess.return_value = 99

        def process_times(handle, creation, exited, kernel, user):
            creation._obj.dwLowDateTime = 0x12345678
            creation._obj.dwHighDateTime = 0x9ABCDEF0
            return 1

        backend.kernel32.GetProcessTimes.side_effect = process_times
        expected = hashlib.sha256(json.dumps(
            [42, 51, 0x9ABCDEF012345678], separators=(',', ':')
        ).encode('ascii')).hexdigest()

        self.assertEqual(backend.target_generation('fixture'), expected)
        backend.kernel32.CloseHandle.assert_called_once_with(99)

    def test_target_generation_changes_when_hwnd_changes_with_same_process(self):
        backend = self.backend()
        backend.process_identity = Mock(return_value={
            'pid': 51, 'creation_time_100ns': 7001})
        first = backend.target_generation('fixture')
        backend.targets['fixture'] = 43
        second = backend.target_generation('fixture')

        self.assertNotEqual(first, second)
        self.assertEqual(backend.process_identity.call_count, 2)

    def test_owner_change_during_identity_query_fails_closed_and_closes_handle(self):
        backend = self.backend()
        pids = iter([51, 52])
        backend.user32.GetWindowThreadProcessId.side_effect = (
            lambda hwnd, out: self.set_pid(out, next(pids)))
        backend.kernel32.OpenProcess.return_value = 99
        backend.kernel32.GetProcessTimes.return_value = 1

        with self.assertRaisesRegex(Win32BackendError, 'owner changed'):
            backend.process_identity('fixture')
        backend.kernel32.CloseHandle.assert_called_once_with(99)

    def test_process_query_failure_fails_closed_and_closes_handle(self):
        backend = self.backend()
        backend.user32.GetWindowThreadProcessId.side_effect = (
            lambda hwnd, out: self.set_pid(out, 51))
        backend.kernel32.OpenProcess.return_value = 99
        backend.kernel32.GetProcessTimes.return_value = 0

        with self.assertRaisesRegex(Win32BackendError, 'GetProcessTimes'):
            backend.process_identity('fixture')
        backend.kernel32.CloseHandle.assert_called_once_with(99)


if __name__ == '__main__':
    unittest.main()
