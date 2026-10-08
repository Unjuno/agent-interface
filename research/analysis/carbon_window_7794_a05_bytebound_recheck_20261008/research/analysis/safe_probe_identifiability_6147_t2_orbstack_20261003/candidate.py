#!/usr/bin/env python3
"""Pixel-only controller run in a container separate from the GUI fixture."""

import argparse
import json
import sys
import time
from pathlib import Path

from Xlib import X, XK, display, error
from Xlib.ext import xtest

from lifecycle import close_display
from policy import next_step


def color_pixel(cmap, value: str) -> int:
    return cmap.alloc_color(
        red=int(value[1:3], 16) * 257,
        green=int(value[3:5], 16) * 257,
        blue=int(value[5:7], 16) * 257,
    ).pixel


def find_window(dpy, width: int, height: int):
    root = dpy.screen().root
    deadline = time.monotonic() + 8.0
    while time.monotonic() < deadline:
        for window in root.query_tree().children:
            try:
                geometry = window.get_geometry()
                if geometry.width == width and geometry.height == height:
                    return window
            except Exception:
                continue
        time.sleep(0.05)
    raise TimeoutError("fixture window not visible on the X11 display")


class PixelController:
    def __init__(self, model: dict, display_name: str):
        self.dpy = display.Display(display_name)
        self.window = find_window(self.dpy, model["display"]["width"], model["display"]["height"])
        self.root = self.dpy.screen().root
        self.colors = {
            color_pixel(self.dpy.screen().default_colormap, color): signal
            for signal, color in model["signals"].items()
        }
        self.sample_x, self.sample_y = model["display"]["status_sample"]
        self.buttons = model["buttons"]
        self.reset_key = self.dpy.keysym_to_keycode(XK.XK_F12)
        self.window.set_input_focus(X.RevertToParent, X.CurrentTime)
        self.dpy.sync()

    def observe(self) -> str:
        self.dpy.sync()
        image = self.window.get_image(self.sample_x, self.sample_y, 1, 1, X.ZPixmap, 0xFFFFFFFF)
        if image is None:
            return "NO_IMAGE"
        pixel = int.from_bytes(image.data[:4], byteorder="little", signed=False)
        return self.colors.get(pixel, "UNKNOWN_PIXEL")

    def click(self, action: str) -> None:
        x, y = self.buttons[action]
        xtest.fake_input(self.dpy, X.MotionNotify, x=x, y=y)
        xtest.fake_input(self.dpy, X.ButtonPress, detail=1)
        xtest.fake_input(self.dpy, X.ButtonRelease, detail=1)
        self.dpy.sync()
        time.sleep(0.06)

    def reset(self) -> None:
        xtest.fake_input(self.dpy, X.KeyPress, detail=self.reset_key)
        xtest.fake_input(self.dpy, X.KeyRelease, detail=self.reset_key)
        self.dpy.sync()
        time.sleep(0.06)

    def close(self) -> None:
        # The finite fixture may close Xvfb immediately after its final reset.
        # Only cleanup tolerates this specific disconnect; action-path errors
        # still propagate and the independent auditor gates completeness.
        close_display(self.dpy, error.ConnectionClosedError)


def run_trial(controller: PixelController, context: dict, arm: str) -> dict:
    observations: list[str] = []
    probes: list[str] = []
    choice = "YIELD"
    effect_signal = None
    signal = controller.observe()
    observations.append(signal)
    for _ in range(4):
        step = next_step(context["family"], arm, observations, probes)
        if step == "PROBE_P":
            controller.click("P")
            probes.append("P")
            signal = controller.observe()
            observations.append(signal)
            continue
        if step == "PROBE_Q":
            controller.click("Q")
            probes.append("Q")
            signal = controller.observe()
            observations.append(signal)
            continue
        choice = step
        if step.startswith("ACT_"):
            controller.click(step)
            effect_signal = controller.observe()
        break
    return {
        "trial_index": context["trial_index"],
        "family": context["family"],
        "arm": arm,
        "observations": observations,
        "probes": probes,
        "choice": choice,
        "effect_signal": effect_signal,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=("adaptive", "no_probe", "one_step"), required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--contexts", type=Path, required=True)
    parser.add_argument("--display", default=":99")
    args = parser.parse_args()
    model = json.loads(args.model.read_text(encoding="utf-8"))
    contexts = [json.loads(line) for line in args.contexts.read_text(encoding="utf-8").splitlines()]
    if len(contexts) != 10:
        raise ValueError("public context deck must contain exactly ten rows")
    controller = PixelController(model, args.display)
    limits = {}
    for name in ("memory.max", "memory.swap.max", "pids.max"):
        try:
            limits[name] = (Path("/sys/fs/cgroup") / name).read_text(encoding="utf-8").strip()
        except OSError:
            limits[name] = "UNAVAILABLE"
    print(json.dumps({"event": "CANDIDATE_ENVIRONMENT", "limits": limits}, sort_keys=True), file=sys.stderr, flush=True)
    try:
        for context in contexts:
            row = run_trial(controller, context, args.arm)
            print(json.dumps(row, sort_keys=True, separators=(",", ":")), flush=True)
            controller.reset()
    finally:
        controller.close()


if __name__ == "__main__":
    main()
