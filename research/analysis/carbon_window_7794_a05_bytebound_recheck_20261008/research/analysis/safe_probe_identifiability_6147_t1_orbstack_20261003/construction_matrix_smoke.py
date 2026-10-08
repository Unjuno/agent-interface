#!/usr/bin/env python3
"""Hidden-deck construction check of rendered signals and terminal receipts; no policy."""

import json
import time
from pathlib import Path

from Xlib import X, XK, display, error
from Xlib.ext import xtest

COLORS = {
    "READY": "#E8C840", "LEFT": "#30D070", "RIGHT": "#4070E8",
    "BOTH": "#20C0B0", "UNKNOWN": "#808080",
    "EXPIRED_LEFT": "#E05050", "EXPIRED_RIGHT": "#B03030",
    "EFFECT_OK": "#FFFFFF",
}
SIGNAL = {
    "A": "LEFT", "B": "RIGHT", "C": "READY", "D": "READY",
    "E": "UNKNOWN", "F": "UNKNOWN", "G": "EXPIRED_LEFT",
    "H": "EXPIRED_RIGHT", "I": "BOTH", "J": "BOTH",
}
ACTION = {"A": "ACT_LEFT", "B": "ACT_RIGHT", "C": "ACT_COMMON", "D": "ACT_COMMON",
          "I": "ACT_COMMON", "J": "ACT_COMMON"}
BUTTONS = {"P": 100, "Q": 210, "ACT_LEFT": 340, "ACT_RIGHT": 430, "ACT_COMMON": 520}


def main() -> None:
    deck = [json.loads(line) for line in Path("/deck.jsonl").read_text().splitlines()]
    dpy = display.Display(":99")
    root = dpy.screen().root
    window = None
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline and window is None:
        for child in root.query_tree().children:
            try:
                geometry = child.get_geometry()
                if (geometry.width, geometry.height) == (640, 360):
                    window = child
                    break
            except Exception:
                continue
        time.sleep(0.05)
    if window is None:
        raise RuntimeError("fixture window not visible")
    cmap = dpy.screen().default_colormap
    pixels = {
        cmap.alloc_color(red=int(color[1:3], 16) * 257, green=int(color[3:5], 16) * 257,
                         blue=int(color[5:7], 16) * 257).pixel: name
        for name, color in COLORS.items()
    }

    def observe() -> str:
        dpy.sync()
        image = window.get_image(30, 60, 1, 1, X.ZPixmap, 0xFFFFFFFF)
        if image is None:
            raise RuntimeError("XGetImage returned no sample")
        return pixels.get(int.from_bytes(image.data[:4], "little"), "UNKNOWN_PIXEL")

    def click(x: int) -> None:
        xtest.fake_input(dpy, X.MotionNotify, x=x, y=250)
        xtest.fake_input(dpy, X.ButtonPress, detail=1)
        xtest.fake_input(dpy, X.ButtonRelease, detail=1)
        dpy.sync()
        time.sleep(0.07)

    def reset() -> None:
        keycode = dpy.keysym_to_keycode(XK.XK_F12)
        xtest.fake_input(dpy, X.KeyPress, detail=keycode)
        xtest.fake_input(dpy, X.KeyRelease, detail=keycode)
        dpy.sync()
        time.sleep(0.07)

    rows = []
    for entry in deck:
        state = entry["state_id"]
        signals = [observe()]
        click(BUTTONS["P"])
        signals.append(observe())
        click(BUTTONS["Q"])
        signals.append(observe())
        expected_terminal = SIGNAL[state]
        action = ACTION.get(state)
        effect = None
        if action:
            click(BUTTONS[action])
            effect = observe()
        expected_effect = "EFFECT_OK" if action else None
        rows.append({"trial_index": entry["trial_index"], "state_id": state,
                     "signals": signals, "expected_terminal": expected_terminal,
                     "action": action, "effect": effect})
        if signals != ["READY", "READY", expected_terminal] or effect != expected_effect:
            raise SystemExit(json.dumps({"transport_gate": False, "rows": rows}, sort_keys=True))
        reset()
    result = {"transport_gate": len(rows) == 10, "rows": rows,
              "scope": "construction-only rendered-pixel, safe-probe, terminal-state and fixture-receipt check; no policy candidate or formal allocation"}
    print(json.dumps(result, sort_keys=True))
    try:
        dpy.close()
    except error.ConnectionClosedError:
        # The fixture exits as soon as the final harness reset is processed.
        pass


if __name__ == "__main__":
    main()
