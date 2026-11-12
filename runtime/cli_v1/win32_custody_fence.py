"""Durable per-logon admission fence for supervised Win32 input custody.

The fence stores the current unresolved action, its target-generation binding,
and generations retired by orphan recovery. The native mutex serializes state
transitions between processes; the journal is atomically replaced while that
mutex is held.
"""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import uuid


_OPERATION_ID = re.compile(r"^[0-9a-f]{32}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SCHEMA = "win32-custody-fence-v1"
_MAX_STATE_BYTES = 65536
_MAX_FENCED_GENERATIONS = 512
_MUTEX_WAIT_MS = 1000
_PROCESS_WAIT_MS = 1000
_CUSTODY_PHASE_ORDER = {"admitted": 0, "starting": 1, "running": 2,
                        "cancel_pending": 3, "recovery_pending": 4,
                        "unknown": 5}
_PRODUCER_GATE_ORDER = {"closed": 0, "identity_verified": 1,
                        "authorization_attempted": 2, "authorized": 3}
_DACL_SECURITY_INFORMATION = 0x00000004
_PROTECTED_DACL_SECURITY_INFORMATION = 0x80000000
_WRITE_DAC = 0x00040000


class _WindowsCustodyAcl:
    """Apply a protected DACL granting custody access to user, SYSTEM and admins."""

    def __init__(self):
        if os.name != "nt":
            raise OSError("the native custody ACL requires Windows")
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
        self._kernel32.GetCurrentProcess.restype = ctypes.c_void_p
        self._kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        self._kernel32.LocalFree.restype = ctypes.c_void_p
        self._kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        self._kernel32.CloseHandle.restype = ctypes.c_int
        self._advapi32.OpenProcessToken.argtypes = [ctypes.c_void_p,
            ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p)]
        self._advapi32.OpenProcessToken.restype = ctypes.c_int
        self._advapi32.GetTokenInformation.argtypes = [ctypes.c_void_p,
            ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32)]
        self._advapi32.GetTokenInformation.restype = ctypes.c_int
        self._advapi32.ConvertSidToStringSidW.argtypes = [ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_wchar_p)]
        self._advapi32.ConvertSidToStringSidW.restype = ctypes.c_int
        self._advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [
            ctypes.c_wchar_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(ctypes.c_uint32)]
        self._advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype = ctypes.c_int
        self._advapi32.GetSecurityDescriptorDacl.argtypes = [ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(ctypes.c_int)]
        self._advapi32.GetSecurityDescriptorDacl.restype = ctypes.c_int
        self._advapi32.SetFileSecurityW.argtypes = [ctypes.c_wchar_p,
            ctypes.c_uint32, ctypes.c_void_p]
        self._advapi32.SetFileSecurityW.restype = ctypes.c_int
        self._sid = self._current_user_sid()

    def _current_user_sid(self):
        token = ctypes.c_void_p()
        if not self._advapi32.OpenProcessToken(
                self._kernel32.GetCurrentProcess(), 0x0008,
                ctypes.byref(token)):
            raise OSError(ctypes.get_last_error(), "OpenProcessToken for custody ACL failed")
        try:
            needed = ctypes.c_uint32()
            self._advapi32.GetTokenInformation(token, 1, None, 0,
                ctypes.byref(needed))
            if not 0 < needed.value <= 65536:
                raise OSError("TokenUser size is invalid")
            buffer = ctypes.create_string_buffer(needed.value)
            if not self._advapi32.GetTokenInformation(token, 1, buffer,
                    needed.value, ctypes.byref(needed)):
                raise OSError(ctypes.get_last_error(), "TokenUser query failed")

            class _TokenUser(ctypes.Structure):
                _fields_ = [("sid", ctypes.c_void_p), ("attributes", ctypes.c_uint32)]

            user = _TokenUser.from_buffer(buffer)
            if not user.sid:
                raise OSError("TokenUser SID is missing")
            sid_string = ctypes.c_wchar_p()
            if not self._advapi32.ConvertSidToStringSidW(user.sid,
                    ctypes.byref(sid_string)):
                raise OSError(ctypes.get_last_error(), "ConvertSidToStringSidW failed")
            try:
                return sid_string.value
            finally:
                self._kernel32.LocalFree(ctypes.cast(sid_string, ctypes.c_void_p))
        finally:
            self._kernel32.CloseHandle(token)

    @contextmanager
    def _security_descriptor(self, rights="FA"):
        sddl = (f"D:P(A;;{rights};;;SY)(A;;{rights};;;BA)"
                f"(A;;{rights};;;{self._sid})")
        descriptor = ctypes.c_void_p()
        if not self._advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW(
                sddl, 1, ctypes.byref(descriptor), None):
            raise OSError(ctypes.get_last_error(), "custody security descriptor creation failed")
        try:
            present, dacl, defaulted = ctypes.c_int(), ctypes.c_void_p(), ctypes.c_int()
            if not self._advapi32.GetSecurityDescriptorDacl(descriptor,
                    ctypes.byref(present), ctypes.byref(dacl), ctypes.byref(defaulted)):
                raise OSError(ctypes.get_last_error(), "custody DACL extraction failed")
            if not present.value or not dacl.value:
                raise CustodyFenceError("CUSTODY_FENCE_DACL_MISSING")
            yield descriptor, dacl
        finally:
            self._kernel32.LocalFree(descriptor)

    def protect_directory(self, path):
        self._protect_file_system_path(path)

    def protect_file(self, path):
        self._protect_file_system_path(path)

    def _protect_file_system_path(self, path):
        with self._security_descriptor() as (descriptor, _dacl):
            if not self._advapi32.SetFileSecurityW(str(path),
                    _DACL_SECURITY_INFORMATION
                    | _PROTECTED_DACL_SECURITY_INFORMATION, descriptor):
                raise OSError(ctypes.get_last_error(),
                    "custody filesystem DACL could not be applied")

    def protect_registry_key(self, key):
        self._advapi32.RegSetKeySecurity.argtypes = [ctypes.c_void_p,
            ctypes.c_uint32, ctypes.c_void_p]
        self._advapi32.RegSetKeySecurity.restype = ctypes.c_long
        with self._security_descriptor("KA") as (descriptor, _dacl):
            result = self._advapi32.RegSetKeySecurity(
                ctypes.c_void_p(key.handle),
                _DACL_SECURITY_INFORMATION
                | _PROTECTED_DACL_SECURITY_INFORMATION, descriptor)
            if result != 0:
                raise OSError(result, "custody registry DACL could not be applied")


