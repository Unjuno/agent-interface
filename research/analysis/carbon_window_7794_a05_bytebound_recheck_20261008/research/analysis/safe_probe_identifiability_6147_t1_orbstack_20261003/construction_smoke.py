#!/usr/bin/env python3
"""Transport-only check; does not run a policy or score a hidden-state case."""

import json
import time

from Xlib import X, XK, display
from Xlib.ext import xtest


def main() -> None:
    dpy = display.Display(":99")
    root = dpy.screen().root
    window = None
    for _ in range(100):
        for child in root.query_tree().children:
            try:
                geometry = child.get_geometry()
                if (geometry.width, geometry.height) == (640, 360):
                    window = child
                    break
            except Exception:
                pass
        if window:
            break
        time.sleep(0.05)
    if window is None:
        raise RuntimeError("fixture window did not appear")
    cmap = dpy.screen().default_colormap
    ready = cmap.alloc_color(red=0xE8E8, green=0xC8C8, blue=0x4040).pixel

    def sample() -> int:
        image = window.get_image(30, 60, 1, 1, X.ZPixmap, 0xFFFFFFFF)
        if image is None:
            raise RuntimeError("XGetImage returned no pixel")
        return int.from_bytes(image.data[:4], byteorder="little", signed=False)

    initial = sample()
    def click(x: int) -> None:
        xtest.fake_input(dpy, X.MotionNotify, x=x, y=250)
        xtest.fake_input(dpy, X.ButtonPress, detail=1)
        xtest.fake_input(dpy, X.ButtonRelease, detail=1)
        dpy.sync()
        time.sleep(0.1)

    click(100)
    after_safe_p = sample()
    click(210)
    after_safe_q = sample()
    right = cmap.alloc_color(red=0x4040, green=0x7070, blue=0xE8E8).pixel
    click(430)
    after_action = sample()
    keycode = dpy.keysym_to_keycode(XK.XK_F12)
    xtest.fake_input(dpy, X.KeyPress, detail=keycode)
    xtest.fake_input(dpy, X.KeyRelease, detail=keycode)
    dpy.sync()
    time.sleep(0.1)
    reset_signal = sample()
    result = {
        "initial_pixel": initial,
        "expected_ready_pixel": ready,
        "after_safe_p_pixel": after_safe_p,
        "after_safe_q_pixel": after_safe_q,
        "expected_right_pixel": right,
        "after_action_pixel": after_action,
        "after_harness_reset_pixel": reset_signal,
        "transport_gate": initial == ready and after_safe_p == ready and after_safe_q == right
        and after_action == 0xFFFFFF and reset_signal == ready,
        "scope": "construction-only X11 pixel/input/effect/reset transport; no protocol comparison or scientific outcome",
    }
    print(json.dumps(result, sort_keys=True))
    dpy.close()
    if not result["transport_gate"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
