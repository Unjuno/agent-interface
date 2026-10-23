"""Process identity reads through a retained multiprocessing process handle."""
from __future__ import annotations

import ctypes
import sys


class _FILETIME(ctypes.Structure):
    _fields_ = [("low", ctypes.c_uint32), ("high", ctypes.c_uint32)]


class Win32ProcessIdentityReader:
    """Return PID and creation time for the exact retained process object.

    ``Process.sentinel`` is the waitable handle owned by multiprocessing. It
    identifies the launched process directly, avoiding a PID-based reopen that
    could bind to a different process after PID reuse. The caller owns the
    Process object and must not close it during this query.
    """

    def __init__(self, *, kernel32=None):
        if kernel32 is None:
            if sys.platform != "win32":
                raise OSError("Win32 process identity requires Windows")
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._kernel32 = kernel32
        try:
            self._kernel32.GetProcessTimes.argtypes = [
                ctypes.c_void_p, ctypes.POINTER(_FILETIME),
                ctypes.POINTER(_FILETIME), ctypes.POINTER(_FILETIME),
                ctypes.POINTER(_FILETIME),
            ]
            self._kernel32.GetProcessTimes.restype = ctypes.c_int
        except (AttributeError, TypeError):
            # Injectable test doubles need not expose ctypes function metadata.
            pass

    def __call__(self, process):
        pid = getattr(process, "pid", None)
        handle = getattr(process, "sentinel", None)
        if (type(pid) is not int or pid <= 0
                or type(handle) is not int or handle <= 0):
            raise ValueError("retained process handle and positive PID required")
        creation, exited, kernel, user = _FILETIME(), _FILETIME(), _FILETIME(), _FILETIME()
        try:
            succeeded = self._kernel32.GetProcessTimes(
                handle, ctypes.byref(creation), ctypes.byref(exited),
                ctypes.byref(kernel), ctypes.byref(user))
        except Exception as error:
            raise RuntimeError("process creation time unavailable") from error
        if not succeeded:
            raise RuntimeError("process creation time unavailable")
        creation_time_100ns = ((int(creation.high) << 32) | int(creation.low))
        if creation_time_100ns <= 0:
            raise RuntimeError("process creation time unavailable")
        return {"pid": pid, "creation_time_100ns": creation_time_100ns}