class CustodyFenceError(RuntimeError):
    """The persistent Win32 input fence is unavailable or unresolved."""


class _WindowsNamedMutex:
    WAIT_OBJECT_0 = 0
    WAIT_ABANDONED = 0x80
    WAIT_TIMEOUT = 0x102

    def __init__(self, name):
        if os.name != "nt":
            raise OSError("the native Win32 custody fence requires Windows")
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._kernel32.CreateMutexW.argtypes = [ctypes.c_void_p,
            ctypes.c_int, ctypes.c_wchar_p]
        self._kernel32.CreateMutexW.restype = ctypes.c_void_p
        self._kernel32.WaitForSingleObject.argtypes = [ctypes.c_void_p,
            ctypes.c_uint32]
        self._kernel32.WaitForSingleObject.restype = ctypes.c_uint32
        self._kernel32.ReleaseMutex.argtypes = [ctypes.c_void_p]
        self._kernel32.ReleaseMutex.restype = ctypes.c_int
        self._kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        self._kernel32.CloseHandle.restype = ctypes.c_int
        self._handle = self._kernel32.CreateMutexW(None, False, name)
        if not self._handle:
            raise OSError(ctypes.get_last_error(), "CreateMutexW failed")

    @contextmanager
    def hold(self):
        result = self._kernel32.WaitForSingleObject(self._handle, _MUTEX_WAIT_MS)
        if result == self.WAIT_TIMEOUT:
            raise CustodyFenceError("CUSTODY_FENCE_WAIT_TIMED_OUT")
        if result not in (self.WAIT_OBJECT_0, self.WAIT_ABANDONED):
            raise OSError(ctypes.get_last_error(), "WaitForSingleObject failed")
        abandoned = result == self.WAIT_ABANDONED
        try:
            yield abandoned
        finally:
            if not self._kernel32.ReleaseMutex(self._handle):
                raise OSError(ctypes.get_last_error(), "ReleaseMutex failed")

    def close(self):
        if self._handle:
            handle, self._handle = self._handle, None
            if not self._kernel32.CloseHandle(handle):
                raise OSError(ctypes.get_last_error(), "CloseHandle failed")


