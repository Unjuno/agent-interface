"""Disposable XTEST receiver-oracle construction check; not formal evidence."""
from __future__ import annotations

import os
import subprocess
import time

from Xlib import X, XK, display
from Xlib.ext import xtest

import runner


def main():
    env = dict(os.environ)
    env["DISPLAY"] = ":229"
    os.environ["DISPLAY"] = env["DISPLAY"]
    proc = subprocess.Popen(["/usr/bin/Xvfb", env["DISPLAY"], "-screen", "0", "800x600x24",
                             "-nolisten", "tcp", "+extension", "XKEYBOARD", "+extension", "XTEST",
                             "-noreset"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    receiver = emitter = lookup = None
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                raise RuntimeError("Xvfb exited")
            try:
                receiver = display.Display(env["DISPLAY"])
                break
            except Exception:
                time.sleep(0.05)
        if receiver is None:
            raise RuntimeError("Xvfb connect timeout")
        win = receiver.screen().root.create_window(0, 0, 1, 1, 0, X.CopyFromParent,
            X.InputOnly, X.CopyFromParent, event_mask=X.KeyPressMask | X.KeyReleaseMask)
        win.map()
        receiver.sync()
        win.set_input_focus(X.RevertToParent, X.CurrentTime)
        receiver.sync()
        lookup = runner.Lookup()
        emitter = display.Display(env["DISPLAY"])
        keycode = int(emitter.keysym_to_keycode(XK.string_to_keysym("a")))
        xtest.fake_input(emitter, X.KeyPress, keycode)
        emitter.sync()
        xtest.fake_input(emitter, X.KeyRelease, keycode)
        emitter.sync()
        observed = runner.drain(receiver, lookup, timeout=1, quiet=0.1)
        expected = [("KeyPress", keycode, "a"), ("KeyRelease", keycode, "a")]
        actual = [(event["type"], event["keycode"], event["lookup_text"]) for event in observed]
        if actual != expected:
            raise AssertionError({"expected": expected, "actual": actual})
        print("CONSTRUCTION_PASS", actual)
    finally:
        if lookup is not None:
            lookup.close()
        if emitter is not None:
            emitter.close()
        if receiver is not None:
            receiver.close()
        if proc.poll() is None:
            proc.terminate()
        proc.wait(timeout=5)


if __name__ == "__main__":
    main()
