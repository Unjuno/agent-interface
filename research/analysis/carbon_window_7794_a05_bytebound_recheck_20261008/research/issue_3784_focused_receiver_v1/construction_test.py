"""Receiver-oracle construction test; its events are not formal evidence."""
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
        "-nolisten", "tcp", "+extension", "XKEYBOARD", "+extension", "XTEST", "-noreset"],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
        focus = receiver.get_input_focus().focus
        if focus.id != win.id:
            raise AssertionError("InputOnly receiver does not own focus")
        us = runner.capture_state(env, "us")
        if not us["layout_ok"] or us["query"]["returncode"] != 0:
            raise AssertionError({"us_layout": us["query"]})
        applied = runner.command(["setxkbmap", "-layout", "de"], env)
        if applied["returncode"] != 0:
            raise AssertionError({"setxkbmap": applied})
        de = runner.capture_state(env, "de")
        if (not de["layout_ok"] or de["query"]["returncode"] != 0
                or de["dump_sha256"] == us["dump_sha256"]
                or de["map_sha256"] == us["map_sha256"]):
            raise AssertionError({"de_layout": de["query"], "dump_changed": de["dump_sha256"] != us["dump_sha256"],
                                  "map_changed": de["map_sha256"] != us["map_sha256"]})
        lookup = runner.Lookup()
        emitter = display.Display(env["DISPLAY"])
        keycode = int(emitter.keysym_to_keycode(XK.string_to_keysym("a")))
        xtest.fake_input(emitter, X.KeyPress, keycode)
        emitter.sync()
        xtest.fake_input(emitter, X.KeyRelease, keycode)
        emitter.sync()
        events = runner.drain(receiver, lookup, timeout=1, quiet=0.1)
        ok = (len(events) == 2 and events[0]["type"] == "KeyPress"
            and events[0]["keycode"] == keycode and events[0]["lookup_text"] == "a"
            and events[1]["type"] == "KeyRelease" and events[1]["keycode"] == keycode)
        if not ok:
            raise AssertionError(events)
        print("CONSTRUCTION_PASS", {"layout_transition": "us->de", "server_dump_changed": True,
              "fresh_client_map_changed": True,
              "receiver_events": [(e["type"], e["keycode"], e["lookup_text"]) for e in events]})
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
