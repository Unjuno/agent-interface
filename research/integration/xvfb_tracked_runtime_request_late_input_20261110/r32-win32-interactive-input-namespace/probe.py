#!/usr/bin/env python3
"""Read-only current Windows interactive input namespace probe."""
import ctypes
import hashlib
import json
import os
import time
from ctypes import wintypes


UOI_NAME = 2
UOI_IO = 6
DESKTOP_READOBJECTS = 0x0001
TOKEN_QUERY = 0x0008
TOKEN_STATISTICS = 10


class LUID(ctypes.Structure):
    _fields_ = [('LowPart', wintypes.DWORD), ('HighPart', wintypes.LONG)]


class TOKEN_STATISTICS_STRUCT(ctypes.Structure):
    _fields_ = [
        ('TokenId', LUID),
        ('AuthenticationId', LUID),
        ('ExpirationTime', ctypes.c_longlong),
        ('TokenType', wintypes.DWORD),
        ('ImpersonationLevel', wintypes.DWORD),
        ('DynamicCharged', wintypes.DWORD),
        ('DynamicAvailable', wintypes.DWORD),
        ('GroupCount', wintypes.DWORD),
        ('PrivilegeCount', wintypes.DWORD),
        ('ModifiedId', LUID),
    ]


def checked(ok, operation):
    if not ok:
        raise ctypes.WinError(ctypes.get_last_error(), operation)


def object_name(user32, handle):
    needed = wintypes.DWORD()
    user32.GetUserObjectInformationW(handle, UOI_NAME, None, 0,
                                     ctypes.byref(needed))
    if not needed.value:
        raise ctypes.WinError(ctypes.get_last_error(), 'GetUserObjectInformationW(UOI_NAME)')
    buffer = ctypes.create_unicode_buffer(
        needed.value // ctypes.sizeof(wintypes.WCHAR) + 2)
    checked(user32.GetUserObjectInformationW(handle, UOI_NAME, buffer,
        ctypes.sizeof(buffer), ctypes.byref(needed)),
        'GetUserObjectInformationW(UOI_NAME)')
    return buffer.value


def token_authentication_id(advapi32, kernel32):
    token = wintypes.HANDLE()
    checked(advapi32.OpenProcessToken(kernel32.GetCurrentProcess(), TOKEN_QUERY,
        ctypes.byref(token)), 'OpenProcessToken')
    try:
        needed = wintypes.DWORD()
        advapi32.GetTokenInformation(token, TOKEN_STATISTICS, None, 0,
                                     ctypes.byref(needed))
        if needed.value < ctypes.sizeof(TOKEN_STATISTICS_STRUCT):
            raise RuntimeError('TOKEN_STATISTICS size unavailable')
        storage = ctypes.create_string_buffer(needed.value)
        checked(advapi32.GetTokenInformation(token, TOKEN_STATISTICS,
            storage, needed.value, ctypes.byref(needed)), 'GetTokenInformation')
        stats = ctypes.cast(storage,
            ctypes.POINTER(TOKEN_STATISTICS_STRUCT)).contents
        luid = ((int(stats.AuthenticationId.HighPart) & 0xFFFFFFFF) << 32) \
            | int(stats.AuthenticationId.LowPart)
        return f'{luid:016x}'
    finally:
        kernel32.CloseHandle(token)


def main():
    if os.name != 'nt':
        raise OSError('Windows host required')
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    advapi32 = ctypes.WinDLL('advapi32', use_last_error=True)
    user32.GetProcessWindowStation.restype = wintypes.HANDLE
    user32.GetThreadDesktop.argtypes = [wintypes.DWORD]
    user32.GetThreadDesktop.restype = wintypes.HANDLE
    user32.OpenInputDesktop.argtypes = [wintypes.DWORD, wintypes.BOOL,
                                       wintypes.DWORD]
    user32.OpenInputDesktop.restype = wintypes.HANDLE
    user32.GetUserObjectInformationW.argtypes = [wintypes.HANDLE,
        wintypes.INT, wintypes.LPVOID, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD)]
    user32.GetUserObjectInformationW.restype = wintypes.BOOL
    user32.CloseDesktop.argtypes = [wintypes.HANDLE]
    user32.CloseDesktop.restype = wintypes.BOOL
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD
    kernel32.GetCurrentProcessId.restype = wintypes.DWORD
    kernel32.ProcessIdToSessionId.argtypes = [wintypes.DWORD,
                                              ctypes.POINTER(wintypes.DWORD)]
    kernel32.ProcessIdToSessionId.restype = wintypes.BOOL

    process_id = int(kernel32.GetCurrentProcessId())
    session_id = wintypes.DWORD()
    checked(kernel32.ProcessIdToSessionId(process_id,
        ctypes.byref(session_id)), 'ProcessIdToSessionId')
    station = user32.GetProcessWindowStation()
    if not station:
        raise ctypes.WinError(ctypes.get_last_error(), 'GetProcessWindowStation')
    station_name = object_name(user32, station)
    thread_desktop = user32.GetThreadDesktop(kernel32.GetCurrentThreadId())
    if not thread_desktop:
        raise ctypes.WinError(ctypes.get_last_error(), 'GetThreadDesktop')
    thread_desktop_name = object_name(user32, thread_desktop)
    input_desktop = user32.OpenInputDesktop(0, False, DESKTOP_READOBJECTS)
    if not input_desktop:
        raise ctypes.WinError(ctypes.get_last_error(), 'OpenInputDesktop(READOBJECTS)')
    try:
        input_desktop_name = object_name(user32, input_desktop)
        input_flag = wintypes.DWORD()
        needed = wintypes.DWORD()
        checked(user32.GetUserObjectInformationW(input_desktop, UOI_IO,
            ctypes.byref(input_flag), ctypes.sizeof(input_flag),
            ctypes.byref(needed)), 'GetUserObjectInformationW(UOI_IO)')
        logon_id = token_authentication_id(advapi32, kernel32)
        namespace = {
            'session_id': int(session_id.value),
            'authentication_id': logon_id,
            'window_station': station_name,
        }
        namespace_hash = hashlib.sha256(json.dumps(namespace, sort_keys=True,
            separators=(',', ':')).encode('utf-8')).hexdigest()
        row = {
            'schema': 'agent-interface/win32-interactive-input-namespace-r32-v1',
            'status': 'observed',
            'observed_monotonic_ns': time.monotonic_ns(),
            'scope': 'read-only OS namespace query; no window input or app launch',
            'process_id': process_id,
            'session_id': int(session_id.value),
            'logon_authentication_id_sha256': hashlib.sha256(
                logon_id.encode('ascii')).hexdigest(),
            'process_window_station': station_name,
            'current_thread_desktop': thread_desktop_name,
            'active_input_desktop': input_desktop_name,
            'active_input_desktop_flag': bool(input_flag.value),
            'current_thread_matches_active_input_desktop': (
                thread_desktop_name == input_desktop_name),
            'input_namespace_sha256': namespace_hash,
            'namespace_fields': ['session_id',
                'logon_authentication_id (SHA-256 only)', 'window_station name'],
            'limitations': [
                'one observation on one current logon; no cross-session collision test',
                'does not identify an X11 server reached through a proxy',
                'does not prove late-input horizon, release, or task effect',
            ],
        }
        print(json.dumps(row, sort_keys=True, indent=2))
    finally:
        user32.CloseDesktop(input_desktop)


if __name__ == '__main__':
    main()
