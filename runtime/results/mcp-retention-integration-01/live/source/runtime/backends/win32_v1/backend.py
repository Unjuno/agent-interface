"""Win32 implementation candidate for the Agent Interface runtime core v1 backend.

The semantic core remains platform neutral. This module owns only Win32-native
translation, preflight, effect emission, capture, and terminal release checks.
"""
from __future__ import annotations

import ctypes
import hashlib
import sys
import time
from ctypes import wintypes
from typing import Any

from runtime.core_v1.contract import OFFICE_FLOOR, capability_manifest, validate_backend_manifest


class Win32BackendError(RuntimeError):
    pass


SW_RESTORE = 9
PW_CLIENTONLY = 0x00000001
SRCCOPY = 0x00CC0020
DIB_RGB_COLORS = 0
BI_RGB = 0
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
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

KEY_ALIASES = {
    "CTRL": VK_CONTROL, "CONTROL": VK_CONTROL, "SHIFT": VK_SHIFT,
    "ALT": VK_MENU, "ENTER": VK_RETURN, "RETURN": VK_RETURN,
    "TAB": VK_TAB, "ESC": VK_ESCAPE, "ESCAPE": VK_ESCAPE,
    "SPACE": VK_SPACE, "BACKSPACE": VK_BACK, "DELETE": VK_DELETE,
    "LEFT": VK_LEFT, "RIGHT": VK_RIGHT, "UP": VK_UP, "DOWN": VK_DOWN,
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
        self.held_buttons: set[str] = set()
        self.emissions = 0

    def _configure_api(self) -> None:
        self.user32.IsWindow.argtypes = [wintypes.HWND]
        self.user32.IsWindow.restype = wintypes.BOOL
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
        self.user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
        self.user32.SetCursorPos.restype = wintypes.BOOL
        self.user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
        self.user32.SendInput.restype = wintypes.UINT
        self.user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
        self.user32.GetAsyncKeyState.restype = wintypes.SHORT
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
        self.user32.SetForegroundWindow(hwnd)
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            if int(self.user32.GetForegroundWindow() or 0) == hwnd:
                return
            time.sleep(0.01)
        raise Win32BackendError("foreground focus verification failed")

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

    def _send_key(self, vk: int, down: bool) -> None:
        item = INPUT(type=INPUT_KEYBOARD)
        item.ki = KEYBDINPUT(vk, 0, 0 if down else KEYEVENTF_KEYUP, 0, 0)
        self._send(item)

    def _send_unicode_unit(self, unit: int, down: bool) -> None:
        item = INPUT(type=INPUT_KEYBOARD)
        flags = KEYEVENTF_UNICODE | (0 if down else KEYEVENTF_KEYUP)
        item.ki = KEYBDINPUT(0, unit, flags, 0, 0)
        self._send(item)

    def key_state(self, key: str, down: bool) -> None:
        vk = virtual_key(key)
        self._send_key(vk, down)
        if down:
            self.held_keys[key] = vk
        else:
            self.held_keys.pop(key, None)

    def key_chord(self, keys: list[str]) -> None:
        for key in keys:
            self.key_state(key, True)
        for key in reversed(keys):
            self.key_state(key, False)

    def text(self, value: str) -> None:
        for unit in utf16_units(value):
            self._send_unicode_unit(unit, True)
            self._send_unicode_unit(unit, False)

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
        else:
            self.held_buttons.discard(button)

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
            if print_window:
                if not self.user32.PrintWindow(source_hwnd, mem_dc, PW_CLIENTONLY):
                    raise Win32BackendError("PrintWindow failed")
            elif not self.gdi32.BitBlt(mem_dc, 0, 0, w, h,
                                       source_dc, sx, sy, SRCCOPY):
                raise Win32BackendError("BitBlt failed")
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

    def capture(self, target: str, frame: str, x: int, y: int,
                w: int, h: int) -> dict[str, Any]:
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
        return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                "width": w, "height": h}

    def preflight(self, program: dict[str, Any]) -> None:
        current_target: str | None = None
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
                for key in op["keys"]:
                    virtual_key(key)
            elif kind == "key_state":
                virtual_key(op["key"])
            elif kind == "pointer_button" and op["button"] not in BUTTON_FLAGS:
                raise Win32BackendError(f"unsupported button {op['button']}")

    def release_all(self) -> dict[str, Any]:
        tracked_keys = dict(self.held_keys)
        tracked_buttons = set(self.held_buttons)
        for vk in list(self.held_keys.values()):
            self._send_key(vk, False)
        for button in list(self.held_buttons):
            _, up_flag, _ = BUTTON_FLAGS[button]
            item = INPUT(type=INPUT_MOUSE)
            item.mi = MOUSEINPUT(0, 0, 0, up_flag, 0, 0)
            self._send(item)
        self.held_keys.clear()
        self.held_buttons.clear()
        time.sleep(0.01)
        keys = sorted(name for name, vk in tracked_keys.items()
                      if self.user32.GetAsyncKeyState(vk) & 0x8000)
        buttons = sorted(button for button in tracked_buttons
                         if self.user32.GetAsyncKeyState(BUTTON_FLAGS[button][2]) & 0x8000)
        return {"keys_down": keys, "buttons_down": buttons,
                "verified": not keys and not buttons,
                "monotonic_ns": time.monotonic_ns()}

    def execute(self, program: dict[str, Any]) -> dict[str, Any]:
        self.preflight(program)
        current_target: str | None = None
        observations: list[dict[str, Any]] = []
        releases: list[dict[str, Any]] = []
        started = time.monotonic_ns()
        try:
            for op in program["ops"]:
                kind = op["op"]
                if kind == "focus":
                    current_target = op["target"]
                    self.focus(current_target)
                elif kind == "key_chord":
                    self.key_chord(op["keys"])
                elif kind == "key_state":
                    self.key_state(op["key"], op["down"])
                elif kind == "text":
                    self.text(op["text"])
                elif kind == "pointer_move":
                    if current_target is None:
                        raise Win32BackendError("pointer_move requires focused target")
                    self.pointer_move(current_target, op["frame"], op["x"], op["y"])
                elif kind == "pointer_button":
                    self.pointer_button(op["button"], op["down"])
                elif kind == "scroll":
                    self.scroll(op["dx"], op["dy"])
                elif kind == "observe":
                    if current_target is None:
                        raise Win32BackendError("observe requires focused target")
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
        except Exception:
            releases.append(self.release_all())
            raise
        return {"started_ns": started, "ended_ns": time.monotonic_ns(),
                "emissions": self.emissions, "observations": observations,
                "releases": releases}