class _RegistryInitializationStore:
    """Keep the first-use marker outside the journal directory on Windows."""

    def __init__(self, namespace_digest, acl):
        if os.name != "nt":
            raise OSError("the native custody marker requires Windows")
        import winreg
        self._winreg = winreg
        self._digest = namespace_digest
        self._acl = acl
        self._key_path = r"Software\Unjuno\AgentInterface\CustodyV1"

    def exists(self):
        try:
            with self._winreg.OpenKey(self._winreg.HKEY_CURRENT_USER,
                    self._key_path, 0, self._winreg.KEY_QUERY_VALUE
                    | _WRITE_DAC) as key:
                self._acl.protect_registry_key(key)
                value, value_type = self._winreg.QueryValueEx(key, self._digest)
        except FileNotFoundError:
            return False
        if value_type != self._winreg.REG_SZ or value != _SCHEMA:
            raise CustodyFenceError("CUSTODY_FENCE_REGISTRY_MARKER_INVALID")
        return True

    def create(self):
        try:
            with self._winreg.CreateKeyEx(self._winreg.HKEY_CURRENT_USER,
                    self._key_path, 0, self._winreg.KEY_SET_VALUE
                    | _WRITE_DAC) as key:
                self._acl.protect_registry_key(key)
                self._winreg.SetValueEx(key, self._digest, 0,
                    self._winreg.REG_SZ, _SCHEMA)
        except OSError as error:
            raise CustodyFenceError("CUSTODY_FENCE_REGISTRY_MARKER_WRITE_FAILED") from error


