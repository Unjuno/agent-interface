"""One-shot bounded WH_KEYBOARD_LL / SendInput delay probe for Windows."""
from __future__ import annotations

import ctypes
import json
import os
import pathlib
import threading
import time
import traceback

ROOT = pathlib.Path(__file__).resolve().parent
RAW = ROOT / "raw.json"
VK_F13 = 0x7C
WH_KEYBOARD_LL = 13
WM_KEYDOWN, WM_KEYUP = 0x0100, 0x0101
LLKHF_INJECTED = 0x10
BLOCK_NS = 50_000_000
LRESULT = ctypes.c_ssize_t
ULONG_PTR = ctypes.c_size_t

class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", ctypes.c_uint32), ("scanCode", ctypes.c_uint32),
                ("flags", ctypes.c_uint32), ("time", ctypes.c_uint32),
                ("dwExtraInfo", ULONG_PTR)]

HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, ctypes.c_size_t,
                              ctypes.c_ssize_t)

def main() -> int:
    if os.name != "nt":
        raise SystemExit("Windows required")
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, ctypes.c_void_p,
                                         ctypes.c_uint32]
    user32.SetWindowsHookExW.restype = ctypes.c_void_p
    user32.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                      ctypes.c_size_t, ctypes.c_ssize_t]
    user32.CallNextHookEx.restype = LRESULT
    user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
    user32.UnhookWindowsHookEx.restype = ctypes.c_int
    user32.GetMessageW.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                   ctypes.c_uint, ctypes.c_uint]
    user32.GetMessageW.restype = ctypes.c_int
    user32.PeekMessageW.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                    ctypes.c_uint, ctypes.c_uint, ctypes.c_uint]
    user32.PostThreadMessageW.argtypes = [ctypes.c_uint32, ctypes.c_uint,
                                          ctypes.c_size_t, ctypes.c_ssize_t]
    user32.SendInput.argtypes = [ctypes.c_uint, ctypes.c_void_p, ctypes.c_int]
    user32.SendInput.restype = ctypes.c_uint
    user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
    user32.GetAsyncKeyState.restype = ctypes.c_short
    kernel32.GetCurrentThreadId.restype = ctypes.c_uint32

    raw = {"packet": ROOT.name, "started_ns": time.perf_counter_ns(),
           "pid": os.getpid(), "python": os.sys.version,
           "events": [], "errors": [], "cleanup": {}}
    ready, stop_block = threading.Event(), threading.Event()
    hook_data: dict[str, object] = {"thread_id": None, "handle": None}
    block_used = False
    injected_down_attempted = False

    def key_state() -> dict[str, object]:
        value = int(user32.GetAsyncKeyState(VK_F13))
        return {"raw": value, "down": bool(value & 0x8000)}

    def send(down: bool) -> dict[str, object]:
        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [("wVk", ctypes.c_uint16), ("wScan", ctypes.c_uint16),
                        ("dwFlags", ctypes.c_uint32), ("time", ctypes.c_uint32),
                        ("dwExtraInfo", ULONG_PTR)]
        class INPUT_UNION(ctypes.Union):
            _fields_ = [("ki", KEYBDINPUT), ("padding", ctypes.c_byte * 32)]
        class INPUT(ctypes.Structure):
            _anonymous_ = ("u",)
            _fields_ = [("type", ctypes.c_uint32), ("u", INPUT_UNION)]
        item = INPUT()
        item.type = 1
        item.ki = KEYBDINPUT(VK_F13, 0, 0x0002 if not down else 0, 0, 0)
        began = time.perf_counter_ns()
        sent = int(user32.SendInput(1, ctypes.byref(item), ctypes.sizeof(INPUT)))
        ended = time.perf_counter_ns()
        return {"kind": "down" if down else "up", "entry_ns": began,
                "return_ns": ended, "duration_ns": ended - began,
                "sent": sent, "last_error": ctypes.get_last_error(),
                "input_size": ctypes.sizeof(INPUT)}

    def hook_thread() -> None:
        nonlocal block_used
        msg = ctypes.create_string_buffer(48)
        user32.PeekMessageW(msg, None, 0, 0, 0)
        hook_data["thread_id"] = int(kernel32.GetCurrentThreadId())

        @HOOKPROC
        def callback(code, wparam, lparam):
            nonlocal block_used
            entry = time.perf_counter_ns()
            event = ctypes.cast(lparam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            vk, flags = int(event.vkCode), int(event.flags)
            if code >= 0 and vk == VK_F13 and (flags & LLKHF_INJECTED):
                name = "down" if wparam == WM_KEYDOWN else "up" if wparam == WM_KEYUP else f"wm_{wparam}"
                row = {"kind": name, "vk": vk, "flags": flags,
                       "callback_entry_ns": entry, "callback_exit_ns": None,
                       "blocked_ns": 0}
                raw["events"].append(row)
                if name == "down" and not block_used:
                    block_used = True
                    before_wait = time.perf_counter_ns()
                    # Fixed finite delay; release event cannot cancel this wait.
                    stop_block.wait(BLOCK_NS / 1_000_000_000)
                    row["blocked_ns"] = time.perf_counter_ns() - before_wait
                row["callback_exit_ns"] = time.perf_counter_ns()
            return user32.CallNextHookEx(hook_data["handle"], code, wparam, lparam)

        hook_data["callback"] = callback
        handle = user32.SetWindowsHookExW(WH_KEYBOARD_LL, callback, None, 0)
        if not handle:
            raw["errors"].append({"stage": "SetWindowsHookExW",
                                  "last_error": ctypes.get_last_error()})
            ready.set()
            return
        hook_data["handle"] = handle
        ready.set()
        while True:
            result = int(user32.GetMessageW(msg, None, 0, 0))
            if result <= 0:
                break

    thread = threading.Thread(target=hook_thread, name="bounded-low-level-hook",
                              daemon=True)
    thread.start()
    try:
        if not ready.wait(3.0):
            raw["errors"].append({"stage": "hook_ready_timeout"})
        else:
            raw["hook_thread_id"] = hook_data["thread_id"]
            raw["initial_f13"] = key_state()
            if hook_data.get("handle") and raw["initial_f13"]["down"] is False:
                injected_down_attempted = True
                raw["send_down"] = send(True)
                # Allow callback return and the queued event to reach its target.
                deadline = time.perf_counter() + 1.0
                while time.perf_counter() < deadline and not any(
                        row["kind"] == "down" and row["callback_exit_ns"] is not None
                        for row in raw["events"]):
                    time.sleep(0.001)
                raw["send_up"] = send(False)
                deadline = time.perf_counter() + 1.0
                while time.perf_counter() < deadline and not any(
                        row["kind"] == "up" for row in raw["events"]):
                    time.sleep(0.001)
                raw["final_f13"] = key_state()
            elif not hook_data.get("handle"):
                raw["errors"].append({"stage": "hook_not_installed"})
            else:
                raw["errors"].append({"stage": "initial_f13_not_up"})
    except BaseException:
        raw["errors"].append({"stage": "runner_exception", "traceback": traceback.format_exc()})
    finally:
        if injected_down_attempted and "send_up" not in raw:
            try:
                raw["cleanup"]["emergency_up"] = send(False)
            except BaseException:
                raw["errors"].append({"stage": "emergency_up_exception",
                                      "traceback": traceback.format_exc()})
        handle = hook_data.get("handle")
        raw["cleanup"]["unhook_ok"] = (bool(user32.UnhookWindowsHookEx(handle))
                                        if handle else None)
        tid = hook_data.get("thread_id")
        raw["cleanup"]["quit_posted"] = (bool(user32.PostThreadMessageW(tid, 0x0012, 0, 0))
                                           if tid else None)
        thread.join(2.0)
        raw["cleanup"]["thread_exited"] = not thread.is_alive()
        raw["finished_ns"] = time.perf_counter_ns()
        try:
            with RAW.open("x", encoding="utf-8", newline="\n") as stream:
                json.dump(raw, stream, indent=2, sort_keys=True)
                stream.write("\n")
        except FileExistsError:
            raise SystemExit("raw.json already exists; refusing overwrite")
    print(json.dumps(raw, indent=2, sort_keys=True))
    return 0 if not raw["errors"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
