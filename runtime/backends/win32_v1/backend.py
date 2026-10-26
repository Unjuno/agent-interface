"""Win32 implementation candidate for the Agent Interface runtime core v1 backend.

The semantic core remains platform neutral. This module owns only Win32-native
translation, preflight, effect emission, capture, and terminal release checks.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import secrets
import sys
import time
from ctypes import wintypes
from typing import Any

from runtime.core_v1.contract import OFFICE_FLOOR, capability_manifest, validate_backend_manifest


class Win32BackendError(RuntimeError):
    pass


class Win32ExecutionError(Win32BackendError):
    """Owned envelope retaining execution and cleanup evidence."""
    def __init__(self, original_error, release_receipt, cleanup_error):
        super().__init__(str(original_error))
        self.original_error = original_error
        self.release_receipt = release_receipt
        self.cleanup_error = cleanup_error



SW_RESTORE = 9
GA_ROOT = 2
PW_CLIENTONLY = 0x00000001
SRCCOPY = 0x00CC0020
DIB_RGB_COLORS = 0
BI_RGB = 0
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_EXTENDEDKEY = 0x0001
MAPVK_VK_TO_VSC_EX = 4
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_HWHEEL = 0x1000
WHEEL_DELTA = 120
VK_LBUTTON = 0x01
VK_RBUTTON = 0x02
VK_MBUTTON = 0x04
VK_BACK = 0x08
VK_TAB = 0x09
VK_RETURN = 0x0D
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_ESCAPE = 0x1B
VK_SPACE = 0x20
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_DELETE = 0x2E
UOI_NAME = 2
UOI_IO = 6
DESKTOP_READOBJECTS = 0x0001
DESKTOP_HOOKCONTROL = 0x0008
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
TOKEN_QUERY = 0x0008
TOKEN_INTEGRITY_LEVEL = 25
TARGET_INCARNATION_PROPERTY = "Unjuno.AgentInterface.Win32TargetIncarnation.v1"

KEY_ALIASES = {
    "CTRL": VK_CONTROL, "CONTROL": VK_CONTROL, "SHIFT": VK_SHIFT,
    "ALT": VK_MENU, "ENTER": VK_RETURN, "RETURN": VK_RETURN,
    "TAB": VK_TAB, "ESC": VK_ESCAPE, "ESCAPE": VK_ESCAPE,
    "SPACE": VK_SPACE, "BACKSPACE": VK_BACK, "DELETE": VK_DELETE,
    "LEFT": VK_LEFT, "RIGHT": VK_RIGHT, "UP": VK_UP, "DOWN": VK_DOWN,
}
EXTENDED_ARROW_SCAN_CODES = {
    VK_LEFT: 0x4B,
    VK_UP: 0x48,
    VK_RIGHT: 0x4D,
    VK_DOWN: 0x50,
}
BUTTON_FLAGS = {
    "left": (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP, VK_LBUTTON),
    "middle": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP, VK_MBUTTON),
    "right": (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP, VK_RBUTTON),
}
ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR)]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD)]


class INPUTUNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", INPUTUNION)]


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class RECT(ctypes.Structure):
    _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG),
                ("right", wintypes.LONG), ("bottom", wintypes.LONG)]


class FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", wintypes.DWORD),
                ("dwHighDateTime", wintypes.DWORD)]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG),
                ("biHeight", wintypes.LONG), ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD)]


class RGBQUAD(ctypes.Structure):
    _fields_ = [("rgbBlue", ctypes.c_ubyte), ("rgbGreen", ctypes.c_ubyte),
                ("rgbRed", ctypes.c_ubyte), ("rgbReserved", ctypes.c_ubyte)]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", RGBQUAD * 1)]


def utf16_units(value: str) -> tuple[int, ...]:
    if not isinstance(value, str):
        raise Win32BackendError("text must be str")
    if any(0xD800 <= ord(ch) <= 0xDFFF for ch in value):
        raise Win32BackendError("text contains explicit surrogate code point")
    raw = value.encode("utf-16-le", "strict")
    return tuple(int.from_bytes(raw[i:i + 2], "little") for i in range(0, len(raw), 2))


def virtual_key(key: str) -> int:
    if not isinstance(key, str) or not key:
        raise Win32BackendError("invalid key")
    upper = key.upper()
    if upper in KEY_ALIASES:
        return KEY_ALIASES[upper]
    if len(key) == 1 and key.isascii() and key.isalnum():
        return ord(key.upper())
    raise Win32BackendError(f"unmapped key {key}")


class Win32Backend:
    def __init__(self, targets: dict[str, int]):
        if sys.platform != "win32":
            raise Win32BackendError("Win32 backend requires Windows")
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
        self._configure_api()
        try:
            self.user32.SetProcessDPIAware()
        except Exception:
            pass
        self.targets = {name: int(hwnd) for name, hwnd in targets.items()}
        for name, hwnd in self.targets.items():
            if not self.user32.IsWindow(hwnd):
                raise Win32BackendError(f"invalid HWND for target {name}")
        self.held_keys: dict[str, int] = {}
        self.held_key_encodings: dict[str, str | None] = {}
        self.held_key_targets: dict[str, str | None] = {}
        self.held_buttons: set[str] = set()
        self.held_button_targets: dict[str, str | None] = {}
        self.focused_target: str | None = None
        self._last_state_query_witness: list[dict[str, Any]] = []
        self.pending_unicode_ups: set[int] = set()
        self.emissions = 0
        self.capture_artifacts = None
        self._target_incarnation_bindings: dict[tuple[str, int], dict[str, Any]] = {}
        self._closed = False
        self._close_report = None

    def _configure_api(self) -> None:
        self.user32.IsWindow.argtypes = [wintypes.HWND]
        self.user32.IsWindow.restype = wintypes.BOOL
        self.user32.SetPropW.argtypes = [wintypes.HWND, wintypes.LPCWSTR,
                                         wintypes.HANDLE]
        self.user32.SetPropW.restype = wintypes.BOOL
        self.user32.GetPropW.argtypes = [wintypes.HWND, wintypes.LPCWSTR]
        self.user32.GetPropW.restype = wintypes.HANDLE
        self.user32.GetWindowThreadProcessId.argtypes = [
            wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        self.user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        self.user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
        self.user32.GetClientRect.restype = wintypes.BOOL
        self.user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(POINT)]
        self.user32.ClientToScreen.restype = wintypes.BOOL
        self.user32.SetForegroundWindow.argtypes = [wintypes.HWND]
        self.user32.SetForegroundWindow.restype = wintypes.BOOL
        self.user32.BringWindowToTop.argtypes = [wintypes.HWND]
        self.user32.BringWindowToTop.restype = wintypes.BOOL
        self.user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        self.user32.GetForegroundWindow.restype = wintypes.HWND
        self.user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
        self.user32.GetCursorPos.restype = wintypes.BOOL
        self.user32.WindowFromPoint.argtypes = [POINT]
        self.user32.WindowFromPoint.restype = wintypes.HWND
        self.user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
        self.user32.GetAncestor.restype = wintypes.HWND
        self.user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
        self.user32.SetCursorPos.restype = wintypes.BOOL
        self.user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
        self.user32.SendInput.restype = wintypes.UINT
        self.user32.MapVirtualKeyW.argtypes = [wintypes.UINT, wintypes.UINT]
        self.user32.MapVirtualKeyW.restype = wintypes.UINT
        self.user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
        self.user32.GetAsyncKeyState.restype = wintypes.SHORT
        self.user32.OpenInputDesktop.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.user32.OpenInputDesktop.restype = wintypes.HANDLE
        self.user32.GetUserObjectInformationW.argtypes = [wintypes.HANDLE, ctypes.c_int,
            wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
        self.user32.GetUserObjectInformationW.restype = wintypes.BOOL
        self.user32.GetThreadDesktop.argtypes = [wintypes.DWORD]
        self.user32.GetThreadDesktop.restype = wintypes.HANDLE
        self.user32.CloseDesktop.argtypes = [wintypes.HANDLE]
        self.user32.CloseDesktop.restype = wintypes.BOOL
        self.user32.GetDC.argtypes = [wintypes.HWND]
        self.user32.GetDC.restype = wintypes.HDC
        self.user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
        self.user32.ReleaseDC.restype = ctypes.c_int
        self.user32.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
        self.user32.PrintWindow.restype = wintypes.BOOL
        self.gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
        self.gdi32.CreateCompatibleDC.restype = wintypes.HDC
        self.gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
        self.gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
        self.gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
        self.gdi32.SelectObject.restype = wintypes.HGDIOBJ
        self.gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
        self.gdi32.DeleteObject.restype = wintypes.BOOL
        self.gdi32.DeleteDC.argtypes = [wintypes.HDC]
        self.gdi32.DeleteDC.restype = wintypes.BOOL
        self.gdi32.GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP, wintypes.UINT,
                                        wintypes.UINT, wintypes.LPVOID,
                                        ctypes.POINTER(BITMAPINFO), wintypes.UINT]
        self.gdi32.GetDIBits.restype = ctypes.c_int
        self.gdi32.BitBlt.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int,
                                      ctypes.c_int, ctypes.c_int, wintypes.HDC,
                                      ctypes.c_int, ctypes.c_int, wintypes.DWORD]
        self.gdi32.BitBlt.restype = wintypes.BOOL
        self.kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL,
                                              wintypes.DWORD]
        self.kernel32.OpenProcess.restype = wintypes.HANDLE
        self.kernel32.GetProcessTimes.argtypes = [
            wintypes.HANDLE, ctypes.POINTER(FILETIME), ctypes.POINTER(FILETIME),
            ctypes.POINTER(FILETIME), ctypes.POINTER(FILETIME)]
        self.kernel32.GetProcessTimes.restype = wintypes.BOOL
        self.kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel32.CloseHandle.restype = wintypes.BOOL
        self.kernel32.GetCurrentThreadId.restype = wintypes.DWORD
        self.kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        self.advapi32.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                   ctypes.POINTER(wintypes.HANDLE)]
        self.advapi32.OpenProcessToken.restype = wintypes.BOOL
        self.advapi32.GetTokenInformation.argtypes = [wintypes.HANDLE, ctypes.c_int,
            wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
        self.advapi32.GetTokenInformation.restype = wintypes.BOOL

    def manifest(self) -> dict[str, Any]:
        row = capability_manifest(
            "win32-v1", "windows", "win32", OFFICE_FLOOR,
            frames=("screen_physical_px", "window_client"),
            permissions=("interactive-desktop", "sendinput"),
        )
        row["capabilities"]["input.text"]["detail"] = (
            "Unicode KEYEVENTF_UNICODE; explicit surrogate code points rejected"
        )
        return validate_backend_manifest(row)

    def monotonic_ns(self) -> int:
        return time.monotonic_ns()

    def _target(self, name: str) -> int:
        hwnd = self.targets.get(name)
        if hwnd is None or not self.user32.IsWindow(hwnd):
            raise Win32BackendError(f"unknown or stale target {name}")
        return hwnd

    def process_identity(self, target: str) -> dict[str, int]:
        """Return the HWND owner's PID and process creation time, fail closed.

        The process handle is opened only for PROCESS_QUERY_LIMITED_INFORMATION.
        The HWND-to-PID/TID association is sampled again after GetProcessTimes
        to reject an observed owner change during the query. This is a
        generation discriminator, not an atomic guarantee against later change.
        """
        hwnd = self._target(target)
        identity = self._window_owner_identity_for_hwnd(hwnd)
        return {"pid": identity["pid"],
                "creation_time_100ns": identity["creation_time_100ns"]}

    def _window_owner_identity_for_hwnd(self, hwnd: int) -> dict[str, int]:
        """Read process and GUI-thread identity for one resolved HWND."""
        pid = wintypes.DWORD()
        thread_id = self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if not thread_id or not pid.value:
            raise Win32BackendError("GetWindowThreadProcessId failed")
        owner = self.kernel32.OpenProcess(0x1000, False, pid.value)
        if not owner:
            raise Win32BackendError("OpenProcess for target identity failed")
        try:
            creation, exited, kernel, user = FILETIME(), FILETIME(), FILETIME(), FILETIME()
            if not self.kernel32.GetProcessTimes(
                    owner, ctypes.byref(creation), ctypes.byref(exited),
                    ctypes.byref(kernel), ctypes.byref(user)):
                raise Win32BackendError("GetProcessTimes for target identity failed")
            confirmed_pid = wintypes.DWORD()
            confirmed_thread_id = self.user32.GetWindowThreadProcessId(
                hwnd, ctypes.byref(confirmed_pid))
            if (not confirmed_thread_id or confirmed_thread_id != thread_id
                    or confirmed_pid.value != pid.value):
                raise Win32BackendError("target owner changed during identity query")
            created_100ns = ((int(creation.dwHighDateTime) << 32)
                             | int(creation.dwLowDateTime))
            if created_100ns <= 0:
                raise Win32BackendError("invalid target process creation time")
            return {"pid": int(pid.value),
                    "creation_time_100ns": created_100ns,
                    "window_thread_id": int(thread_id)}
        finally:
            self.kernel32.CloseHandle(owner)

    def target_generation(self, target: str) -> str:
        """Return a fail-closed SHA-256 discriminator for the configured HWND.

        The digest binds the numeric HWND to its GUI thread, owner PID, and
        process creation time and a per-window-lifetime property. A reused
        numeric HWND without the original property is refused for this backend.
        The property read is not an atomic fence against destruction immediately
        after the check.
        """
        if getattr(self, "_closed", False):
            raise Win32BackendError("target generation unavailable after backend close")
        hwnd = self._target(target)
        identity = self._window_owner_identity_for_hwnd(hwnd)
        if self._target(target) != hwnd:
            raise Win32BackendError("target HWND changed during generation query")
        cookie = self._target_incarnation_cookie(target, hwnd, identity)
        if self._target(target) != hwnd:
            raise Win32BackendError("target HWND changed during generation query")
        payload = [hwnd, identity["window_thread_id"], identity["pid"],
                   identity["creation_time_100ns"], cookie]
        return hashlib.sha256(json.dumps(
            payload, separators=(",", ":")).encode("ascii")).hexdigest()

    def _target_incarnation_cookie(self, target: str, hwnd: int,
                                   identity: dict[str, int]) -> int:
        bindings = getattr(self, "_target_incarnation_bindings", None)
        if bindings is None:
            bindings = self._target_incarnation_bindings = {}
        key = (target, hwnd)
        binding = bindings.get(key)
        try:
            current = self._handle_value(self.user32.GetPropW(
                hwnd, TARGET_INCARNATION_PROPERTY))
        except Exception as error:
            raise Win32BackendError("target incarnation property read failed") from error
        if binding is not None:
            if (binding["identity"] != identity or
                    current != binding["cookie"]):
                raise Win32BackendError("target HWND incarnation property changed")
            return current
        if current:
            cookie = current
        else:
            cookie = secrets.randbits(ctypes.sizeof(ctypes.c_void_p) * 8 - 1) or 1
            ctypes.set_last_error(0)
            try:
                set_ok = self.user32.SetPropW(
                    hwnd, TARGET_INCARNATION_PROPERTY, wintypes.HANDLE(cookie))
                error_code = ctypes.get_last_error()
            except Exception as error:
                raise Win32BackendError("target incarnation property set failed") from error
            if not set_ok:
                raise Win32BackendError(
                    f"target incarnation property set failed error={error_code}")
            try:
                current = self._handle_value(self.user32.GetPropW(
                    hwnd, TARGET_INCARNATION_PROPERTY))
            except Exception as error:
                raise Win32BackendError(
                    "target incarnation property readback failed") from error
            if current != cookie:
                raise Win32BackendError("target incarnation property readback mismatch")
        bindings[key] = {"hwnd": hwnd, "identity": dict(identity),
                         "cookie": cookie}
        return cookie

    @staticmethod
    def _handle_value(value) -> int:
        if value is None:
            return 0
        if type(value) is int:
            return value
        return int(ctypes.cast(value, ctypes.c_void_p).value or 0)

    def close(self) -> dict[str, Any]:
        """Close this backend while leaving HWND-lifetime markers to Windows.

        A property can be shared by multiple backend instances. Win32 has no
        compare-and-remove operation, so deleting it here could invalidate a
        concurrent session or remove a marker another session just replaced.
        Windows destroys the property with its HWND.
        """
        if getattr(self, "_closed", False):
            return self._close_report
        results = []
        for binding in getattr(self, "_target_incarnation_bindings", {}).values():
            row = {"hwnd": binding["hwnd"],
                   "status": "retained_until_window_destroyed"}
            try:
                if not self.user32.IsWindow(binding["hwnd"]):
                    row["status"] = "window_destroyed"
                else:
                    current = self._handle_value(self.user32.GetPropW(
                        binding["hwnd"], TARGET_INCARNATION_PROPERTY))
                    if current == 0:
                        row["status"] = "property_missing"
                    elif current != binding["cookie"]:
                        row["status"] = "property_value_changed"
            except Exception as error:
                row["error"] = repr(error)
            results.append(row)
        self._close_report = {
            "status": "closed",
            "property_cleanup": results,
        }
        self._closed = True
        return self._close_report

    def geometry(self, target: str) -> dict[str, int]:
        hwnd = self._target(target)
        rect = RECT()
        if not self.user32.GetClientRect(hwnd, ctypes.byref(rect)):
            raise Win32BackendError("GetClientRect failed")
        origin = POINT(0, 0)
        if not self.user32.ClientToScreen(hwnd, ctypes.byref(origin)):
            raise Win32BackendError("ClientToScreen failed")
        return {"x": int(origin.x), "y": int(origin.y),
                "width": int(rect.right - rect.left),
                "height": int(rect.bottom - rect.top)}

    def focus(self, target: str) -> None:
        hwnd = self._target(target)
        self.user32.ShowWindow(hwnd, SW_RESTORE)
        self.user32.BringWindowToTop(hwnd)
        set_foreground_result = bool(self.user32.SetForegroundWindow(hwnd))
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            observed = self._handle_value(self.user32.GetForegroundWindow())
            if observed == hwnd or (observed and self._handle_value(
                    self.user32.GetAncestor(observed, GA_ROOT)) == hwnd):
                self.focused_target = target
                return
            time.sleep(0.01)
        observed_foreground_hwnd = self._handle_value(
            self.user32.GetForegroundWindow())
        raise Win32BackendError(
            "foreground focus verification failed "
            f"(SetForegroundWindow={set_foreground_result}, "
            f"observed_foreground_hwnd={observed_foreground_hwnd})")

    def _root_point(self, target: str, frame: str, x: int, y: int) -> tuple[int, int]:
        if frame == "screen_physical_px":
            return x, y
        if frame == "window_client":
            g = self.geometry(target)
            return g["x"] + x, g["y"] + y
        raise Win32BackendError(f"unsupported frame {frame}")

    def _send(self, item: INPUT) -> None:
        array = (INPUT * 1)(item)
        sent = self.user32.SendInput(1, array, ctypes.sizeof(INPUT))
        if sent != 1:
            raise Win32BackendError(f"SendInput failed error={ctypes.get_last_error()}")
        self.emissions += 1

    def _send_key(self, vk: int, down: bool, encoding: str | None = None) -> None:
        item = INPUT(type=INPUT_KEYBOARD)
        flags = 0 if down else KEYEVENTF_KEYUP
        if encoding == "scan_code":
            mapped = int(self.user32.MapVirtualKeyW(vk, MAPVK_VK_TO_VSC_EX))
            scan_code = mapped & 0xFF
            if not scan_code:
                raise Win32BackendError(f"key {vk} has no scan code")
            prefix = (mapped >> 8) & 0xFF
            flags |= KEYEVENTF_SCANCODE
            if prefix in {0xE0, 0xE1}:
                flags |= KEYEVENTF_EXTENDEDKEY
            item.ki = KEYBDINPUT(0, scan_code, flags, 0, 0)
            self._send(item)
            return
        if encoding not in {None, "virtual_key"}:
            raise Win32BackendError(f"unsupported key encoding {encoding!r}")
        scan_code = EXTENDED_ARROW_SCAN_CODES.get(vk)
        if scan_code is None:
            item.ki = KEYBDINPUT(vk, 0, flags, 0, 0)
        else:
            item.ki = KEYBDINPUT(
                0, scan_code,
                flags | KEYEVENTF_SCANCODE | KEYEVENTF_EXTENDEDKEY, 0, 0,
            )
        self._send(item)

    def _desktop_name(self, handle) -> str | None:
        needed = wintypes.DWORD()
        self.user32.GetUserObjectInformationW(handle, UOI_NAME, None, 0,
                                              ctypes.byref(needed))
        if not needed.value:
            return None
        buffer = ctypes.create_unicode_buffer(
            needed.value // ctypes.sizeof(wintypes.WCHAR) + 2)
        if not self.user32.GetUserObjectInformationW(
                handle, UOI_NAME, buffer, ctypes.sizeof(buffer), ctypes.byref(needed)):
            return None
        return buffer.value

    def _process_integrity_rid(self, process_handle) -> int | None:
        token = wintypes.HANDLE()
        if not self.advapi32.OpenProcessToken(process_handle, TOKEN_QUERY,
                                             ctypes.byref(token)):
            return None
        try:
            needed = wintypes.DWORD()
            self.advapi32.GetTokenInformation(token, TOKEN_INTEGRITY_LEVEL,
                None, 0, ctypes.byref(needed))
            if not needed.value:
                return None
            buffer = ctypes.create_string_buffer(needed.value)
            if not self.advapi32.GetTokenInformation(token, TOKEN_INTEGRITY_LEVEL,
                    buffer, needed.value, ctypes.byref(needed)):
                return None
            sid = ctypes.c_void_p.from_buffer(buffer).value
            if not sid:
                return None
            count = ctypes.c_ubyte.from_address(sid + 1).value
            if not count:
                return None
            return ctypes.c_uint32.from_address(sid + 8 + 4 * (count - 1)).value
        finally:
            self.kernel32.CloseHandle(token)

    def _async_key_state_query_witness(self, target: str | None):
        """Return evidence that a zero GetAsyncKeyState sample means key-up here.

        A zero sample is ambiguous unless this target is the foreground window
        on the active input desktop, the caller can open that desktop with
        hook-control rights, and the caller is at least as privileged as the
        target. Any unavailable fact leaves the input obligation UNKNOWN.
        """
        targets = getattr(self, "targets", {})
        if target not in targets:
            return None
        desktop = None
        process = None
        try:
            hwnd = int(self.user32.GetForegroundWindow() or 0)
            if hwnd != targets[target]:
                return None
            pid = wintypes.DWORD()
            thread_id = int(self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid)))
            if not thread_id or not pid.value:
                return None
            desktop = self.user32.OpenInputDesktop(
                0, False, DESKTOP_READOBJECTS | DESKTOP_HOOKCONTROL)
            if not desktop:
                return None
            is_input = wintypes.DWORD()
            needed = wintypes.DWORD()
            if not self.user32.GetUserObjectInformationW(
                    desktop, UOI_IO, ctypes.byref(is_input), ctypes.sizeof(is_input),
                    ctypes.byref(needed)) or not is_input.value:
                return None
            input_name = self._desktop_name(desktop)
            probe_desktop = self.user32.GetThreadDesktop(
                self.kernel32.GetCurrentThreadId())
            target_desktop = self.user32.GetThreadDesktop(thread_id)
            probe_name = self._desktop_name(probe_desktop) if probe_desktop else None
            target_name = self._desktop_name(target_desktop) if target_desktop else None
            if not input_name or input_name != probe_name or input_name != target_name:
                return None
            process = self.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
            if not process:
                return None
            probe_rid = self._process_integrity_rid(self.kernel32.GetCurrentProcess())
            target_rid = self._process_integrity_rid(process)
            if probe_rid is None or target_rid is None or probe_rid < target_rid:
                return None
            # Recheck that the same configured foreground target still owns
            # the active input desktop after the access and token queries.
            if int(self.user32.GetForegroundWindow() or 0) != hwnd:
                return None
            return {"target": target, "hwnd": hwnd, "pid": int(pid.value),
                    "thread_id": thread_id, "input_desktop": input_name,
                    "input_desktop_active": True,
                    "desktop_hookcontrol_opened": True,
                    "probe_integrity_rid": probe_rid,
                    "target_integrity_rid": target_rid}
        except Exception:
            return None
        finally:
            if process:
                self.kernel32.CloseHandle(process)
            if desktop:
                self.user32.CloseDesktop(desktop)

    def _key_down_state(self, vk: int, target: str | None = None) -> bool | None:
        self._last_state_query_witness = []
        try:
            state = int(self.user32.GetAsyncKeyState(vk)) & 0x8001
        except Exception as error:
            raise Win32BackendError(f"key state query failed for {vk}: {error}") from error
        if state & 0x8000:
            return True
        if state & 1:
            return False
        before = self._async_key_state_query_witness(target)
        if before is None:
            return None
        try:
            confirmed = int(self.user32.GetAsyncKeyState(vk)) & 0x8001
        except Exception as error:
            raise Win32BackendError(f"key state query failed for {vk}: {error}") from error
        if confirmed & 0x8000:
            return True
        if confirmed & 1:
            return False
        after = self._async_key_state_query_witness(target)
        if before is not None and after is not None and before == after:
            self._last_state_query_witness = [before, after]
            return False
        return None

    def _key_is_down(self, vk: int, target: str | None = None) -> bool:
        state = self._key_down_state(vk, target)
        if state is None:
            raise Win32BackendError(f"key state is unknown for {vk}")
        return state

    def _send_unicode_unit(self, unit: int, down: bool) -> None:
        item = INPUT(type=INPUT_KEYBOARD)
        flags = KEYEVENTF_UNICODE | (0 if down else KEYEVENTF_KEYUP)
        item.ki = KEYBDINPUT(0, unit, flags, 0, 0)
        self._send(item)

    def key_state(self, key: str, down: bool, encoding: str | None = None) -> None:
        vk = virtual_key(key)
        if down:
            self._send_key(vk, True, encoding) if encoding is not None else self._send_key(vk, True)
        else:
            held_encoding = getattr(self, "held_key_encodings", {}).get(key)
            if encoding is not None and held_encoding != encoding:
                raise Win32BackendError(f"key UP encoding differs from held DOWN: {key}")
            effective_encoding = held_encoding if encoding is None else encoding
            self._send_key(vk, False, effective_encoding) if effective_encoding is not None else self._send_key(vk, False)
        if down:
            self.held_keys[key] = vk
            if not hasattr(self, "held_key_encodings"):
                self.held_key_encodings = {}
            self.held_key_encodings[key] = encoding
            if not hasattr(self, "held_key_targets"):
                self.held_key_targets = {}
            self.held_key_targets[key] = getattr(self, "focused_target", None)
        elif self._key_is_down(vk, getattr(self, "held_key_targets", {}).get(
                key, getattr(self, "focused_target", None))):
            # Do not let later operations run while an explicit UP remains
            # unresolved. The enclosing execute path will retain custody and
            # attempt cleanup before returning the failure.
            raise Win32BackendError(f"key UP unverified: {key}")

    def key_chord(self, keys: list[str], encoding: str | None = None) -> None:
        for key in keys:
            self.key_state(key, True, encoding) if encoding is not None else self.key_state(key, True)
        for key in reversed(keys):
            self.key_state(key, False, encoding) if encoding is not None else self.key_state(key, False)

    def text(self, value: str) -> None:
        if self.pending_unicode_ups:
            raise Win32BackendError("unresolved Unicode UP delivery")
        for unit in utf16_units(value):
            self._send_unicode_unit(unit, True)
            self.pending_unicode_ups.add(unit)
            self._send_unicode_unit(unit, False)
            self.pending_unicode_ups.remove(unit)

    def pointer_move(self, target: str, frame: str, x: int, y: int) -> None:
        rx, ry = self._root_point(target, frame, x, y)
        if not self.user32.SetCursorPos(rx, ry):
            raise Win32BackendError("SetCursorPos failed")
        self.emissions += 1

    def pointer_button(self, button: str, down: bool) -> None:
        if button not in BUTTON_FLAGS:
            raise Win32BackendError(f"unsupported button {button}")
        down_flag, up_flag, _ = BUTTON_FLAGS[button]
        item = INPUT(type=INPUT_MOUSE)
        item.mi = MOUSEINPUT(0, 0, 0, down_flag if down else up_flag, 0, 0)
        self._send(item)
        if down:
            self.held_buttons.add(button)
            if not hasattr(self, "held_button_targets"):
                self.held_button_targets = {}
            self.held_button_targets[button] = getattr(self, "focused_target", None)
        elif self._key_is_down(BUTTON_FLAGS[button][2],
                               getattr(self, "held_button_targets", {}).get(
                                   button, getattr(self, "focused_target", None))):
            raise Win32BackendError(f"button UP unverified: {button}")

    def _require_pointer_target(self, target: str) -> None:
        """Refuse a global mouse-down when another top-level window owns the cursor."""
        target_hwnd = self._target(target)
        point = POINT()
        if not self.user32.GetCursorPos(ctypes.byref(point)):
            raise Win32BackendError("POINTER_TARGET_CHECK_CURSOR_UNAVAILABLE")
        hit_hwnd = self._handle_value(self.user32.WindowFromPoint(point))
        if not hit_hwnd:
            raise Win32BackendError("POINTER_TARGET_CHECK_HIT_UNAVAILABLE")
        root_hwnd = self._handle_value(
            self.user32.GetAncestor(hit_hwnd, GA_ROOT))
        if not root_hwnd:
            raise Win32BackendError("POINTER_TARGET_CHECK_ROOT_UNAVAILABLE")
        if root_hwnd != target_hwnd:
            raise Win32BackendError(
                "POINTER_TARGET_OCCLUDED "
                f"(expected_hwnd={target_hwnd}, hit_hwnd={hit_hwnd}, "
                f"root_hwnd={root_hwnd}, cursor=({point.x},{point.y}))")

    def scroll(self, dx: int, dy: int) -> None:
        for value, flag in ((dy, MOUSEEVENTF_WHEEL), (dx, MOUSEEVENTF_HWHEEL)):
            if not value:
                continue
            item = INPUT(type=INPUT_MOUSE)
            item.mi = MOUSEINPUT(0, 0, ctypes.c_ulong(value * WHEEL_DELTA).value,
                                 flag, 0, 0)
            self._send(item)

    def _capture_hdc(self, source_hwnd: int, sx: int, sy: int,
                     w: int, h: int, *, print_window: bool) -> bytes:
        source_dc = self.user32.GetDC(source_hwnd)
        if not source_dc:
            raise Win32BackendError("GetDC failed")
        mem_dc = self.gdi32.CreateCompatibleDC(source_dc)
        bitmap = self.gdi32.CreateCompatibleBitmap(source_dc, w, h)
        old = None
        try:
            if not mem_dc or not bitmap:
                raise Win32BackendError("GDI allocation failed")
            old = self.gdi32.SelectObject(mem_dc, bitmap)
            if not old or old == ctypes.c_void_p(-1).value:
                old = None
                raise Win32BackendError("GDI bitmap selection failed")
            if print_window:
                if not self.user32.PrintWindow(source_hwnd, mem_dc, PW_CLIENTONLY):
                    raise Win32BackendError("PrintWindow failed")
            elif not self.gdi32.BitBlt(mem_dc, 0, 0, w, h,
                                       source_dc, sx, sy, SRCCOPY):
                raise Win32BackendError("BitBlt failed")
            # GetDIBits requires the bitmap to be deselected from every DC.
            restored = self.gdi32.SelectObject(mem_dc, old)
            if not restored or restored == ctypes.c_void_p(-1).value:
                raise Win32BackendError("GDI bitmap deselection failed")
            old = None
            info = BITMAPINFO()
            info.bmiHeader = BITMAPINFOHEADER(
                ctypes.sizeof(BITMAPINFOHEADER), w, -h, 1, 32, BI_RGB,
                w * h * 4, 0, 0, 0, 0,
            )
            buffer = ctypes.create_string_buffer(w * h * 4)
            rows = self.gdi32.GetDIBits(mem_dc, bitmap, 0, h, buffer,
                                        ctypes.byref(info), DIB_RGB_COLORS)
            if rows != h:
                raise Win32BackendError("GetDIBits failed")
            return bytes(buffer.raw)
        finally:
            if old and mem_dc:
                self.gdi32.SelectObject(mem_dc, old)
            if bitmap:
                self.gdi32.DeleteObject(bitmap)
            if mem_dc:
                self.gdi32.DeleteDC(mem_dc)
            self.user32.ReleaseDC(source_hwnd, source_dc)

    def observe_read_only(self, target: str, frame: str, region) -> dict[str, Any]:
        # Validate binding without changing caller-owned input or recovery state.
        self._target(target)
        return self.capture(target, frame, *region)

    def configure_capture_artifacts(self, directory, *, retain_rgb=False) -> None:
        from .capture_artifacts import CaptureArtifacts
        self.capture_artifacts = CaptureArtifacts(directory, retain_rgb=retain_rgb)

    def capture_pixels(self, target: str, frame: str, x: int, y: int,
                w: int, h: int) -> bytes:
        if w <= 0 or h <= 0:
            raise Win32BackendError("capture dimensions must be positive")
        if frame == "window_client":
            hwnd = self._target(target)
            g = self.geometry(target)
            if x < 0 or y < 0 or x + w > g["width"] or y + h > g["height"]:
                raise Win32BackendError("capture outside client bounds")
            full = self._capture_hdc(hwnd, 0, 0, g["width"], g["height"],
                                     print_window=True)
            stride = g["width"] * 4
            raw = b"".join(
                full[(y + row) * stride + x * 4:
                     (y + row) * stride + (x + w) * 4]
                for row in range(h)
            )
        elif frame == "screen_physical_px":
            raw = self._capture_hdc(0, x, y, w, h, print_window=False)
        else:
            raise Win32BackendError(f"unsupported capture frame {frame}")
        return raw


    def capture(self, target: str, frame: str, x: int, y: int,
                w: int, h: int) -> dict[str, Any]:
        started_ns = time.monotonic_ns()
        raw = self.capture_pixels(target, frame, x, y, w, h)
        ended_ns = time.monotonic_ns()
        row = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
               "width": w, "height": h}
        artifacts = getattr(self, "capture_artifacts", None)
        if artifacts is not None:
            row.update(target=target, native_window_id=self.targets[target],
                       frame=frame, region=[x, y, w, h],
                       capture_started_ns=started_ns, capture_ended_ns=ended_ns)
            try:
                row["artifact"] = artifacts.write(raw, w, h)
            except Exception as error:
                # Keep the capture result even when PNG presentation fails.
                row["artifact_error"] = repr(error)
        return row

    def preflight(self, program: dict[str, Any], *, bound_target=None, guard=None) -> None:
        if bound_target is not None:
            if not callable(guard) or guard() is not True:
                raise Win32BackendError("bound execution guard refused")
            self._target(bound_target)
            if any(op["op"] in {"focus", "activate"} for op in program["ops"]):
                raise Win32BackendError("bound execution forbids focus changes")
        current_target: str | None = bound_target
        for op in program["ops"]:
            kind = op["op"]
            if kind == "focus":
                self._target(op["target"])
                current_target = op["target"]
            elif kind in {"pointer_move", "observe"}:
                if current_target is None:
                    raise Win32BackendError(f"{kind} requires focused target")
                if op["frame"] not in {"screen_physical_px", "window_client"}:
                    raise Win32BackendError(f"unsupported frame {op['frame']}")
                if kind == "observe" and op["frame"] == "window_client":
                    g = self.geometry(current_target)
                    if (op["x"] < 0 or op["y"] < 0 or
                            op["x"] + op["w"] > g["width"] or
                            op["y"] + op["h"] > g["height"]):
                        raise Win32BackendError("capture outside client bounds")
            elif kind == "text":
                utf16_units(op["text"])
            elif kind == "key_chord":
                encoding = op.get("encoding")
                if encoding not in {None, "virtual_key", "scan_code"}:
                    raise Win32BackendError(f"unsupported key encoding {encoding!r}")
                for key in op["keys"]:
                    vk = virtual_key(key)
                    if encoding == "scan_code":
                        mapped = int(self.user32.MapVirtualKeyW(vk, MAPVK_VK_TO_VSC_EX))
                        if not (mapped & 0xFF):
                            raise Win32BackendError(f"key {key} has no scan code")
            elif kind == "key_state":
                encoding = op.get("encoding")
                if encoding not in {None, "virtual_key", "scan_code"}:
                    raise Win32BackendError(f"unsupported key encoding {encoding!r}")
                vk = virtual_key(op["key"])
                if encoding == "scan_code":
                    mapped = int(self.user32.MapVirtualKeyW(vk, MAPVK_VK_TO_VSC_EX))
                    if not (mapped & 0xFF):
                        raise Win32BackendError(f"key {op['key']} has no scan code")
            elif kind == "pointer_button" and op["button"] not in BUTTON_FLAGS:
                raise Win32BackendError(f"unsupported button {op['button']}")

    def release_all(self) -> dict[str, Any]:
        # Compensate unmatched Unicode delivery once; failure retains the unit.
        # This acknowledges UP insertion, not physical or application state.
        unicode_error = None
        for unit in sorted(getattr(self, "pending_unicode_ups", ())):
            try:
                self._send_unicode_unit(unit, False)
            except Exception as error:
                unicode_error = unicode_error or error
            else:
                self.pending_unicode_ups.remove(unit)
        tracked_keys = dict(self.held_keys)
        tracked_buttons = set(self.held_buttons)
        target_sets: dict[int, set[str | None]] = {}
        key_targets = getattr(self, "held_key_targets", {})
        key_encodings = getattr(self, "held_key_encodings", {})
        button_targets = getattr(self, "held_button_targets", {})
        for name, vk in tracked_keys.items():
            target_sets.setdefault(vk, set()).add(key_targets.get(name))
        for button in tracked_buttons:
            target_sets.setdefault(BUTTON_FLAGS[button][2], set()).add(
                button_targets.get(button))
        sent_key_ups = set()
        for name, vk in tracked_keys.items():
            encoding = key_encodings.get(name)
            marker = (vk, encoding)
            if marker in sent_key_ups:
                continue
            sent_key_ups.add(marker)
            if encoding is None:
                self._send_key(vk, False)
            else:
                self._send_key(vk, False, encoding)
        for button in list(self.held_buttons):
            _, up_flag, _ = BUTTON_FLAGS[button]
            item = INPUT(type=INPUT_MOUSE)
            item.mi = MOUSEINPUT(0, 0, 0, up_flag, 0, 0)
            self._send(item)
        time.sleep(0.01)
        # Aliases share one sample: querying the same VK twice can consume the
        # unreliable legacy low bit and create an artificial zero ambiguity.
        state_targets = {vk: next(iter(targets)) if len(targets) == 1 else None
                         for vk, targets in target_sets.items()}
        states = {}
        button_states = {}
        state_witnesses = {}
        for vk in sorted(set(tracked_keys.values())):
            states[vk] = self._key_down_state(vk, state_targets.get(vk))
            if self._last_state_query_witness:
                state_witnesses[str(vk)] = self._last_state_query_witness
        for button in tracked_buttons:
            vk = BUTTON_FLAGS[button][2]
            button_states[button] = self._key_down_state(vk, state_targets.get(vk))
            if self._last_state_query_witness:
                state_witnesses[str(vk)] = self._last_state_query_witness
        keys = sorted(name for name, vk in tracked_keys.items() if states[vk] is True)
        buttons = sorted(button for button in tracked_buttons if button_states[button] is True)
        unknown_keys = sorted(name for name, vk in tracked_keys.items() if states[vk] is None)
        unknown_buttons = sorted(button for button in tracked_buttons if button_states[button] is None)
        # A sent UP is not neutral-state evidence. Keep unverified obligations;
        # an incomplete state read leaves the entire previous ledger intact.
        if unicode_error is not None:
            raise unicode_error
        for name in tracked_keys:
            if states[tracked_keys[name]] is False:
                self.held_keys.pop(name, None)
                getattr(self, "held_key_encodings", {}).pop(name, None)
                getattr(self, "held_key_targets", {}).pop(name, None)
        self.held_buttons.difference_update(button for button in tracked_buttons
                                            if button_states[button] is False)
        for button in tracked_buttons:
            if button_states[button] is False:
                getattr(self, "held_button_targets", {}).pop(button, None)
        return {"keys_down": keys, "buttons_down": buttons,
                "keys_unknown": unknown_keys, "buttons_unknown": unknown_buttons,
                "state_query_witnesses": state_witnesses,
                "verified": not keys and not buttons and not unknown_keys and not unknown_buttons,
                "monotonic_ns": time.monotonic_ns()}

    def execute(self, program: dict[str, Any], *, bound_target=None, guard=None, preflight_guard=None) -> dict[str, Any]:
        if bound_target is None:
            self.preflight(program)
        else:
            self.preflight(program, bound_target=bound_target, guard=guard if preflight_guard is None else preflight_guard)
        source = program.get("source")
        source = source if isinstance(source, dict) else {}
        expected_generations = source.get("target_generations")
        expected_generations = expected_generations if isinstance(expected_generations, dict) else {}

        def check_target_generation(target):
            if not isinstance(target, str) or target not in expected_generations:
                return
            reader = getattr(self, "target_generation", None)
            if not callable(reader):
                raise Win32BackendError("TARGET_GENERATION_UNAVAILABLE")
            if reader(target) != expected_generations[target]:
                raise Win32BackendError("TARGET_GENERATION_CHANGED")

        current_target: str | None = bound_target
        observations: list[dict[str, Any]] = []
        releases: list[dict[str, Any]] = []
        started = time.monotonic_ns()
        try:
            for op in program["ops"]:
                kind = op["op"]
                if bound_target is not None and kind != "release_all" and guard() is not True:
                    raise Win32BackendError("bound execution guard refused before operation")
                if kind == "focus":
                    next_target = op["target"]
                    check_target_generation(next_target)
                    self.focus(next_target)
                    current_target = next_target
                    # Focus is a visible side effect; pin the same HWND owner
                    # again before any later input can reach the foreground.
                    check_target_generation(current_target)
                elif kind == "key_chord":
                    check_target_generation(current_target)
                    self.key_chord(op["keys"], encoding=op["encoding"]) if "encoding" in op else self.key_chord(op["keys"])
                elif kind == "key_state":
                    check_target_generation(current_target)
                    self.key_state(op["key"], op["down"], encoding=op["encoding"]) if "encoding" in op else self.key_state(op["key"], op["down"])
                elif kind == "text":
                    check_target_generation(current_target)
                    self.text(op["text"])
                elif kind == "pointer_move":
                    if current_target is None:
                        raise Win32BackendError("pointer_move requires focused target")
                    check_target_generation(current_target)
                    self.pointer_move(current_target, op["frame"], op["x"], op["y"])
                elif kind == "pointer_button":
                    check_target_generation(current_target)
                    if op["down"] is True:
                        if current_target is None:
                            raise Win32BackendError(
                                "pointer_button down requires focused target")
                        self._require_pointer_target(current_target)
                    self.pointer_button(op["button"], op["down"])
                elif kind == "scroll":
                    check_target_generation(current_target)
                    if current_target is None:
                        raise Win32BackendError(
                            "scroll requires focused target")
                    self._require_pointer_target(current_target)
                    self.scroll(op["dx"], op["dy"])
                elif kind == "observe":
                    if current_target is None:
                        raise Win32BackendError("observe requires focused target")
                    check_target_generation(current_target)
                    observations.append(self.capture(
                        current_target, op["frame"], op["x"], op["y"],
                        op["w"], op["h"],
                    ))
                elif kind == "wait_update":
                    time.sleep(op["timeout_ms"] / 1000.0)
                elif kind == "verify":
                    pass
                elif kind == "release_all":
                    releases.append(self.release_all())
                else:
                    raise Win32BackendError(f"unsupported op {kind}")
        except Exception as error:
            try:
                release = self.release_all()
            except Exception as cleanup_error:
                if isinstance(error, Win32BackendError):
                    raise Win32ExecutionError(
                        error, None, {"type": type(cleanup_error).__name__,
                                      "detail": str(cleanup_error)}
                    ) from error
                raise
            releases.append(release)
            if isinstance(error, Win32BackendError):
                raise Win32ExecutionError(error, release, None) from error
            raise
        return {"started_ns": started, "ended_ns": time.monotonic_ns(),
                "emissions": self.emissions, "observations": observations,
                "releases": releases}
