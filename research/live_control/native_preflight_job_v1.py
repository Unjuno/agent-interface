"""Own a native schema preflight and its descendants on the Windows host."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import json
import math
import os
import secrets
from pathlib import Path
import subprocess
import sys
import threading
import time


RECEIPT = "windows-job.json"
START_RECORD = "windows-job-start.json"
LEASE_FILE = "windows-job-lease.txt"
LEASE_TIMEOUT = 3
SCHEMA = "native-preflight-windows-job-v1"
JOB_LIST = 0x0002000D
HANDLE_LIST = 0x00020002
KILL_ON_JOB_CLOSE = 0x00002000
JOB_KILL_EXIT_CODE = 0xE001F001
EXTENDED_STARTUPINFO_PRESENT = 0x00080000
STARTF_USESTDHANDLES = 0x00000100
WAIT_OBJECT_0 = 0
WAIT_TIMEOUT = 258
JOB_TIMEOUT = 75
CLEANUP_TIMEOUT = 5


class BasicLimit(ctypes.Structure):
    _fields_ = [("ProcessTimeLimit", ctypes.c_int64), ("JobTimeLimit", ctypes.c_int64),
                ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD)]


class ExtendedLimit(ctypes.Structure):
    _fields_ = [("BasicLimitInformation", BasicLimit), ("IoInfo", ctypes.c_uint64 * 6),
                ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]


class Accounting(ctypes.Structure):
    _fields_ = [("TotalUserTime", ctypes.c_int64), ("TotalKernelTime", ctypes.c_int64),
                ("PeriodUserTime", ctypes.c_int64), ("PeriodKernelTime", ctypes.c_int64),
                ("PageFaults", wintypes.DWORD), ("TotalProcesses", wintypes.DWORD),
                ("ActiveProcesses", wintypes.DWORD), ("TotalTerminatedProcesses", wintypes.DWORD)]


class JobProcessIds(ctypes.Structure):
    _fields_ = [("NumberOfAssignedProcesses", wintypes.DWORD), ("NumberOfProcessIdsInList", wintypes.DWORD),
                ("ProcessIdList", ctypes.c_size_t * 64)]


class StartupInfo(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("lpReserved", wintypes.LPWSTR),
                ("lpDesktop", wintypes.LPWSTR), ("lpTitle", wintypes.LPWSTR),
                *[(name, wintypes.DWORD) for name in (
                    "dwX", "dwY", "dwXSize", "dwYSize", "dwXCountChars", "dwYCountChars",
                    "dwFillAttribute", "dwFlags")],
                ("wShowWindow", wintypes.WORD), ("cbReserved2", wintypes.WORD),
                ("lpReserved2", ctypes.c_void_p), ("hStdInput", wintypes.HANDLE),
                ("hStdOutput", wintypes.HANDLE), ("hStdError", wintypes.HANDLE)]


class ExtendedStartupInfo(ctypes.Structure):
    _fields_ = [("StartupInfo", StartupInfo), ("AttributeList", ctypes.c_void_p)]


class ProcessInfo(ctypes.Structure):
    _fields_ = [("hProcess", wintypes.HANDLE), ("hThread", wintypes.HANDLE),
                ("dwProcessId", wintypes.DWORD), ("dwThreadId", wintypes.DWORD)]


def kernel():
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    handle, ptr, dword, size, boolean = (wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
                                        ctypes.c_size_t, wintypes.BOOL)
    signatures = {
        "CreateJobObjectW": (handle, [ptr, wintypes.LPCWSTR]),
        "SetInformationJobObject": (boolean, [handle, ctypes.c_int, ptr, dword]),
        "QueryInformationJobObject": (boolean, [handle, ctypes.c_int, ptr, dword, ptr]),
        "InitializeProcThreadAttributeList": (boolean, [ptr, dword, dword, ctypes.POINTER(size)]),
        "UpdateProcThreadAttribute": (boolean, [ptr, dword, size, ptr, size, ptr, ptr]),
        "DeleteProcThreadAttributeList": (None, [ptr]),
        "CreateProcessW": (boolean, [wintypes.LPCWSTR, wintypes.LPWSTR, ptr, ptr, boolean, dword,
                                    ptr, wintypes.LPCWSTR, ptr, ctypes.POINTER(ProcessInfo)]),
        "WaitForSingleObject": (dword, [handle, dword]),
        "GetExitCodeProcess": (boolean, [handle, ctypes.POINTER(dword)]),
        "OpenProcess": (handle, [dword, boolean, dword]),
        "IsProcessInJob": (boolean, [handle, handle, ctypes.POINTER(boolean)]),
        "TerminateJobObject": (boolean, [handle, wintypes.UINT]),
        "CloseHandle": (boolean, [handle]),
    }
    for name, (result, arguments) in signatures.items():
        function = getattr(api, name)
        function.restype, function.argtypes = result, arguments
    return api


def check(value):
    if not value:
        raise ctypes.WinError(ctypes.get_last_error())
    return value


def create_owned_process(api, job, argv, streams):
    import msvcrt

    standard_handles = (wintypes.HANDLE * 3)(*(msvcrt.get_osfhandle(f.fileno()) for f in streams))
    jobs = (wintypes.HANDLE * 1)(job)
    size = ctypes.c_size_t()
    api.InitializeProcThreadAttributeList(None, 2, 0, ctypes.byref(size))
    check(size.value)
    buffer = ctypes.create_string_buffer(size.value)
    attributes = ctypes.cast(buffer, ctypes.c_void_p)
    check(api.InitializeProcThreadAttributeList(attributes, 2, 0, ctypes.byref(size)))
    originals = []
    try:
        for handle in standard_handles:
            originals.append((handle, os.get_handle_inheritable(handle)))
            os.set_handle_inheritable(handle, True)
        for key, data in ((JOB_LIST, jobs), (HANDLE_LIST, standard_handles)):
            check(api.UpdateProcThreadAttribute(
                attributes, 0, key, ctypes.byref(data), ctypes.sizeof(data), None, None))
        info = ExtendedStartupInfo()
        info.StartupInfo.cb = ctypes.sizeof(info)
        info.StartupInfo.dwFlags = STARTF_USESTDHANDLES
        info.StartupInfo.hStdInput, info.StartupInfo.hStdOutput, info.StartupInfo.hStdError = standard_handles
        info.AttributeList = attributes
        process = ProcessInfo()
        command = ctypes.create_unicode_buffer(subprocess.list2cmdline(argv))
        check(api.CreateProcessW(argv[0], command, None, None, True,
                                 EXTENDED_STARTUPINFO_PRESENT | subprocess.CREATE_NO_WINDOW,
                                 None, None, ctypes.byref(info), ctypes.byref(process)))
        api.CloseHandle(process.hThread)
        return process.hProcess
    finally:
        api.DeleteProcThreadAttributeList(attributes)
        for handle, inheritable in originals:
            os.set_handle_inheritable(handle, inheritable)


def read_accounting(api, job):
    counts = Accounting()
    check(api.QueryInformationJobObject(job, 1, ctypes.byref(counts), ctypes.sizeof(counts), None))
    return counts


def wait_empty(api, job, deadline):
    counts = read_accounting(api, job)
    while counts.ActiveProcesses and time.monotonic() < deadline:
        time.sleep(.01)
        counts = read_accounting(api, job)
    return counts


def wait_milliseconds(deadline):
    return max(0, math.ceil((deadline - time.monotonic()) * 1000))


def terminate_and_wait(api, job):
    # Query the owned job only. Never send termination to a PID.
    ids = JobProcessIds()
    check(api.QueryInformationJobObject(job, 3, ctypes.byref(ids), ctypes.sizeof(ids), None))
    witnesses = []
    try:
        for pid in ids.ProcessIdList[:ids.NumberOfProcessIdsInList]:
            handle = api.OpenProcess(0x00101000, False, pid)  # synchronize and query
            if not handle:
                if ctypes.get_last_error() == 87:  # already exited
                    continue
                check(handle)
            belongs = wintypes.BOOL()
            try:
                check(api.IsProcessInJob(handle, job, ctypes.byref(belongs)))
            except BaseException:
                api.CloseHandle(handle)
                raise
            if belongs.value:
                witnesses.append(handle)
            else:
                api.CloseHandle(handle)
        check(api.TerminateJobObject(job, JOB_KILL_EXIT_CODE))
        deadline = time.monotonic() + CLEANUP_TIMEOUT
        states = [api.WaitForSingleObject(handle, wait_milliseconds(deadline)) for handle in witnesses]
        counts = wait_empty(api, job, deadline)
        return counts, all(state == WAIT_OBJECT_0 for state in states)
    finally:
        for handle in witnesses:
            api.CloseHandle(handle)


class LeaseWriter:
    """Publish a lease from the actual WSL caller, rather than its launcher process."""

    def __init__(self, root):
        self.path = root / LEASE_FILE
        self.nonce = secrets.token_hex(16)
        self.stop = threading.Event()
        self.writer = None

    def write(self, value):
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(f"{self.nonce}:{value}\n", encoding="ascii")
        temporary.replace(self.path)

    def heartbeat(self):
        counter = 0
        while not self.stop.wait(.25):
            counter += 1
            try:
                self.write(counter)
            except OSError:
                break

    def __enter__(self):
        self.write(0)
        self.writer = threading.Thread(target=self.heartbeat, daemon=True)
        self.writer.start()
        return self

    def __exit__(self, *_):
        self.stop.set()
        self.writer.join(timeout=1)


class LeaseReader:
    def __init__(self, root, nonce):
        self.path = root / LEASE_FILE
        self.nonce = nonce
        self.seen = time.monotonic()
        self.last = self.read()

    def read(self):
        try:
            prefix, value = self.path.read_text(encoding="ascii").strip().split(":", 1)
        except (OSError, ValueError):
            return None
        return int(value) if prefix == self.nonce and value.isdecimal() and len(value) <= 9 else None

    def await_owner(self):
        origin = self.last
        while time.monotonic() - self.seen < LEASE_TIMEOUT:
            value = self.read()
            observed = time.monotonic()
            if observed - self.seen >= LEASE_TIMEOUT:
                break
            if value is not None:
                if origin is None:
                    origin = value
                elif value > origin:
                    self.last, self.seen = value, observed
                    return
            time.sleep(.05)
        raise TimeoutError("WSL caller did not renew the initial Windows job lease")

    def lost(self):
        if time.monotonic() - self.seen >= LEASE_TIMEOUT:
            return True
        value = self.read()
        observed = time.monotonic()
        if observed - self.seen >= LEASE_TIMEOUT:
            return True
        if value is not None and (self.last is None or value > self.last):
            self.last, self.seen = value, observed
        return False


class LeaseMonitor:
    """Keep filesystem liveness checks off the Windows job deadline loop."""

    def __init__(self, lease, stop_requested=None):
        self.lease = lease
        self.stop_requested = stop_requested
        self.requested_stop = threading.Event()
        self.done = threading.Event()

    def watch(self):
        while not self.done.wait(.05):
            if self.stop_requested is not None and self.stop_requested():
                self.requested_stop.set()
                return
            if self.lease.lost():
                return

    def retired(self):
        return self.requested_stop.is_set() or time.monotonic() - self.lease.seen >= LEASE_TIMEOUT

    def __enter__(self):
        threading.Thread(target=self.watch, daemon=True).start()
        return self

    def __exit__(self, *_):
        self.done.set()


def run_owned(argv, stdout, stderr, *, timeout=JOB_TIMEOUT, owner_lost=None):
    with open(os.devnull, "rb") as stdin, stdout.open("xb") as out, stderr.open("xb") as err:
        return run_in_job(argv, (stdin, out, err), timeout=timeout, owner_lost=owner_lost)


def run_in_job(argv, streams, *, timeout, owner_lost=None):
    """Begin within an anonymous job and verify emptiness before reporting success."""
    deadline = time.monotonic() + timeout
    api = kernel()
    job = check(api.CreateJobObjectW(None, None))
    process = None
    try:
        limits = ExtendedLimit()
        limits.BasicLimitInformation.LimitFlags = KILL_ON_JOB_CLOSE
        check(api.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
        if owner_lost is not None and owner_lost():
            raise TimeoutError("WSL caller lease expired before Windows process creation")
        if time.monotonic() > deadline:
            raise TimeoutError("Windows job deadline expired before process creation")
        process = create_owned_process(api, job, argv, streams)
        reason = None
        while True:
            remaining = wait_milliseconds(deadline)
            wait = api.WaitForSingleObject(process, min(remaining, 100) if owner_lost else remaining)
            if wait not in (WAIT_OBJECT_0, WAIT_TIMEOUT):
                raise ctypes.WinError(ctypes.get_last_error())
            if time.monotonic() > deadline or wait == WAIT_TIMEOUT and remaining == 0:
                reason = "TIMED_OUT"
                break
            if wait == WAIT_OBJECT_0:
                break
            if owner_lost is not None and owner_lost():
                if api.WaitForSingleObject(process, 0) != WAIT_OBJECT_0:
                    reason = "OWNER_LOST"
                break
        counts = wait_empty(api, job, min(deadline, time.monotonic() + .15))
        status = reason or ("DESCENDANTS_ACTIVE" if counts.ActiveProcesses else "COMPLETED")
        signalled = True
        termination_requested = counts.ActiveProcesses > 0
        if termination_requested:
            counts, signalled = terminate_and_wait(api, job)
        job_empty = counts.ActiveProcesses == 0 and signalled
        exit_code = wintypes.DWORD()
        if not job_empty:
            status, code = "CLEANUP_UNVERIFIED", None
        else:
            check(api.GetExitCodeProcess(process, ctypes.byref(exit_code)))
            code = exit_code.value
        if status == "COMPLETED":
            caller_lost = owner_lost is not None and owner_lost()
            if time.monotonic() > deadline:
                status = "TIMED_OUT"
            elif caller_lost:
                status = "OWNER_LOST"
        return {"schema": SCHEMA, "ownership": "create-process-job-list",
                "status": status, "exit_code": code, "job_empty": job_empty,
                "termination_requested": termination_requested,
                "active_processes": counts.ActiveProcesses, "total_processes": counts.TotalProcesses}
    finally:
        # Closing the private last job handle is also the fallback on interruption.
        api.CloseHandle(job)
        if process is not None:
            api.CloseHandle(process)


def valid_hex(value, length):
    return type(value) is str and len(value) == length and all(ch in "0123456789abcdef" for ch in value)


def completed_receipt(value, returncode, *, run_nonce, owner_sha256, minimum_processes=2):
    return (type(value) is dict and value.get("schema") == SCHEMA
            and valid_hex(run_nonce, 32) and valid_hex(owner_sha256, 64)
            and value.get("run_nonce") == run_nonce and value.get("owner_sha256") == owner_sha256
            and value.get("ownership") == "create-process-job-list"
            and value.get("status") == "COMPLETED" and value.get("job_empty") is True
            and type(value.get("active_processes")) is int and value["active_processes"] == 0
            and type(value.get("total_processes")) is int and value["total_processes"] >= minimum_processes
            and type(value.get("exit_code")) is int and value["exit_code"] == returncode)


def main(argv):
    destination, nonce, runner, *request = argv
    if Path(runner).resolve() != Path(__file__).with_name("target_handle_model_runner_v2.py").resolve():
        raise ValueError("the built-in native preflight runner is required")
    if len(request) != 9 or request[0] != "--native-codex-exe":
        raise ValueError("the native preflight request is required")
    root = Path(destination)
    lease = LeaseReader(root, nonce)
    lease.await_owner()
    with LeaseMonitor(lease) as monitor:
        result = run_owned([sys.executable, "-B", runner, *request],
                           root / "windows-runner-stdout.txt", root / "windows-runner-stderr.txt",
                           owner_lost=monitor.retired)
    result.update(run_nonce=nonce, owner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with (root / RECEIPT).open("x", encoding="utf-8", newline="\n") as receipt:
        json.dump(result, receipt, indent=2)
        receipt.write("\n")
        receipt.flush()
        os.fsync(receipt.fileno())
    return int(result["exit_code"] or 0) if result["status"] == "COMPLETED" else 124


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
