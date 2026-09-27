"""X11/XTEST implementation of the runtime core v1 backend boundary.

This implementation is intentionally narrow: X11 only, strict ASCII text, and
explicitly registered target windows. It never decides admission itself.
"""
from __future__ import annotations

import hashlib
import time
from typing import Any
from Xlib import X, XK, display
from Xlib.ext import xtest

from runtime.core_v1.contract import OFFICE_FLOOR, capability_manifest, validate_backend_manifest

BUTTON_MAP = {"left": 1, "middle": 2, "right": 3, "x1": 8, "x2": 9}
BUTTON_MASKS = {1: X.Button1Mask, 2: X.Button2Mask, 3: X.Button3Mask}


class X11BackendError(RuntimeError):
    pass


class X11Backend:
    def __init__(self, display_name: str, targets: dict[str, int]):
        self.d = display.Display(display_name)
        self.root = self.d.screen().root
        if not self.d.has_extension("XTEST"):
            raise X11BackendError("XTEST unavailable")
        self.targets = {
            name: self.d.create_resource_object("window", wid)
            for name, wid in targets.items()
        }
        self.held_keycodes: dict[str, int] = {}
        self.held_buttons: set[str] = set()
        self.emissions = 0
        self.capture_artifacts = None

    def configure_capture_artifacts(self, directory) -> None:
        from .capture_artifacts import CaptureArtifacts
        self.capture_artifacts = CaptureArtifacts(directory)

    def observe_read_only(self, target, frame, region):
        # Unlike a program's focus/observe sequence this does not change focus,
        # send input, release somebody else's held input, or renew a lease.
        return self.capture(target, frame, *region)

    def close(self) -> None:
        self.d.close()

    def manifest(self) -> dict[str, Any]:
        row = capability_manifest(
            "x11-v1",
            "linux",
            "x11",
            OFFICE_FLOOR,
            frames=("screen_physical_px", "window_client"),
            permissions=("x11-display-access",),
        )
        row["capabilities"]["input.text"]["detail"] = "strict ASCII letters/digits/space/._-"
        return validate_backend_manifest(row)

    def monotonic_ns(self) -> int:
        return time.monotonic_ns()

    def _target(self, name: str):
        if name not in self.targets:
            raise X11BackendError(f"unknown target {name}")
        return self.targets[name]

    def focus(self, target: str) -> None:
        win = self._target(target)
        win.set_input_focus(X.RevertToParent, X.CurrentTime)
        self.d.sync()
        focus = self.d.get_input_focus().focus
        if getattr(focus, "id", None) != win.id:
            raise X11BackendError("focus verification failed")

    def geometry(self, target: str) -> dict[str, int]:
        win = self._target(target)
        geo = win.get_geometry()
        translated = self.root.translate_coords(win, 0, 0)
        return {"x": translated.x, "y": translated.y, "width": geo.width, "height": geo.height}

    def _root_point(self, target: str, frame: str, x: int, y: int) -> tuple[int, int]:
        if frame == "screen_physical_px":
            return x, y
        if frame == "window_client":
            g = self.geometry(target)
            return g["x"] + x, g["y"] + y
        raise X11BackendError(f"unsupported frame {frame}")

    def pointer_move(self, target: str, frame: str, x: int, y: int) -> None:
        rx, ry = self._root_point(target, frame, x, y)
        xtest.fake_input(self.d, X.MotionNotify, x=rx, y=ry)
        self.emissions += 1
        self.d.sync()

    def pointer_button(self, button: str, down: bool) -> None:
        number = BUTTON_MAP[button]
        xtest.fake_input(self.d, X.ButtonPress if down else X.ButtonRelease, number)
        self.emissions += 1
        self.d.sync()
        if down:
            self.held_buttons.add(button)
        else:
            self.held_buttons.discard(button)

    def _keycode(self, key: str) -> int:
        aliases = {
            "CTRL": "Control_L", "SHIFT": "Shift_L", "ALT": "Alt_L",
            "ENTER": "Return", "TAB": "Tab", "ESC": "Escape", "SPACE": "space",
        }
        keysym = XK.string_to_keysym(aliases.get(key, key))
        if keysym == 0 and len(key) == 1:
            keysym = XK.string_to_keysym(key.lower())
        code = self.d.keysym_to_keycode(keysym)
        if not code:
            raise X11BackendError(f"unmapped key {key}")
        return code

    def key_state(self, key: str, down: bool) -> None:
        code = self._keycode(key)
        xtest.fake_input(self.d, X.KeyPress if down else X.KeyRelease, code)
        self.emissions += 1
        self.d.sync()
        if down:
            self.held_keycodes[key] = code
        else:
            self.held_keycodes.pop(key, None)

    def key_chord(self, keys: list[str]) -> None:
        for key in keys:
            self.key_state(key, True)
        for key in reversed(keys):
            self.key_state(key, False)

    def preflight(self, program: dict[str, Any]) -> None:
        """Validate X11-specific constraints before the first physical emission."""
        focused = False
        for op in program["ops"]:
            kind = op["op"]
            if kind == "focus":
                self._target(op["target"])
                focused = True
            elif kind in {"pointer_move", "observe"} and not focused:
                raise X11BackendError(f"{kind} requires focused target")
            elif kind == "text":
                for ch in op["text"]:
                    if ch == " ":
                        continue
                    if not (ch.isascii() and (ch.isalpha() or ch.isdigit() or ch in ".-_")):
                        raise X11BackendError(f"unsupported text character U+{ord(ch):04X}")
            elif kind == "key_chord":
                for key in op["keys"]:
                    self._keycode(key)
            elif kind == "key_state":
                self._keycode(op["key"])

    def text(self, value: str) -> None:
        # Validate the complete string before the first physical emission.
        # A rejected text operation must not leave an accepted prefix behind.
        for ch in value:
            if ch == " ":
                continue
            if not (ch.isascii() and (ch.isalpha() or ch.isdigit() or ch in ".-_")):
                raise X11BackendError(f"unsupported text character U+{ord(ch):04X}")
        for ch in value:
            if ch == " ":
                self.key_chord(["SPACE"])
                continue
            if ch.isalpha() and ch.isupper():
                self.key_state("SHIFT", True)
                self.key_chord([ch.lower()])
                self.key_state("SHIFT", False)
            else:
                self.key_chord([ch])

    def scroll(self, dx: int, dy: int) -> None:
        buttons = [4] * max(0, -dy) + [5] * max(0, dy)
        buttons += [6] * max(0, -dx) + [7] * max(0, dx)
        for number in buttons:
            xtest.fake_input(self.d, X.ButtonPress, number)
            xtest.fake_input(self.d, X.ButtonRelease, number)
            self.emissions += 2
        self.d.sync()

    def capture(self, target: str, frame: str, x: int, y: int, w: int, h: int) -> dict[str, Any]:
        win = self._target(target)
        if frame == "window_client":
            source, sx, sy = win, x, y
        elif frame == "screen_physical_px":
            source, sx, sy = self.root, x, y
        else:
            raise X11BackendError(f"unsupported capture frame {frame}")
        capture_started_ns = time.monotonic_ns()
        image = source.get_image(sx, sy, w, h, X.ZPixmap, 0xFFFFFFFF)
        capture_ended_ns = time.monotonic_ns()
        if image is None:
            raise X11BackendError("capture returned no image")
        raw = bytes(image.data)
        row = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "width": w, "height": h}
        if self.capture_artifacts is not None:
            row.update(target=target, native_window_id=win.id, frame=frame,
                       region=[x, y, w, h], capture_started_ns=capture_started_ns,
                       capture_ended_ns=capture_ended_ns)
            try:
                info = self.d.display.info
                fmt = next(f for f in info.pixmap_formats if f.depth == image.depth)
                visual = next(v for screen in info.roots for d in screen.allowed_depths
                              for v in d.visuals if v.visual_id == image.visual)
                row["artifact"] = self.capture_artifacts.write(
                    raw, w, h, depth=image.depth, bits_per_pixel=fmt.bits_per_pixel,
                    scanline_pad=fmt.scanline_pad, byte_order=info.image_byte_order,
                    masks=(visual.red_mask, visual.green_mask, visual.blue_mask),
                    true_color=visual.visual_class == X.TrueColor)
            except Exception as error:
                # Keep the actual observation and completed input evidence even
                # if image presentation fails. Never take a replacement capture.
                row["artifact_error"] = repr(error)
        return row

    def _physical_keys_down(self, tracked: dict[str, int] | None = None) -> list[str]:
        keymap = self.d.query_keymap()
        rows = []
        for name, code in (tracked or self.held_keycodes).items():
            if keymap[code // 8] & (1 << (code % 8)):
                rows.append(name)
        return sorted(rows)

    def _physical_buttons_down(self) -> list[str]:
        mask = self.root.query_pointer().mask
        reverse = {1: "left", 2: "middle", 3: "right"}
        return sorted(reverse[n] for n, bit in BUTTON_MASKS.items() if mask & bit)

    def release_all(self) -> dict[str, Any]:
        tracked = dict(self.held_keycodes)
        for code in list(self.held_keycodes.values()):
            xtest.fake_input(self.d, X.KeyRelease, code)
            self.emissions += 1
        for button in list(self.held_buttons):
            xtest.fake_input(self.d, X.ButtonRelease, BUTTON_MAP[button])
            self.emissions += 1
        self.d.sync()
        self.held_keycodes.clear()
        self.held_buttons.clear()
        keys = self._physical_keys_down(tracked)
        buttons = self._physical_buttons_down()
        return {
            "keys_down": keys,
            "buttons_down": buttons,
            "verified": not keys and not buttons,
            "monotonic_ns": time.monotonic_ns(),
        }

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
                elif kind == "key_chord": self.key_chord(op["keys"])
                elif kind == "key_state": self.key_state(op["key"], op["down"])
                elif kind == "text": self.text(op["text"])
                elif kind == "pointer_move":
                    if current_target is None: raise X11BackendError("pointer_move requires focused target")
                    self.pointer_move(current_target, op["frame"], op["x"], op["y"])
                elif kind == "pointer_button": self.pointer_button(op["button"], op["down"])
                elif kind == "scroll": self.scroll(op["dx"], op["dy"])
                elif kind == "observe":
                    if current_target is None: raise X11BackendError("observe requires focused target")
                    observations.append(self.capture(current_target, op["frame"], op["x"], op["y"], op["w"], op["h"]))
                elif kind == "wait_update": time.sleep(op["timeout_ms"] / 1000.0)
                elif kind == "verify": pass
                elif kind == "release_all": releases.append(self.release_all())
                else: raise X11BackendError(f"unsupported op {kind}")
        except Exception:
            releases.append(self.release_all())
            raise
        return {
            "started_ns": started,
            "ended_ns": time.monotonic_ns(),
            "emissions": self.emissions,
            "observations": observations,
            "releases": releases,
        }
