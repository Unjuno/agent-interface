#!/usr/bin/env python3
"""Check same-logon namespace stability and Win32 mutex custody semantics."""
import ctypes
import json
import subprocess
import sys
import time
import uuid
from ctypes import wintypes
from pathlib import Path


SYNCHRONIZE = 0x00100000
MUTEX_MODIFY_STATE = 0x0001
WAIT_OBJECT_0 = 0x00000000
WAIT_ABANDONED = 0x00000080
WAIT_TIMEOUT = 0x00000102


def configure_kernel32():
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL,
                                      wintypes.LPCWSTR]
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    kernel32.OpenMutexW.argtypes = [wintypes.DWORD, wintypes.BOOL,
                                    wintypes.LPCWSTR]
    kernel32.OpenMutexW.restype = wintypes.HANDLE
    kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    kernel32.ReleaseMutex.argtypes = [wintypes.HANDLE]
    kernel32.ReleaseMutex.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    return kernel32


def child_wait(name, timeout_ms):
    kernel32 = configure_kernel32()
    handle = kernel32.OpenMutexW(SYNCHRONIZE | MUTEX_MODIFY_STATE,
                                  False, name)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error(), 'OpenMutexW')
    try:
        result = int(kernel32.WaitForSingleObject(handle, timeout_ms))
        row = {'wait_result': result,
               'wait_name': ('object' if result == WAIT_OBJECT_0 else
                             'abandoned' if result == WAIT_ABANDONED else
                             'timeout' if result == WAIT_TIMEOUT else 'other')}
        if result in (WAIT_OBJECT_0, WAIT_ABANDONED):
            row['released'] = bool(kernel32.ReleaseMutex(handle))
        print(json.dumps(row, sort_keys=True), flush=True)
        return 0 if result in (WAIT_OBJECT_0, WAIT_ABANDONED, WAIT_TIMEOUT) else 2
    finally:
        kernel32.CloseHandle(handle)


def child_acquire_then_exit(name):
    kernel32 = configure_kernel32()
    handle = kernel32.OpenMutexW(SYNCHRONIZE | MUTEX_MODIFY_STATE,
                                  False, name)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error(), 'OpenMutexW')
    result = int(kernel32.WaitForSingleObject(handle, 3000))
    print(json.dumps({'wait_result': result,
        'wait_name': 'object' if result == WAIT_OBJECT_0 else 'other'},
        sort_keys=True), flush=True)
    # Deliberately exit while owning the mutex. Windows should mark it
    # abandoned; the parent keeps another handle open during this check.
    return 0 if result == WAIT_OBJECT_0 else 2


def run_child(*args):
    completed = subprocess.run([sys.executable, str(Path(__file__).resolve()),
        *args], capture_output=True, text=True, timeout=8)
    if completed.returncode != 0:
        raise RuntimeError(f'child failed: rc={completed.returncode} '
                           f'stdout={completed.stdout!r} stderr={completed.stderr!r}')
    rows = [json.loads(line) for line in completed.stdout.splitlines() if line]
    if len(rows) != 1:
        raise RuntimeError(f'child output malformed: {completed.stdout!r}')
    return rows[0]


def namespace_observation(script):
    completed = subprocess.run([sys.executable, str(script)], capture_output=True,
                               text=True, timeout=8)
    if completed.returncode != 0:
        raise RuntimeError(f'namespace probe failed: {completed.stderr}')
    return json.loads(completed.stdout)


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == 'wait':
            raise SystemExit(child_wait(sys.argv[2], int(sys.argv[3])))
        if sys.argv[1] == 'acquire-exit':
            raise SystemExit(child_acquire_then_exit(sys.argv[2]))
        raise SystemExit('unknown child mode')

    probe = Path(__file__).resolve().parents[1] / \
        'r33-win32-interactive-input-namespace-handle-types' / 'probe.py'
    first = namespace_observation(probe)
    second = namespace_observation(probe)
    if (first.get('status') != 'observed'
            or second.get('status') != 'observed'
            or first.get('input_namespace_sha256')
                != second.get('input_namespace_sha256')):
        raise RuntimeError('same-logon namespace key did not match across processes')
    key = first['input_namespace_sha256']
    prefix = 'Local\\UnjunoAgentInterface-R34-'
    kernel32 = configure_kernel32()
    trace = {'first_snapshot': first, 'second_snapshot': second,
             'namespace_key_equal_across_processes': True}

    held_name = prefix + uuid.uuid4().hex
    held = kernel32.CreateMutexW(None, True, held_name)
    if not held:
        raise ctypes.WinError(ctypes.get_last_error(), 'CreateMutexW(held)')
    try:
        trace['contender_while_held'] = run_child('wait', held_name, '150')
        if trace['contender_while_held']['wait_name'] != 'timeout':
            raise RuntimeError('second process unexpectedly entered owned mutex')
        if not kernel32.ReleaseMutex(held):
            raise ctypes.WinError(ctypes.get_last_error(), 'ReleaseMutex')
        trace['contender_after_release'] = run_child('wait', held_name, '1000')
        if trace['contender_after_release']['wait_name'] != 'object':
            raise RuntimeError('second process failed to enter released mutex')
    finally:
        kernel32.CloseHandle(held)

    abandoned_name = prefix + uuid.uuid4().hex
    abandoned = kernel32.CreateMutexW(None, False, abandoned_name)
    if not abandoned:
        raise ctypes.WinError(ctypes.get_last_error(), 'CreateMutexW(abandoned)')
    try:
        trace['abandoning_child'] = run_child('acquire-exit', abandoned_name)
        result = int(kernel32.WaitForSingleObject(abandoned, 0))
        trace['parent_after_child_exit'] = {
            'wait_result': result,
            'wait_name': ('abandoned' if result == WAIT_ABANDONED else
                          'object' if result == WAIT_OBJECT_0 else 'other'),
        }
        if result != WAIT_ABANDONED:
            raise RuntimeError('child process exit did not yield WAIT_ABANDONED')
        trace['parent_after_child_exit']['released'] = bool(
            kernel32.ReleaseMutex(abandoned))
    finally:
        kernel32.CloseHandle(abandoned)

    trace.update({
        'schema': 'agent-interface/win32-cross-process-mutex-r34-v1',
        'namespace_key_sha256': key,
        'mutex_scope': 'Local namespace; ephemeral random names; no persistent state',
        'observed_monotonic_ns': time.monotonic_ns(),
        'scope': 'same-user same-session process coordination only; no desktop input',
        'limitation': 'Mutex exclusion/abandonment does not itself preserve UNKNOWN custody; a durable journal is still required.',
    })
    print(json.dumps(trace, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
