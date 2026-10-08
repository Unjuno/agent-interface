"""Experimental Windows Popen-compatible factory owning a Job Object tree."""
import ctypes
import subprocess
from ctypes import wintypes

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
CREATE_SUSPENDED = 0x00000004
TH32CS_SNAPTHREAD = 0x00000004
THREAD_SUSPEND_RESUME = 0x0002
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

class IO_COUNTERS(ctypes.Structure):
    _fields_ = [(name, ctypes.c_ulonglong) for name in (
        "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
        "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

class BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]

class EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", BASIC_LIMIT_INFORMATION),
        ("IoInfo", IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]

class THREADENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
        ("th32ThreadID", wintypes.DWORD), ("th32OwnerProcessID", wintypes.DWORD),
        ("tpBasePri", wintypes.LONG), ("tpDeltaPri", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
    ]

kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
kernel32.CreateJobObjectW.restype = wintypes.HANDLE
kernel32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
kernel32.SetInformationJobObject.restype = wintypes.BOOL
kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
kernel32.Thread32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(THREADENTRY32)]
kernel32.Thread32First.restype = wintypes.BOOL
kernel32.Thread32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(THREADENTRY32)]
kernel32.Thread32Next.restype = wintypes.BOOL
kernel32.OpenThread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenThread.restype = wintypes.HANDLE
kernel32.ResumeThread.argtypes = [wintypes.HANDLE]
kernel32.ResumeThread.restype = wintypes.DWORD
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL


def _winerror(label):
    return OSError(ctypes.get_last_error(), label)


def _resume_only_primary_thread(pid):
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
    if snapshot == INVALID_HANDLE_VALUE:
        raise _winerror("CreateToolhelp32Snapshot")
    matches = []
    try:
        entry = THREADENTRY32()
        entry.dwSize = ctypes.sizeof(entry)
        ok = kernel32.Thread32First(snapshot, ctypes.byref(entry))
        while ok:
            if entry.th32OwnerProcessID == pid:
                matches.append(entry.th32ThreadID)
            ok = kernel32.Thread32Next(snapshot, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snapshot)
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one suspended primary thread, found {len(matches)}")
    thread = kernel32.OpenThread(THREAD_SUSPEND_RESUME, False, matches[0])
    if not thread:
        raise _winerror("OpenThread")
    try:
        prior = kernel32.ResumeThread(thread)
        if prior == 0xFFFFFFFF:
            raise _winerror("ResumeThread")
        if prior != 1:
            raise RuntimeError(f"expected one suspended start count, got {prior}")
    finally:
        kernel32.CloseHandle(thread)


class JobOwnedPopen:
    """Popen delegate; close the private kill-on-close job after parent exit."""
    def __init__(self, process, job_handle):
        self._process = process
        self._job_handle = job_handle

    def __getattr__(self, name):
        return getattr(self._process, name)

    def _close_job(self):
        if self._job_handle:
            handle, self._job_handle = self._job_handle, None
            if not kernel32.CloseHandle(handle):
                raise _winerror("CloseHandle(job)")

    def poll(self):
        code = self._process.poll()
        if code is not None:
            self._close_job()
        return code

    def wait(self, timeout=None):
        code = self._process.wait(timeout=timeout)
        self._close_job()
        return code

    def terminate(self):
        return self._process.terminate()

    def kill(self):
        return self._process.kill()

    def close_job(self):
        self._close_job()


def windows_job_popen_factory(command, *args, **kwargs):
    if kwargs.get("creationflags", 0) & CREATE_SUSPENDED:
        raise ValueError("factory owns CREATE_SUSPENDED")
    kwargs["creationflags"] = kwargs.get("creationflags", 0) | CREATE_SUSPENDED
    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        raise _winerror("CreateJobObjectW")
    info = EXTENDED_LIMIT_INFORMATION()
    info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    if not kernel32.SetInformationJobObject(job, JOB_OBJECT_EXTENDED_LIMIT_INFORMATION, ctypes.byref(info), ctypes.sizeof(info)):
        error = _winerror("SetInformationJobObject")
        kernel32.CloseHandle(job)
        raise error
    process = None
    try:
        process = subprocess.Popen(command, *args, **kwargs)
        if not kernel32.AssignProcessToJobObject(job, process._handle):
            raise _winerror("AssignProcessToJobObject")
        _resume_only_primary_thread(process.pid)
        return JobOwnedPopen(process, job)
    except BaseException:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()
        kernel32.CloseHandle(job)
        raise
