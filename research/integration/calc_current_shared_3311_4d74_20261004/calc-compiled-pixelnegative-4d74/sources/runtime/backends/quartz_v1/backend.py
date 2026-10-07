"""Quartz/ApplicationServices backend candidate for runtime core v1."""
from __future__ import annotations

import ctypes
import hashlib
import os
import sys
import time
from typing import Any

from runtime.core_v1.contract import (
    OFFICE_FLOOR, CAPTURE_FRAME, INPUT_KEYBOARD, INPUT_TEXT, INPUT_POINTER,
    INPUT_SCROLL, INPUT_RELEASE_ALL, WINDOW_FOCUS, capability_manifest,
    validate_backend_manifest,
)


class QuartzBackendError(RuntimeError):
    pass


class CGPoint(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]


class CGSize(ctypes.Structure):
    _fields_ = [("width", ctypes.c_double), ("height", ctypes.c_double)]


class CGRect(ctypes.Structure):
    _fields_ = [("origin", CGPoint), ("size", CGSize)]


KEY_CODES = {
    "A": 0, "S": 1, "D": 2, "F": 3, "H": 4, "G": 5, "Z": 6,
    "X": 7, "C": 8, "V": 9, "B": 11, "Q": 12, "W": 13, "E": 14,
    "R": 15, "Y": 16, "T": 17, "1": 18, "2": 19, "3": 20,
    "4": 21, "6": 22, "5": 23, "9": 25, "7": 26, "8": 28,
    "0": 29, "O": 31, "U": 32, "I": 34, "P": 35, "ENTER": 36,
    "RETURN": 36, "L": 37, "J": 38, "K": 40, "N": 45, "M": 46,
    "TAB": 48, "SPACE": 49, "BACKSPACE": 51, "ESC": 53, "ESCAPE": 53,
    "SHIFT": 56, "ALT": 58, "OPTION": 58, "CTRL": 59, "CONTROL": 59,
}

KCG_HID_EVENT_TAP = 0
KCG_EVENT_LEFT_MOUSE_DOWN = 1
KCG_EVENT_LEFT_MOUSE_UP = 2
KCG_EVENT_RIGHT_MOUSE_DOWN = 3
KCG_EVENT_RIGHT_MOUSE_UP = 4
KCG_EVENT_MOUSE_MOVED = 5
KCG_EVENT_SCROLL_WHEEL = 22
KCG_EVENT_OTHER_MOUSE_DOWN = 25
KCG_EVENT_OTHER_MOUSE_UP = 26
KCG_MOUSE_BUTTON_LEFT = 0
KCG_MOUSE_BUTTON_RIGHT = 1
KCG_MOUSE_BUTTON_CENTER = 2
KCG_EVENT_SOURCE_STATE_COMBINED_SESSION = 0
KCG_SCROLL_EVENT_UNIT_LINE = 1
KCF_STRING_ENCODING_UTF8 = 0x08000100

BUTTONS = {
    "left": (KCG_MOUSE_BUTTON_LEFT, KCG_EVENT_LEFT_MOUSE_DOWN, KCG_EVENT_LEFT_MOUSE_UP),
    "right": (KCG_MOUSE_BUTTON_RIGHT, KCG_EVENT_RIGHT_MOUSE_DOWN, KCG_EVENT_RIGHT_MOUSE_UP),
    "middle": (KCG_MOUSE_BUTTON_CENTER, KCG_EVENT_OTHER_MOUSE_DOWN, KCG_EVENT_OTHER_MOUSE_UP),
}


def utf16_units(value: str) -> tuple[int, ...]:
    if not isinstance(value, str):
        raise QuartzBackendError("text must be str")
    if any(0xD800 <= ord(ch) <= 0xDFFF for ch in value):
        raise QuartzBackendError("text contains explicit surrogate code point")
    raw = value.encode("utf-16-le", "strict")
    return tuple(int.from_bytes(raw[i:i + 2], "little") for i in range(0, len(raw), 2))


def key_code(key: str) -> int:
    if not isinstance(key, str) or not key:
        raise QuartzBackendError("invalid key")
    upper = key.upper()
    if upper in KEY_CODES:
        return KEY_CODES[upper]
    raise QuartzBackendError(f"unmapped key {key}")


