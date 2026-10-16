"""Small native Win32 fixture used only to score backend effects independently."""
from __future__ import annotations

import argparse
import ctypes
import json
import sys
from ctypes import wintypes
from pathlib import Path

if sys.platform != "win32":
    raise SystemExit("fixture requires Windows")

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

WM_DESTROY = 0x0002
WM_PAINT = 0x000F
WM_KEYDOWN = 0x0100
WM_CHAR = 0x0102
WM_LBUTTONDOWN = 0x0201
WM_PRINTCLIENT = 0x0318
VK_CONTROL = 0x11
VK_S = 0x53
WS_OVERLAPPEDWINDOW = 0x00CF0000
WS_VISIBLE = 0x10000000
SW_SHOW = 5
COLOR_WINDOW = 5

LRESULT = ctypes.c_ssize_t
WPARAM = ctypes.c_size_t
LPARAM = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, WPARAM, LPARAM)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE
user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, WPARAM, LPARAM]
user32.DefWindowProcW.restype = LRESULT
user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
user32.RegisterClassW.restype = wintypes.ATOM
user32.CreateWindowExW.argtypes = [
    wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.HWND,
    wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID,
]
user32.CreateWindowExW.restype = wintypes.HWND
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.UpdateWindow.argtypes = [wintypes.HWND]
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
user32.GetKeyState.argtypes = [ctypes.c_int]
user32.GetKeyState.restype = wintypes.SHORT
user32.GetDC.argtypes = [wintypes.HWND]
user32.GetDC.restype = wintypes.HDC
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
user32.ValidateRect.argtypes = [wintypes.HWND, ctypes.c_void_p]
gdi32.TextOutW.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, wintypes.LPCWSTR, ctypes.c_int]
gdi32.SetTextColor.argtypes = [wintypes.HDC, wintypes.COLORREF]
gdi32.SetBkColor.argtypes = [wintypes.HDC, wintypes.COLORREF]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--meta", required=True, type=Path)
    parser.add_argument("--effect", required=True, type=Path)
    parser.add_argument("--events", required=True, type=Path)
    args = parser.parse_args()
    args.meta.parent.mkdir(parents=True, exist_ok=True)
    state = {"text": "", "clicked": False}

    def event(kind: str, **payload) -> None:
        with args.events.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"kind": kind, **payload}, sort_keys=True) + "\n")

    def paint(dc) -> None:
        gdi32.SetBkColor(dc, 0x00F0F0F0)
        gdi32.SetTextColor(dc, 0x00000000)
        label = "Agent Interface Win32 fixture: " + state["text"]
        gdi32.TextOutW(dc, 16, 40, label, len(label))

    @WNDPROC
    def wndproc(hwnd, msg, wparam, lparam):
        if msg == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0
        if msg == WM_LBUTTONDOWN:
            state["clicked"] = True
            event("click")
            return 0
        if msg == WM_CHAR:
            code = int(wparam)
            if code == 8:
                state["text"] = state["text"][:-1]
            elif code >= 32:
                state["text"] += chr(code)
                event("char", code=code)
            user32.InvalidateRect(hwnd, None, True)
            return 0
        if msg == WM_KEYDOWN and int(wparam) == VK_S and user32.GetKeyState(VK_CONTROL) & 0x8000:
            result = {"saved": True, "text": state["text"], "clicked": bool(state["clicked"])}
            args.effect.write_text(json.dumps(result, sort_keys=True), encoding="utf-8")
            event("save", **result)
            return 0
        if msg == WM_PRINTCLIENT:
            paint(wintypes.HDC(int(wparam)))
            return 0
        if msg == WM_PAINT:
            dc = user32.GetDC(hwnd)
            if dc:
                paint(dc)
                user32.ReleaseDC(hwnd, dc)
            user32.ValidateRect(hwnd, None)
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    hinstance = kernel32.GetModuleHandleW(None)
    class_name = "AgentInterfaceWin32FixtureV1"
    wc = WNDCLASSW()
    wc.lpfnWndProc = wndproc
    wc.hInstance = hinstance
    wc.hbrBackground = ctypes.c_void_p(COLOR_WINDOW + 1)
    wc.lpszClassName = class_name
    atom = user32.RegisterClassW(ctypes.byref(wc))
    if not atom and ctypes.get_last_error() != 1410:
        raise OSError(ctypes.get_last_error(), "RegisterClassW")
    hwnd = user32.CreateWindowExW(
        0, class_name, "Agent Interface Win32 Fixture", WS_OVERLAPPEDWINDOW | WS_VISIBLE,
        80, 80, 420, 220, 0, 0, hinstance, None,
    )
    if not hwnd:
        raise OSError(ctypes.get_last_error(), "CreateWindowExW")
    user32.ShowWindow(hwnd, SW_SHOW)
    user32.UpdateWindow(hwnd)
    user32.SetForegroundWindow(hwnd)
    args.meta.write_text(json.dumps({"hwnd": int(hwnd), "width": 420, "height": 220}), encoding="utf-8")
    event("ready", hwnd=int(hwnd))

    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) > 0:
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
