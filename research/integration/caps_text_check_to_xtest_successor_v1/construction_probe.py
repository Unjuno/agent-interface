"""Excluded construction probe for the private Xvfb lock/XTEST boundary.

This is not a formal experiment runner. It deliberately performs one directed
state transition after a LockMask sample and before the first XTEST event.
"""
from __future__ import annotations

import ctypes
import json
import os
import sys
import time
import tkinter as tk

from Xlib import X, XK, display
from Xlib.ext import xtest


def set_caps_lock(display_name: str, enabled: bool) -> tuple[int, int]:
    lib = ctypes.CDLL("libX11.so.6")
    lib.XOpenDisplay.argtypes = [ctypes.c_char_p]
    lib.XOpenDisplay.restype = ctypes.c_void_p
    lib.XkbLockModifiers.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                                     ctypes.c_uint, ctypes.c_uint]
    lib.XkbLockModifiers.restype = ctypes.c_int
    lib.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.XCloseDisplay.argtypes = [ctypes.c_void_p]
    conn = lib.XOpenDisplay(display_name.encode())
    if not conn:
        raise RuntimeError("XOpenDisplay failed for lock actor")
    try:
        accepted = lib.XkbLockModifiers(
            conn, 0x100, X.LockMask, X.LockMask if enabled else 0
        )
        lib.XSync(conn, 0)
        observer = display.Display(display_name)
        try:
            mask = observer.screen().root.query_pointer().mask
        finally:
            observer.close()
        return int(accepted), int(bool(mask & X.LockMask))
    finally:
        lib.XCloseDisplay(conn)


def send_key(d: display.Display, key: str, shifted: bool = False) -> None:
    code = d.keysym_to_keycode(XK.string_to_keysym(key))
    shift = d.keysym_to_keycode(XK.string_to_keysym("Shift_L"))
    if shifted:
        xtest.fake_input(d, X.KeyPress, shift)
    xtest.fake_input(d, X.KeyPress, code)
    xtest.fake_input(d, X.KeyRelease, code)
    if shifted:
        xtest.fake_input(d, X.KeyRelease, shift)
    d.sync()


def main() -> int:
    interpose = len(sys.argv) == 2 and sys.argv[1] == "interpose"
    display_name = os.environ["DISPLAY"]
    set_caps_lock(display_name, False)

    root = tk.Tk()
    value = tk.StringVar()
    entry = tk.Entry(root, textvariable=value)
    entry.pack()
    events: list[dict[str, object]] = []
    entry.bind("<KeyPress>", lambda e: events.append(
        {"type": "press", "keysym": e.keysym, "char": e.char,
         "state": int(e.state)}
    ))
    entry.bind("<KeyRelease>", lambda e: events.append(
        {"type": "release", "keysym": e.keysym, "char": e.char,
         "state": int(e.state)}
    ))
    entry.focus_force()
    root.update()
    d = display.Display(display_name)
    root_window = d.screen().root
    sample = int(bool(root_window.query_pointer().mask & X.LockMask))
    if sample:
        raise RuntimeError("construction precondition failed: LockMask was ON")

    actor = None
    if interpose:
        actor = set_caps_lock(display_name, True)
        if actor[0] != 1 or actor[1] != 1:
            raise RuntimeError(f"lock actor did not establish ON: {actor}")

    # The transition above is synchronously acknowledged before this first
    # task XTEST event; no timing sleep is used to order the boundary.
    send_key(d, "a")
    send_key(d, "b", shifted=True)
    send_key(d, "2")
    root.update()
    time.sleep(0.15)
    root.update()
    actual = value.get()
    expected = "Ab2" if interpose else "aB2"
    final_mask = int(bool(root_window.query_pointer().mask & X.LockMask))
    keymap = d.query_keymap()
    held = [i for i in range(256)
            if keymap[i // 8] & (1 << (i % 8))]
    result = {
        "kind": "excluded-construction-only",
        "display": display_name,
        "interpose": interpose,
        "precheck_lock": sample,
        "actor_ack": actor,
        "post_lock": final_mask,
        "requested": "aB2",
        "actual": actual,
        "expected_for_arm": expected,
        "entry_events": events,
        "held_keycodes": held,
    }
    print(json.dumps(result, sort_keys=True))
    d.close()
    root.destroy()
    set_caps_lock(display_name, False)
    return 0 if actual == expected and not held else 1


if __name__ == "__main__":
    raise SystemExit(main())