def manifest_for_permissions(accessibility: bool, screen_recording: bool) -> dict[str, Any]:
    supported = set(OFFICE_FLOOR)
    permission_required: set[str] = set()
    if not accessibility:
        gated = {INPUT_KEYBOARD, INPUT_TEXT, INPUT_POINTER, INPUT_SCROLL,
                 INPUT_RELEASE_ALL, WINDOW_FOCUS}
        supported -= gated
        permission_required |= gated
    if not screen_recording:
        supported.discard(CAPTURE_FRAME)
        permission_required.add(CAPTURE_FRAME)
    row = capability_manifest(
        "quartz-v1", "macos", "quartz", supported,
        permission_required=permission_required,
        frames=("screen_physical_px",),
        permissions=(
            f"accessibility:{'granted' if accessibility else 'required'}",
            f"screen-recording:{'granted' if screen_recording else 'required'}",
        ),
    )
    row["capabilities"]["input.text"]["detail"] = (
        "CGEvent Unicode; explicit surrogate code points rejected"
    )
    return validate_backend_manifest(row)


class QuartzBackend:
    def __init__(self, targets: dict[str, int]):
        if sys.platform != "darwin":
            raise QuartzBackendError("Quartz backend requires macOS")
        self.cg = ctypes.CDLL("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
        self.ax = ctypes.CDLL("/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices")
        self.cf = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
        self._configure_api()
        self.targets = {name: int(pid) for name, pid in targets.items()}
        for name, pid in self.targets.items():
            if not self._pid_alive(pid):
                raise QuartzBackendError(f"invalid PID for target {name}")
        self.accessibility_granted = bool(self.ax.AXIsProcessTrusted())
        self.screen_recording_granted = bool(self.cg.CGPreflightScreenCaptureAccess())
        self.held_keys: dict[str, int] = {}
        self.held_buttons: set[str] = set()
        self.emissions = 0

    def _configure_api(self) -> None:
        self.ax.AXIsProcessTrusted.restype = ctypes.c_bool
        self.ax.AXUIElementCreateApplication.argtypes = [ctypes.c_int]
        self.ax.AXUIElementCreateApplication.restype = ctypes.c_void_p
        self.ax.AXUIElementSetAttributeValue.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        self.ax.AXUIElementSetAttributeValue.restype = ctypes.c_int
        self.ax.AXUIElementCopyAttributeValue.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
        self.ax.AXUIElementCopyAttributeValue.restype = ctypes.c_int
        self.cf.CFStringCreateWithCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32]
        self.cf.CFStringCreateWithCString.restype = ctypes.c_void_p
        self.cf.CFRelease.argtypes = [ctypes.c_void_p]
        self.cf.CFBooleanGetValue.argtypes = [ctypes.c_void_p]
        self.cf.CFBooleanGetValue.restype = ctypes.c_bool
        self.cf.CFDataGetLength.argtypes = [ctypes.c_void_p]
        self.cf.CFDataGetLength.restype = ctypes.c_long
        self.cf.CFDataGetBytePtr.argtypes = [ctypes.c_void_p]
        self.cf.CFDataGetBytePtr.restype = ctypes.POINTER(ctypes.c_ubyte)

        self.cg.CGPreflightScreenCaptureAccess.restype = ctypes.c_bool
        self.cg.CGMainDisplayID.restype = ctypes.c_uint32
        self.cg.CGDisplayBounds.argtypes = [ctypes.c_uint32]
        self.cg.CGDisplayBounds.restype = CGRect
        self.cg.CGDisplayCreateImageForRect.argtypes = [ctypes.c_uint32, CGRect]
        self.cg.CGDisplayCreateImageForRect.restype = ctypes.c_void_p
        self.cg.CGImageGetWidth.argtypes = [ctypes.c_void_p]
        self.cg.CGImageGetWidth.restype = ctypes.c_size_t
        self.cg.CGImageGetHeight.argtypes = [ctypes.c_void_p]
        self.cg.CGImageGetHeight.restype = ctypes.c_size_t
        self.cg.CGImageGetDataProvider.argtypes = [ctypes.c_void_p]
        self.cg.CGImageGetDataProvider.restype = ctypes.c_void_p
        self.cg.CGDataProviderCopyData.argtypes = [ctypes.c_void_p]
        self.cg.CGDataProviderCopyData.restype = ctypes.c_void_p
        self.cg.CGEventCreateKeyboardEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint16, ctypes.c_bool]
        self.cg.CGEventCreateKeyboardEvent.restype = ctypes.c_void_p
        self.cg.CGEventKeyboardSetUnicodeString.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(ctypes.c_uint16)]
        self.cg.CGEventPost.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
        self.cg.CGEventCreateMouseEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint32, CGPoint, ctypes.c_uint32]
        self.cg.CGEventCreateMouseEvent.restype = ctypes.c_void_p
        self.cg.CGEventCreate.argtypes = [ctypes.c_void_p]
        self.cg.CGEventCreate.restype = ctypes.c_void_p
        self.cg.CGEventGetLocation.argtypes = [ctypes.c_void_p]
        self.cg.CGEventGetLocation.restype = CGPoint
        self.cg.CGEventSourceKeyState.argtypes = [ctypes.c_int, ctypes.c_uint16]
        self.cg.CGEventSourceKeyState.restype = ctypes.c_bool
        self.cg.CGEventSourceButtonState.argtypes = [ctypes.c_int, ctypes.c_uint32]
        self.cg.CGEventSourceButtonState.restype = ctypes.c_bool
        self.cg.CGEventCreateScrollWheelEvent.restype = ctypes.c_void_p

    @staticmethod
    def _pid_alive(pid: int) -> bool:
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True

    def _target(self, name: str) -> int:
        pid = self.targets.get(name)
        if pid is None or not self._pid_alive(pid):
            raise QuartzBackendError(f"unknown or stale target {name}")
        return pid

    def manifest(self) -> dict[str, Any]:
        return manifest_for_permissions(self.accessibility_granted, self.screen_recording_granted)

    def monotonic_ns(self) -> int:
        return time.monotonic_ns()

    def display_bounds(self) -> dict[str, int]:
        display = self.cg.CGMainDisplayID()
        bounds = self.cg.CGDisplayBounds(display)
        return {"x": int(round(bounds.origin.x)), "y": int(round(bounds.origin.y)),
                "width": int(round(bounds.size.width)), "height": int(round(bounds.size.height))}

    def focus(self, target: str) -> None:
        pid = self._target(target)
        app = self.ax.AXUIElementCreateApplication(pid)
        if not app:
            raise QuartzBackendError("AXUIElementCreateApplication failed")
        attr = self.cf.CFStringCreateWithCString(None, b"AXFrontmost", KCF_STRING_ENCODING_UTF8)
        try:
            true_ref = ctypes.c_void_p.in_dll(self.cf, "kCFBooleanTrue").value
            error = self.ax.AXUIElementSetAttributeValue(app, attr, true_ref)
            if error != 0:
                raise QuartzBackendError(f"AXFrontmost set failed error={error}")
            deadline = time.monotonic() + 1.0
            while time.monotonic() < deadline:
                value = ctypes.c_void_p()
                error = self.ax.AXUIElementCopyAttributeValue(app, attr, ctypes.byref(value))
                if error == 0 and value.value:
                    try:
                        if self.cf.CFBooleanGetValue(value):
                            return
                    finally:
                        self.cf.CFRelease(value)
                time.sleep(0.02)
            raise QuartzBackendError("AXFrontmost verification failed")
        finally:
            if attr:
                self.cf.CFRelease(attr)
            self.cf.CFRelease(app)

    def _post(self, event: int) -> None:
        if not event:
            raise QuartzBackendError("CGEvent creation failed")
        try:
            self.cg.CGEventPost(KCG_HID_EVENT_TAP, event)
            self.emissions += 1
        finally:
            self.cf.CFRelease(event)

    def key_state(self, key: str, down: bool) -> None:
        code = key_code(key)
        self._post(self.cg.CGEventCreateKeyboardEvent(None, code, down))
        if down: self.held_keys[key] = code
        else: self.held_keys.pop(key, None)

    def key_chord(self, keys: list[str]) -> None:
        for key in keys: self.key_state(key, True)
        for key in reversed(keys): self.key_state(key, False)

    def text(self, value: str) -> None:
        for unit in utf16_units(value):
            buf = (ctypes.c_uint16 * 1)(unit)
            for down in (True, False):
                event = self.cg.CGEventCreateKeyboardEvent(None, 0, down)
                if not event: raise QuartzBackendError("keyboard event creation failed")
                self.cg.CGEventKeyboardSetUnicodeString(event, 1, buf)
                self._post(event)

    def pointer_position(self) -> tuple[int, int]:
        event = self.cg.CGEventCreate(None)
        if not event: raise QuartzBackendError("CGEventCreate failed")
        try:
            point = self.cg.CGEventGetLocation(event)
            return int(round(point.x)), int(round(point.y))
        finally: self.cf.CFRelease(event)

    def pointer_move(self, frame: str, x: int, y: int) -> None:
        if frame != "screen_physical_px": raise QuartzBackendError(f"unsupported frame {frame}")
        self._post(self.cg.CGEventCreateMouseEvent(None, KCG_EVENT_MOUSE_MOVED, CGPoint(x, y), KCG_MOUSE_BUTTON_LEFT))

    def pointer_button(self, button: str, down: bool) -> None:
        if button not in BUTTONS: raise QuartzBackendError(f"unsupported button {button}")
        number, down_type, up_type = BUTTONS[button]; x, y = self.pointer_position()
        self._post(self.cg.CGEventCreateMouseEvent(None, down_type if down else up_type, CGPoint(x, y), number))
        if down: self.held_buttons.add(button)
        else: self.held_buttons.discard(button)

    def scroll(self, dx: int, dy: int) -> None:
        self._post(self.cg.CGEventCreateScrollWheelEvent(None, KCG_SCROLL_EVENT_UNIT_LINE, 2, int(dy), int(dx)))

    def capture(self, frame: str, x: int, y: int, w: int, h: int) -> dict[str, Any]:
        if frame != "screen_physical_px": raise QuartzBackendError(f"unsupported capture frame {frame}")
        bounds = self.display_bounds()
        if w <= 0 or h <= 0 or x < bounds["x"] or y < bounds["y"] or x + w > bounds["x"] + bounds["width"] or y + h > bounds["y"] + bounds["height"]:
            raise QuartzBackendError("capture outside display bounds")
        image = self.cg.CGDisplayCreateImageForRect(self.cg.CGMainDisplayID(), CGRect(CGPoint(x, y), CGSize(w, h)))
        if not image: raise QuartzBackendError("screen capture returned no image")
        try:
            width = int(self.cg.CGImageGetWidth(image)); height = int(self.cg.CGImageGetHeight(image))
            provider = self.cg.CGImageGetDataProvider(image); data = self.cg.CGDataProviderCopyData(provider)
            if not data: raise QuartzBackendError("CGDataProviderCopyData failed")
            try:
                length = int(self.cf.CFDataGetLength(data)); raw = ctypes.string_at(self.cf.CFDataGetBytePtr(data), length)
            finally: self.cf.CFRelease(data)
        finally: self.cf.CFRelease(image)
        return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "width": width, "height": height}

    def preflight(self, program: dict[str, Any]) -> None:
        bounds = self.display_bounds()
        for op in program["ops"]:
            kind = op["op"]
            if kind == "focus": self._target(op["target"])
            elif kind in {"pointer_move", "observe"}:
                if op["frame"] != "screen_physical_px": raise QuartzBackendError(f"unsupported frame {op['frame']}")
                if kind == "observe" and (op["x"] < bounds["x"] or op["y"] < bounds["y"] or op["x"] + op["w"] > bounds["x"] + bounds["width"] or op["y"] + op["h"] > bounds["y"] + bounds["height"]): raise QuartzBackendError("capture outside display bounds")
            elif kind == "text": utf16_units(op["text"])
            elif kind == "key_chord":
                for key in op["keys"]: key_code(key)
            elif kind == "key_state": key_code(op["key"])
            elif kind == "pointer_button" and op["button"] not in BUTTONS: raise QuartzBackendError(f"unsupported button {op['button']}")

    def release_all(self) -> dict[str, Any]:
        tracked_keys = dict(self.held_keys); tracked_buttons = set(self.held_buttons)
        for code in list(self.held_keys.values()): self._post(self.cg.CGEventCreateKeyboardEvent(None, code, False))
        for button in list(self.held_buttons):
            number, _, up_type = BUTTONS[button]; x, y = self.pointer_position(); self._post(self.cg.CGEventCreateMouseEvent(None, up_type, CGPoint(x, y), number))
        self.held_keys.clear(); self.held_buttons.clear(); time.sleep(0.02)
        keys = sorted(name for name, code in tracked_keys.items() if self.cg.CGEventSourceKeyState(KCG_EVENT_SOURCE_STATE_COMBINED_SESSION, code))
        buttons = sorted(button for button in tracked_buttons if self.cg.CGEventSourceButtonState(KCG_EVENT_SOURCE_STATE_COMBINED_SESSION, BUTTONS[button][0]))
        return {"keys_down": keys, "buttons_down": buttons, "verified": not keys and not buttons, "monotonic_ns": time.monotonic_ns()}

    def execute(self, program: dict[str, Any]) -> dict[str, Any]:
        self.preflight(program); observations=[]; releases=[]; started=time.monotonic_ns()
        try:
            for op in program["ops"]:
                kind=op["op"]
                if kind=="focus": self.focus(op["target"])
                elif kind=="key_chord": self.key_chord(op["keys"])
                elif kind=="key_state": self.key_state(op["key"],op["down"])
                elif kind=="text": self.text(op["text"])
                elif kind=="pointer_move": self.pointer_move(op["frame"],op["x"],op["y"])
                elif kind=="pointer_button": self.pointer_button(op["button"],op["down"])
                elif kind=="scroll": self.scroll(op["dx"],op["dy"])
                elif kind=="observe": observations.append(self.capture(op["frame"],op["x"],op["y"],op["w"],op["h"]))
                elif kind=="wait_update": time.sleep(op["timeout_ms"]/1000.0)
                elif kind=="verify": pass
                elif kind=="release_all": releases.append(self.release_all())
                else: raise QuartzBackendError(f"unsupported op {kind}")
        except Exception:
            releases.append(self.release_all()); raise
        return {"started_ns":started,"ended_ns":time.monotonic_ns(),"emissions":self.emissions,"observations":observations,"releases":releases}
