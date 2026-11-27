import hashlib
import json
import unittest
from unittest.mock import Mock, patch

from runtime.backends.win32_v1.backend import (
    Win32Backend, Win32BackendError,
)


class ReusedHandleUser32:
    def __init__(self, hwnd):
        self.windows = {hwnd}
        self.properties = {hwnd: {}}

    def IsWindow(self, hwnd):
        return hwnd in self.windows

    def GetPropW(self, hwnd, name):
        return self.properties.get(hwnd, {}).get(name, 0)

    def SetPropW(self, hwnd, name, value):
        if hwnd not in self.windows:
            return False
        self.properties[hwnd][name] = int(getattr(value, "value", value))
        return True

    def RemovePropW(self, hwnd, name):
        return self.properties.get(hwnd, {}).pop(name, 0)

    def recycle_numeric_handle(self, hwnd):
        self.windows.remove(hwnd)
        self.properties.pop(hwnd)
        self.windows.add(hwnd)
        self.properties[hwnd] = {}

    def add_window(self, hwnd):
        self.windows.add(hwnd)
        self.properties[hwnd] = {}


class ProcessIdentityTests(unittest.TestCase):
    def backend(self):
        backend = object.__new__(Win32Backend)
        backend.targets = {'fixture': 42}
        backend.user32 = Mock()
        backend.kernel32 = Mock()
        backend.user32.IsWindow.return_value = True
        backend.user32.GetPropW.return_value = 0
        def set_property(hwnd, name, value):
            backend.user32.GetPropW.return_value = value.value
            return True
        backend.user32.SetPropW.side_effect = set_property
        def remove_property(hwnd, name):
            value = backend.user32.GetPropW.return_value
            backend.user32.GetPropW.return_value = 0
            return value
        backend.user32.RemovePropW.side_effect = remove_property
        return backend

    @staticmethod
    def set_pid(out, value, thread_id=101):
        out._obj.value = value
        return thread_id

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
        with patch('runtime.backends.win32_v1.backend.secrets.randbits', return_value=12345):
            expected = hashlib.sha256(json.dumps(
                [42, 101, 51, 0x9ABCDEF012345678, 12345], separators=(',', ':')
            ).encode('ascii')).hexdigest()
            self.assertEqual(backend.target_generation('fixture'), expected)
        backend.kernel32.CloseHandle.assert_called_once_with(99)

    def test_target_generation_changes_when_hwnd_changes_with_same_process(self):
        backend = self.backend()
        backend._window_owner_identity_for_hwnd = Mock(return_value={
            'pid': 51, 'creation_time_100ns': 7001,
            'window_thread_id': 101})
        first = backend.target_generation('fixture')
        backend.targets['fixture'] = 43
        second = backend.target_generation('fixture')

        self.assertNotEqual(first, second)
        self.assertEqual(backend._window_owner_identity_for_hwnd.call_count, 2)

    def test_target_generation_refuses_window_thread_change(self):
        backend = self.backend()
        backend._window_owner_identity_for_hwnd = Mock(side_effect=[
            {'pid': 51, 'creation_time_100ns': 7001, 'window_thread_id': 101},
            {'pid': 51, 'creation_time_100ns': 7001, 'window_thread_id': 102},
        ])

        backend.target_generation('fixture')
        with self.assertRaisesRegex(Win32BackendError, 'incarnation'):
            backend.target_generation('fixture')

    def test_target_generation_refuses_reused_numeric_hwnd_after_window_incarnation_changes(self):
        backend = self.backend()
        backend.user32 = ReusedHandleUser32(42)
        backend._window_owner_identity_for_hwnd = Mock(return_value={
            'pid': 51, 'creation_time_100ns': 7001,
            'window_thread_id': 101})

        backend.target_generation('fixture')
        backend.user32.recycle_numeric_handle(42)

        with self.assertRaisesRegex(Win32BackendError, 'incarnation'):
            backend.target_generation('fixture')

    def test_target_generation_fails_closed_when_uipi_blocks_property_set(self):
        backend = self.backend()
        backend._window_owner_identity_for_hwnd = Mock(return_value={
            'pid': 51, 'creation_time_100ns': 7001,
            'window_thread_id': 101})
        backend.user32.SetPropW.side_effect = None
        backend.user32.SetPropW.return_value = False

        with self.assertRaisesRegex(Win32BackendError, 'property set failed'):
            backend.target_generation('fixture')

    def test_close_retains_owned_property_until_the_window_is_destroyed(self):
        backend = self.backend()
        backend._window_owner_identity_for_hwnd = Mock(return_value={
            'pid': 51, 'creation_time_100ns': 7001,
            'window_thread_id': 101})
        with patch('runtime.backends.win32_v1.backend.secrets.randbits', return_value=12345):
            backend.target_generation('fixture')
        report = backend.close()
        self.assertEqual(report['status'], 'closed')
        self.assertEqual(report['property_cleanup'][0]['status'],
                         'retained_until_window_destroyed')
        self.assertEqual(backend.user32.GetPropW.return_value, 12345)
        self.assertIs(backend.close(), report)

    def test_close_retains_a_borrowed_property_for_other_backends(self):
        backend = self.backend()
        backend.user32.GetPropW.return_value = 98765
        backend._window_owner_identity_for_hwnd = Mock(return_value={
            'pid': 51, 'creation_time_100ns': 7001,
            'window_thread_id': 101})

        backend.target_generation('fixture')
        report = backend.close()

        self.assertEqual(report['status'], 'closed')
        self.assertEqual(report['property_cleanup'][0]['status'],
                         'retained_until_window_destroyed')
        backend.user32.RemovePropW.assert_not_called()

    def test_process_identity_query_refuses_owner_thread_change(self):
        backend = self.backend()
        thread_ids = iter([101, 102])
        backend.user32.GetWindowThreadProcessId.side_effect = (
            lambda hwnd, out: self.set_pid(out, 51, next(thread_ids)))
        backend.kernel32.OpenProcess.return_value = 99
        backend.kernel32.GetProcessTimes.return_value = 1

        with self.assertRaisesRegex(Win32BackendError, 'owner changed'):
            backend.process_identity('fixture')
        backend.kernel32.CloseHandle.assert_called_once_with(99)

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