def _win32_logon_namespace_digest():
    """Hash session, process window station, and logon AuthenticationId."""
    if os.name != "nt":
        raise OSError("the Win32 logon namespace is unavailable")

    class _Luid(ctypes.Structure):
        _fields_ = [("LowPart", ctypes.c_uint32), ("HighPart", ctypes.c_int32)]

    class _TokenStatistics(ctypes.Structure):
        _fields_ = [("TokenId", _Luid), ("AuthenticationId", _Luid),
            ("ExpirationTime", ctypes.c_int64), ("TokenType", ctypes.c_uint32),
            ("ImpersonationLevel", ctypes.c_uint32),
            ("DynamicCharged", ctypes.c_uint32),
            ("DynamicAvailable", ctypes.c_uint32),
            ("GroupCount", ctypes.c_uint32), ("PrivilegeCount", ctypes.c_uint32),
            ("ModifiedId", _Luid)]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int
    current_process = kernel32.GetCurrentProcess
    current_process.argtypes = []
    current_process.restype = ctypes.c_void_p
    pid = kernel32.GetCurrentProcessId
    pid.argtypes = []
    pid.restype = ctypes.c_uint32
    session_id = ctypes.c_uint32()
    if not kernel32.ProcessIdToSessionId(pid(), ctypes.byref(session_id)):
        raise OSError(ctypes.get_last_error(), "ProcessIdToSessionId failed")

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    station = user32.GetProcessWindowStation
    station.argtypes = []
    station.restype = ctypes.c_void_p
    station_handle = station()
    if not station_handle:
        raise OSError(ctypes.get_last_error(), "GetProcessWindowStation failed")
    get_object_info = user32
    get_object_info.GetUserObjectInformationW.argtypes = [ctypes.c_void_p,
        ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_uint32)]
    get_object_info.GetUserObjectInformationW.restype = ctypes.c_int
    required = ctypes.c_uint32()
    if get_object_info.GetUserObjectInformationW(station_handle, 2, None, 0,
            ctypes.byref(required)) or not required.value or required.value > 4096:
        raise OSError(ctypes.get_last_error(), "window-station name size query failed")
    name_buffer = ctypes.create_unicode_buffer(
        required.value // ctypes.sizeof(ctypes.c_wchar) + 1)
    if not get_object_info.GetUserObjectInformationW(station_handle, 2,
            name_buffer, ctypes.sizeof(name_buffer), ctypes.byref(required)):
        raise OSError(ctypes.get_last_error(), "window-station name query failed")
    station_name = name_buffer.value
    if not station_name or len(station_name) > 256:
        raise CustodyFenceError("CUSTODY_FENCE_WINDOW_STATION_INVALID")

    token = ctypes.c_void_p()
    advapi32.OpenProcessToken.argtypes = [ctypes.c_void_p, ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_void_p)]
    advapi32.OpenProcessToken.restype = ctypes.c_int
    if not advapi32.OpenProcessToken(current_process(), 0x0008,
            ctypes.byref(token)):
        raise OSError(ctypes.get_last_error(), "OpenProcessToken failed")
    try:
        needed = ctypes.c_uint32()
        advapi32.GetTokenInformation.argtypes = [ctypes.c_void_p, ctypes.c_int,
            ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
        advapi32.GetTokenInformation.restype = ctypes.c_int
        advapi32.GetTokenInformation(token, 10, None, 0, ctypes.byref(needed))
        if needed.value < ctypes.sizeof(_TokenStatistics) or needed.value > 4096:
            raise OSError(ctypes.get_last_error(), "token statistics size invalid")
        buffer = ctypes.create_string_buffer(needed.value)
        if not advapi32.GetTokenInformation(token, 10, buffer, needed.value,
                ctypes.byref(needed)):
            raise OSError(ctypes.get_last_error(), "GetTokenInformation failed")
        stats = _TokenStatistics.from_buffer_copy(buffer.raw)
        auth_id = stats.AuthenticationId
    finally:
        kernel32.CloseHandle(token)

    identity = {"session_id": session_id.value,
        "window_station": station_name,
        "authentication_id": [auth_id.HighPart & 0xFFFFFFFF, auth_id.LowPart]}
    canonical = json.dumps(identity, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=True).encode("ascii")
    return hashlib.sha256(canonical).hexdigest()


def _terminate_or_confirm_process_absent(identity, *, process_opener=None,
                                         wait_timeout_ms=_PROCESS_WAIT_MS,
                                         windows_api=None):
    """Terminate only the exact persisted producer, then verify process exit."""
    if os.name != "nt" and windows_api is None and process_opener is None:
        raise OSError("producer process verification requires Windows")
    if (type(identity) is not dict or set(identity) != {"pid", "creation_time_100ns"}
            or type(identity.get("pid")) is not int or identity["pid"] <= 0
            or type(identity.get("creation_time_100ns")) is not int
            or identity["creation_time_100ns"] <= 0):
        raise ValueError("exact producer process identity required")
    if type(wait_timeout_ms) is not int or not 1 <= wait_timeout_ms <= 5000:
        raise ValueError("producer wait timeout must be between 1 and 5000 ms")
    kernel32 = (windows_api or ctypes.WinDLL("kernel32", use_last_error=True)
                if process_opener is None else None)
    if kernel32 is not None:
        kernel32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
        kernel32.OpenProcess.restype = ctypes.c_void_p
        kernel32.GetProcessTimes.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        kernel32.GetProcessTimes.restype = ctypes.c_int
        kernel32.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        kernel32.WaitForSingleObject.restype = ctypes.c_uint32
        kernel32.TerminateProcess.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        kernel32.TerminateProcess.restype = ctypes.c_int
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel32.CloseHandle.restype = ctypes.c_int
        process = kernel32.OpenProcess(0x00100001 | 0x00001000, False,
                                       identity["pid"])
    else:
        try:
            process = process_opener(identity["pid"])
        except ProcessLookupError:
            return True
        except Exception as error:
            raise OSError("producer process identity could not be verified") from error
    if not process:
        if process_opener is not None:
            return False
        error = ctypes.get_last_error()
        if error == 87:  # ERROR_INVALID_PARAMETER: no process has this PID.
            return True
        raise OSError(error, "OpenProcess could not verify producer identity")
    try:
        if kernel32 is None:
            created = process.creation_time_100ns
            wait_for_single_object = process.wait
            terminate = process.terminate
            close_handle = process.close
        else:
            class _FileTime(ctypes.Structure):
                _fields_ = [("low", ctypes.c_uint32), ("high", ctypes.c_uint32)]

            creation, exited, kernel, user = (
                _FileTime(), _FileTime(), _FileTime(), _FileTime())
            if not kernel32.GetProcessTimes(process, ctypes.byref(creation),
                    ctypes.byref(exited), ctypes.byref(kernel), ctypes.byref(user)):
                raise OSError(ctypes.get_last_error(), "GetProcessTimes failed")
            created = (int(creation.high) << 32) | int(creation.low)
            wait_for_single_object = lambda timeout: kernel32.WaitForSingleObject(
                process, timeout)
            terminate = lambda: kernel32.TerminateProcess(process, 0xC000013A)
            close_handle = lambda: kernel32.CloseHandle(process)
        if created != identity["creation_time_100ns"]:
            return True  # PID reuse: the recorded producer is absent.
        wait = wait_for_single_object(0)
        if wait == 0:
            return True
        if wait != 0x102:
            raise OSError(ctypes.get_last_error(), "producer liveness query failed")
        if not terminate():
            # It may have exited between the signaled check and termination.
            wait = wait_for_single_object(wait_timeout_ms)
            if wait == 0:
                return True
            raise OSError(ctypes.get_last_error(), "TerminateProcess failed")
        wait = wait_for_single_object(wait_timeout_ms)
        if wait == 0:
            return True
        if wait == 0x102:
            return False
        raise OSError(ctypes.get_last_error(), "producer exit wait failed")
    finally:
        close_handle()


class Win32CustodyFence:
    """Persistent, cross-process fail-closed gate for one Win32 logon namespace."""

    def __init__(self, state_directory, namespace_digest, *, mutex_factory=None,
                 initialization_store=None, acl=None):
        if type(namespace_digest) is not str or not _SHA256.fullmatch(namespace_digest):
            raise ValueError("namespace_digest must be a SHA-256 digest")
        self.namespace_digest = namespace_digest
        self.state_directory = Path(state_directory).resolve()
        self.state_directory.mkdir(parents=True, exist_ok=True)
        self._acl = acl
        if self._acl is not None:
            self._acl.protect_directory(self.state_directory)
        self._state_path = self.state_directory / (namespace_digest + ".json")
        self._marker_path = self.state_directory / (namespace_digest + ".initialized")
        self._initialization_store = initialization_store
        name = "Local\\Unjuno.AgentInterface.InputCustody." + namespace_digest
        self._mutex = (mutex_factory or _WindowsNamedMutex)(name)
        self._closed = False

    @classmethod
    def for_current_logon(cls):
        if os.name != "nt":
            raise OSError("the native Win32 custody fence requires Windows")
        local_app_data = os.environ.get("LOCALAPPDATA")
        if not local_app_data or not Path(local_app_data).is_absolute():
            raise CustodyFenceError("CUSTODY_FENCE_LOCAL_APP_DATA_UNAVAILABLE")
        digest = _win32_logon_namespace_digest()
        acl = _WindowsCustodyAcl()
        return cls(Path(local_app_data) / "Unjuno" / "AgentInterface"
                   / "custody-v1", digest,
                   initialization_store=_RegistryInitializationStore(digest, acl),
                   acl=acl)

    @contextmanager
    def _state(self):
        if self._closed:
            raise CustodyFenceError("CUSTODY_FENCE_CLOSED")
        with self._mutex.hold() as abandoned:
            yield self._load_or_initialize(), abandoned

    def _load_or_initialize(self):
        if self._acl is not None:
            self._acl.protect_directory(self.state_directory)
        marker_exists = (self._initialization_store.exists()
                         if self._initialization_store is not None
                         else self._marker_path.exists())
        state_exists = self._state_path.exists()
        if state_exists and self._acl is not None:
            self._acl.protect_file(self._state_path)
        if (self._initialization_store is None and self._marker_path.exists()
                and self._acl is not None):
            self._acl.protect_file(self._marker_path)
        if not marker_exists and not state_exists:
            if self._initialization_store is not None:
                self._initialization_store.create()
            else:
                self._write_marker()
            state = self._empty_state()
            self._write_state(state)
            return state
        if marker_exists != state_exists:
            raise CustodyFenceError("CUSTODY_FENCE_MARKER_STATE_MISMATCH")
        if self._initialization_store is None:
            self._read_marker()
        try:
            raw = self._state_path.read_bytes()
        except OSError as error:
            raise CustodyFenceError("CUSTODY_FENCE_STATE_UNREADABLE") from error
        if len(raw) > _MAX_STATE_BYTES:
            raise CustodyFenceError("CUSTODY_FENCE_STATE_TOO_LARGE")
        try:
            state = json.loads(raw.decode("utf-8"))
        except (UnicodeError, ValueError) as error:
            raise CustodyFenceError("CUSTODY_FENCE_STATE_CORRUPT") from error
        self._validate_state(state)
        return state

    def _empty_state(self):
        return {"schema": _SCHEMA, "namespace_digest": self.namespace_digest,
            "revision": 0, "status": "clear", "pending": None,
            "last_resolved": None, "fenced_generations": []}

    def _validate_state(self, state):
        legacy_keys = {"schema", "namespace_digest", "revision", "status",
            "pending", "last_resolved"}
        current_keys = legacy_keys | {"fenced_generations"}
        if (type(state) is not dict
                or set(state) not in (legacy_keys, current_keys)
                or state.get("schema") != _SCHEMA
                or state.get("namespace_digest") != self.namespace_digest
                or type(state.get("revision")) is not int
                or state["revision"] < 0
                or state.get("status") not in ("clear", "unresolved")):
            raise CustodyFenceError("CUSTODY_FENCE_STATE_SCHEMA_INVALID")
        # Additive upgrade for v1 journals created before generation fences
        # were persisted. The next state transition writes the new field.
        state.setdefault("fenced_generations", [])
        fenced = state["fenced_generations"]
        if (type(fenced) is not list or len(fenced) > _MAX_FENCED_GENERATIONS
                or any(type(item) is not str or not _SHA256.fullmatch(item)
                       for item in fenced)
                or len(set(fenced)) != len(fenced)):
            raise CustodyFenceError("CUSTODY_FENCE_GENERATION_HISTORY_INVALID")
        pending = state.get("pending")
        if state["status"] == "clear":
            if pending is not None:
                raise CustodyFenceError("CUSTODY_FENCE_CLEAR_STATE_HAS_PENDING_ACTION")
        else:
            if (type(pending) is not dict
                or set(pending) != {"operation_id", "target_generation",
                    "obligations", "phase", "input_dispatched",
                    "late_input_horizon_required", "producer_identity",
                    "gate_state"}
                or type(pending.get("operation_id")) is not str
                or not _OPERATION_ID.fullmatch(pending["operation_id"])
                or type(pending.get("target_generation")) is not str
                or not _SHA256.fullmatch(pending["target_generation"])
                or type(pending.get("obligations")) is not list
                or not pending["obligations"]
                or any(type(item) is not str or not item
                       for item in pending["obligations"])
                or len(set(pending["obligations"])) != len(pending["obligations"])
                or type(pending.get("phase")) is not str
                or pending["phase"] not in ("admitted", "starting", "running",
                    "cancel_pending", "unknown", "recovery_pending")
                or (pending.get("input_dispatched") is not None
                    and type(pending.get("input_dispatched")) is not bool)
                or pending.get("late_input_horizon_required") is not True):
                raise CustodyFenceError("CUSTODY_FENCE_PENDING_STATE_INVALID")
            identity = pending.get("producer_identity")
            if (identity is not None and (type(identity) is not dict
                or set(identity) != {"pid", "creation_time_100ns"}
                or type(identity.get("pid")) is not int or identity["pid"] <= 0
                or type(identity.get("creation_time_100ns")) is not int
                or identity["creation_time_100ns"] <= 0)):
                raise CustodyFenceError("CUSTODY_FENCE_PRODUCER_IDENTITY_INVALID")
            if pending.get("gate_state") not in ("closed", "identity_verified",
                "authorization_attempted", "authorized"):
                raise CustodyFenceError("CUSTODY_FENCE_GATE_STATE_INVALID")
            if pending["gate_state"] != "closed" and identity is None:
                raise CustodyFenceError("CUSTODY_FENCE_GATE_IDENTITY_MISSING")
        resolved = state.get("last_resolved")
        if resolved is not None and (type(resolved) is not dict
                or set(resolved) != {"operation_id", "target_generation"}
                or type(resolved.get("operation_id")) is not str
                or not _OPERATION_ID.fullmatch(resolved["operation_id"])
                or type(resolved.get("target_generation")) is not str
                or not _SHA256.fullmatch(resolved["target_generation"])):
            raise CustodyFenceError("CUSTODY_FENCE_RESOLUTION_STATE_INVALID")

    def _write_marker(self):
        try:
            with self._marker_path.open("xb") as stream:
                stream.write((_SCHEMA + "\n" + self.namespace_digest + "\n")
                             .encode("ascii"))
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError:
            pass
        except OSError as error:
            raise CustodyFenceError("CUSTODY_FENCE_MARKER_WRITE_FAILED") from error
        if self._acl is not None:
            self._acl.protect_file(self._marker_path)
        self._read_marker()

    def _read_marker(self):
        try:
            marker = self._marker_path.read_text(encoding="ascii")
        except OSError as error:
            raise CustodyFenceError("CUSTODY_FENCE_MARKER_UNREADABLE") from error
        if marker != _SCHEMA + "\n" + self.namespace_digest + "\n":
            raise CustodyFenceError("CUSTODY_FENCE_MARKER_INVALID")

    def _write_state(self, state):
        payload = json.dumps(state, sort_keys=True, separators=(",", ":"),
            ensure_ascii=True, allow_nan=False).encode("utf-8")
        if len(payload) > _MAX_STATE_BYTES:
            raise CustodyFenceError("CUSTODY_FENCE_STATE_TOO_LARGE")
        fd, temporary = tempfile.mkstemp(prefix=self.namespace_digest + ".",
            suffix=".tmp", dir=str(self.state_directory))
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self._state_path)
            if self._acl is not None:
                self._acl.protect_file(self._state_path)
        except OSError as error:
            try:
                os.unlink(temporary)
            except OSError:
                pass
            raise CustodyFenceError("CUSTODY_FENCE_STATE_WRITE_FAILED") from error

    def snapshot(self):
        with self._state() as (state, abandoned):
            return {"state": deepcopy(state), "mutex_abandoned": abandoned}

    def admit(self, operation_id, target_generation, obligations):
        self._validate_action(operation_id, target_generation, obligations)
        with self._state() as (state, abandoned):
            if abandoned:
                raise CustodyFenceError("CUSTODY_FENCE_MUTEX_ABANDONED")
            if state["status"] != "clear":
                raise CustodyFenceError("ORPHAN_RECOVERY_UNRESOLVED")
            if target_generation in state["fenced_generations"]:
                raise CustodyFenceError("CUSTODY_FENCE_TARGET_GENERATION_FENCED")
            state["revision"] += 1
            state["status"] = "unresolved"
            state["pending"] = {"operation_id": operation_id,
                "target_generation": target_generation,
                "obligations": list(obligations), "phase": "admitted",
                "input_dispatched": None,
                # Any unresolved action may have delivered delayed input.
                "late_input_horizon_required": True,
                "producer_identity": None, "gate_state": "closed"}
            state["last_resolved"] = None
            self._write_state(state)

    @staticmethod
    def _validate_action(operation_id, target_generation, obligations):
        if type(operation_id) is not str or not _OPERATION_ID.fullmatch(operation_id):
            raise ValueError("operation_id must be a lowercase 32-digit hex ID")
        if (type(target_generation) is not str
                or not _SHA256.fullmatch(target_generation)):
            raise ValueError("target_generation must be a SHA-256 digest")
        if (type(obligations) not in (list, tuple) or not obligations
                or any(type(item) is not str or not item for item in obligations)
                or len(set(obligations)) != len(obligations)):
            raise ValueError("unique input obligations are required")

    def update(self, operation_id, target_generation, *, phase=None,
               input_dispatched=None, producer_identity=None, gate_state=None):
        if (phase is not None and phase not in ("admitted", "starting", "running",
                "cancel_pending", "unknown", "recovery_pending")):
            raise ValueError("unsupported custody phase")
        if input_dispatched is not None and type(input_dispatched) is not bool:
            raise ValueError("input_dispatched must be boolean or unknown")
        if producer_identity is not None and (type(producer_identity) is not dict
                or set(producer_identity) != {"pid", "creation_time_100ns"}
                or type(producer_identity.get("pid")) is not int
                or producer_identity["pid"] <= 0
                or type(producer_identity.get("creation_time_100ns")) is not int
                or producer_identity["creation_time_100ns"] <= 0):
            raise ValueError("exact producer process identity required")
        if gate_state is not None and gate_state not in ("closed", "identity_verified",
                "authorization_attempted", "authorized"):
            raise ValueError("unsupported producer gate state")
        if (phase is None and input_dispatched is None
                and producer_identity is None and gate_state is None):
            raise ValueError("a custody transition or witness is required")
        with self._state() as (state, _abandoned):
            pending = self._matching_pending(state, operation_id, target_generation)
            if (producer_identity is not None
                    and pending["producer_identity"] is not None
                    and pending["producer_identity"] != producer_identity):
                raise CustodyFenceError("CUSTODY_FENCE_PRODUCER_IDENTITY_MISMATCH")
            if (phase is not None and _CUSTODY_PHASE_ORDER[phase]
                    < _CUSTODY_PHASE_ORDER[pending["phase"]]):
                phase = None  # A delayed snapshot must not roll custody backward.
            if (gate_state is not None and _PRODUCER_GATE_ORDER[gate_state]
                    < _PRODUCER_GATE_ORDER[pending["gate_state"]]):
                gate_state = None
            if input_dispatched is False and pending["input_dispatched"] is True:
                input_dispatched = None
            if (phase is None and input_dispatched is None
                    and producer_identity is None and gate_state is None):
                return
            if ((phase is None or pending["phase"] == phase)
                    and (input_dispatched is None
                         or pending["input_dispatched"] == input_dispatched)
                    and (producer_identity is None
                         or pending["producer_identity"] == producer_identity)
                    and (gate_state is None or pending["gate_state"] == gate_state)):
                return
            state["revision"] += 1
            if phase is not None:
                pending["phase"] = phase
            if input_dispatched is not None:
                pending["input_dispatched"] = input_dispatched
            if producer_identity is not None:
                pending["producer_identity"] = dict(producer_identity)
            if gate_state is not None:
                pending["gate_state"] = gate_state
            if pending["gate_state"] != "closed" and pending["producer_identity"] is None:
                raise CustodyFenceError("CUSTODY_FENCE_GATE_IDENTITY_MISSING")
            self._write_state(state)

    def confirm_producer_absent(self, identity):
        return _terminate_or_confirm_process_absent(identity)

    def abort_unstarted(self, operation_id, target_generation, *,
                        start_gate_verified_closed, input_dispatched,
                        producer_absent_verified=False):
        """Clear only when the caller proves the gated producer emitted nothing."""
        if (start_gate_verified_closed is not True or input_dispatched is not False
                or type(producer_absent_verified) is not bool):
            raise CustodyFenceError("CUSTODY_FENCE_UNSTARTED_PROOF_REQUIRED")
        with self._state() as (state, _abandoned):
            pending = self._matching_pending(state, operation_id, target_generation)
            gate_never_open = pending["gate_state"] == "closed"
            gate_identity_only = (pending["gate_state"] == "identity_verified"
                and producer_absent_verified
                and pending["producer_identity"] is not None)
            if (not (gate_never_open or gate_identity_only)
                    or pending["input_dispatched"] is True):
                raise CustodyFenceError("CUSTODY_FENCE_INPUT_ALREADY_DISPATCHED")
            state["revision"] += 1
            state["status"] = "clear"
            state["pending"] = None
            state["last_resolved"] = {"operation_id": operation_id,
                "target_generation": target_generation}
            self._append_fenced_generation(state, target_generation)
            self._write_state(state)

    def require_recovery_source(self, operation_id, target_generation, obligations):
        self._validate_action(operation_id, target_generation, obligations)
        with self._state() as (state, abandoned):
            if state["status"] != "unresolved":
                raise CustodyFenceError("CUSTODY_FENCE_NO_UNRESOLVED_ACTION")
            pending = self._matching_pending(state, operation_id, target_generation)
            if pending["obligations"] != list(obligations):
                raise CustodyFenceError("CUSTODY_FENCE_OBLIGATIONS_MISMATCH")
            return {"pending": deepcopy(pending), "mutex_abandoned": abandoned}

    def persist_resolved_generation_fence(self, operation_id, target_generation):
        """Persist a fresh-generation requirement for the exact last resolution."""
        self._validate_action(operation_id, target_generation, ["custody"])
        with self._state() as (state, _abandoned):
            resolved = state.get("last_resolved")
            if (state["status"] != "clear" or type(resolved) is not dict
                    or resolved.get("operation_id") != operation_id
                    or resolved.get("target_generation") != target_generation):
                raise CustodyFenceError("CUSTODY_FENCE_RESOLUTION_SOURCE_MISMATCH")
            if target_generation in state["fenced_generations"]:
                return False
            self._append_fenced_generation(state, target_generation)
            state["revision"] += 1
            self._write_state(state)
            return True

    def resolve(self, operation_id, target_generation, *, release_confirmed,
                late_input_horizon_required=False, late_input_horizon_verified=False,
                fence_generations=()):
        if type(release_confirmed) is not bool:
            raise ValueError("release_confirmed must be boolean")
        if (type(late_input_horizon_required) is not bool
                or type(late_input_horizon_verified) is not bool):
            raise ValueError("late-input horizon evidence must be boolean")
        if (type(fence_generations) not in (list, tuple)
                or any(type(item) is not str or not _SHA256.fullmatch(item)
                       for item in fence_generations)
                or len(set(fence_generations)) != len(fence_generations)):
            raise ValueError("fence_generations must contain unique SHA-256 digests")
        if not release_confirmed:
            raise CustodyFenceError("CUSTODY_FENCE_RELEASE_UNCONFIRMED")
        with self._state() as (state, _abandoned):
            pending = self._matching_pending(state, operation_id, target_generation)
            if late_input_horizon_required != pending["late_input_horizon_required"]:
                raise CustodyFenceError(
                    "CUSTODY_FENCE_HORIZON_REQUIREMENT_MISMATCH")
            if (pending["late_input_horizon_required"]
                    and not late_input_horizon_verified):
                raise CustodyFenceError(
                    "CUSTODY_FENCE_LATE_INPUT_HORIZON_UNVERIFIED")
            state["revision"] += 1
            state["status"] = "clear"
            state["pending"] = None
            state["last_resolved"] = {"operation_id": operation_id,
                "target_generation": target_generation}
            for generation in fence_generations:
                self._append_fenced_generation(state, generation)
            self._write_state(state)

    @staticmethod
    def _append_fenced_generation(state, target_generation):
        fenced = state["fenced_generations"]
        if target_generation in fenced:
            return
        if len(fenced) >= _MAX_FENCED_GENERATIONS:
            raise CustodyFenceError("CUSTODY_FENCE_GENERATION_HISTORY_FULL")
        fenced.append(target_generation)

    @staticmethod
    def _matching_pending(state, operation_id, target_generation):
        if state["status"] != "unresolved":
            raise CustodyFenceError("CUSTODY_FENCE_NO_UNRESOLVED_ACTION")
        pending = state["pending"]
        if (pending["operation_id"] != operation_id
                or pending["target_generation"] != target_generation):
            raise CustodyFenceError("CUSTODY_FENCE_SOURCE_MISMATCH")
        return pending

    def close(self):
        if not self._closed:
            self._closed = True
            close = getattr(self._mutex, "close", None)
            if callable(close):
                close()
