#!/usr/bin/env python3
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import time
from typing import Any
from Xlib import X, XK, display
from Xlib.ext import xtest

BUTTON_MAP = {'left': 1, 'middle': 2, 'right': 3, 'x1': 8, 'x2': 9}
BUTTON_MASKS = {1: X.Button1Mask, 2: X.Button2Mask, 3: X.Button3Mask, 4: X.Button4Mask, 5: X.Button5Mask}

class BackendError(RuntimeError):
    pass

@dataclass
class ReleaseReceipt:
    keys_down: list[str]
    buttons_down: list[str]
    verified: bool
    monotonic_ns: int

class X11Backend:
    def __init__(self, display_name: str, targets: dict[str, int]):
        self.d = display.Display(display_name)
        self.root = self.d.screen().root
        if not self.d.has_extension('XTEST'):
            raise BackendError('XTEST unavailable')
        self.targets = {name: self.d.create_resource_object('window', wid) for name, wid in targets.items()}
        self.held_keycodes: dict[str, int] = {}
        self.held_buttons: set[str] = set()
        self.emissions = 0

    def close(self) -> None:
        self.d.close()

    def capabilities(self) -> dict[str, bool]:
        return {
            'capture.frame': True,
            'input.keyboard': True,
            'input.text': True,
            'input.pointer': True,
            'input.scroll': True,
            'input.release_all': True,
            'window.focus': True,
            'display.geometry': True,
            'clock.monotonic': True,
            'event.feedback': True,
        }

    def _target(self, name: str):
        if name not in self.targets:
            raise BackendError(f'unknown target {name}')
        return self.targets[name]

    def focus(self, target: str) -> None:
        win = self._target(target)
        win.set_input_focus(X.RevertToParent, X.CurrentTime)
        self.d.sync()
        focus = self.d.get_input_focus().focus
        if getattr(focus, 'id', None) != win.id:
            raise BackendError('focus verification failed')

    def geometry(self, target: str) -> dict[str, int]:
        win = self._target(target)
        geo = win.get_geometry()
        translated = self.root.translate_coords(win, 0, 0)
        return {'x': translated.x, 'y': translated.y, 'width': geo.width, 'height': geo.height}

    def _root_point(self, target: str, frame: str, x: int, y: int) -> tuple[int, int]:
        if frame == 'screen_physical_px':
            return x, y
        if frame == 'window_client':
            g = self.geometry(target)
            return g['x'] + x, g['y'] + y
        raise BackendError(f'unsupported frame {frame}')

    def pointer_move(self, target: str, frame: str, x: int, y: int) -> None:
        rx, ry = self._root_point(target, frame, x, y)
        xtest.fake_input(self.d, X.MotionNotify, x=rx, y=ry)
        self.emissions += 1
        self.d.sync()

    def pointer_button(self, button: str, down: bool) -> None:
        number = BUTTON_MAP[button]
        etype = X.ButtonPress if down else X.ButtonRelease
        xtest.fake_input(self.d, etype, number)
        self.emissions += 1
        self.d.sync()
        if down:
            self.held_buttons.add(button)
        else:
            self.held_buttons.discard(button)

    def _keycode(self, key: str) -> int:
        aliases = {'CTRL': 'Control_L', 'SHIFT': 'Shift_L', 'ALT': 'Alt_L', 'ENTER': 'Return', 'TAB': 'Tab', 'ESC': 'Escape', 'SPACE': 'space'}
        keysym = XK.string_to_keysym(aliases.get(key, key))
        if keysym == 0 and len(key) == 1:
            keysym = XK.string_to_keysym(key.lower())
        code = self.d.keysym_to_keycode(keysym)
        if not code:
            raise BackendError(f'unmapped key {key}')
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

    def text(self, text: str) -> None:
        # v0 X11 backend intentionally supports a strict ASCII subset; richer IME/text
        # semantics remain a separate capability extension rather than silent guessing.
        for ch in text:
            if ch == ' ':
                self.key_chord(['SPACE'])
                continue
            if not (ch.isascii() and (ch.isalpha() or ch.isdigit() or ch in '.-_')):
                raise BackendError(f'unsupported text character U+{ord(ch):04X}')
            if ch.isalpha() and ch.isupper():
                self.key_state('SHIFT', True)
                self.key_chord([ch.lower()])
                self.key_state('SHIFT', False)
            else:
                self.key_chord([ch])

    def scroll(self, dx: int, dy: int) -> None:
        # X11 wheel conventions: 4 up, 5 down, 6 left, 7 right.
        actions = []
        actions += [4] * max(0, -dy) + [5] * max(0, dy)
        actions += [6] * max(0, -dx) + [7] * max(0, dx)
        for button in actions:
            xtest.fake_input(self.d, X.ButtonPress, button)
            xtest.fake_input(self.d, X.ButtonRelease, button)
            self.emissions += 2
        self.d.sync()

    def capture(self, target: str, frame: str, x: int, y: int, w: int, h: int) -> dict[str, Any]:
        win = self._target(target)
        if frame == 'window_client':
            source = win
            sx, sy = x, y
        elif frame == 'screen_physical_px':
            source = self.root
            sx, sy = x, y
        else:
            raise BackendError(f'unsupported capture frame {frame}')
        image = source.get_image(sx, sy, w, h, X.ZPixmap, 0xFFFFFFFF)
        if image is None:
            raise BackendError('capture returned no image')
        data = bytes(image.data)
        return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'width': w, 'height': h}

    def wait_update(self, timeout_ms: int) -> None:
        time.sleep(timeout_ms / 1000.0)

    def _physical_keys_down(self, tracked: dict[str, int] | None = None) -> list[str]:
        keymap = self.d.query_keymap()
        rows = []
        for name, code in (tracked or self.held_keycodes).items():
            if keymap[code // 8] & (1 << (code % 8)):
                rows.append(name)
        return sorted(rows)

    def _physical_buttons_down(self) -> list[str]:
        mask = self.root.query_pointer().mask
        reverse = {1: 'left', 2: 'middle', 3: 'right'}
        return sorted(reverse[n] for n, bit in BUTTON_MASKS.items() if n in reverse and mask & bit)

    def release_all(self) -> ReleaseReceipt:
        tracked_keys = dict(self.held_keycodes)
        for key, code in list(self.held_keycodes.items()):
            xtest.fake_input(self.d, X.KeyRelease, code)
            self.emissions += 1
        for button in list(self.held_buttons):
            xtest.fake_input(self.d, X.ButtonRelease, BUTTON_MAP[button])
            self.emissions += 1
        self.d.sync()
        self.held_keycodes.clear()
        self.held_buttons.clear()
        keys = self._physical_keys_down(tracked_keys)
        buttons = self._physical_buttons_down()
        return ReleaseReceipt(keys, buttons, not keys and not buttons, time.monotonic_ns())

    def execute(self, program: dict[str, Any]) -> dict[str, Any]:
        current_target = None
        observations = []
        releases = []
        started = time.monotonic_ns()
        try:
            for op in program['ops']:
                kind = op['op']
                if kind == 'focus':
                    current_target = op['target']
                    self.focus(current_target)
                elif kind == 'key_chord':
                    self.key_chord(op['keys'])
                elif kind == 'key_state':
                    self.key_state(op['key'], op['down'])
                elif kind == 'text':
                    self.text(op['text'])
                elif kind == 'pointer_move':
                    if current_target is None:
                        raise BackendError('pointer_move requires focused target')
                    self.pointer_move(current_target, op['frame'], op['x'], op['y'])
                elif kind == 'pointer_button':
                    self.pointer_button(op['button'], op['down'])
                elif kind == 'scroll':
                    self.scroll(op['dx'], op['dy'])
                elif kind == 'observe':
                    if current_target is None:
                        raise BackendError('observe requires focused target')
                    observations.append(self.capture(current_target, op['frame'], op['x'], op['y'], op['w'], op['h']))
                elif kind == 'wait_update':
                    self.wait_update(op['timeout_ms'])
                elif kind == 'verify':
                    # Semantic verification belongs to caller/scorer; backend does not guess.
                    pass
                elif kind == 'release_all':
                    releases.append(self.release_all().__dict__)
                else:
                    raise BackendError(f'unsupported op {kind}')
        except Exception:
            # Fail-closed terminal release on backend exceptions.
            releases.append(self.release_all().__dict__)
            raise
        return {
            'started_ns': started,
            'ended_ns': time.monotonic_ns(),
            'emissions': self.emissions,
            'observations': observations,
            'releases': releases,
        }
