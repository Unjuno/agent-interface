#!/usr/bin/env python3
"""LibreOffice-facing X11 candidate policy stacked on the retained X11 backend.

This module changes backend policy only: EWMH activation and bounded keyboard
pacing. The portable semantic program/authority contract is unchanged.
"""
from __future__ import annotations
import time
from Xlib import X
from Xlib.protocol import event
from backend_x11 import X11Backend, BackendError

class OfficeX11Backend(X11Backend):
    def __init__(self, display_name: str, targets: dict[str, int], *, text_pacing_s: float = 0.012,
                 activation_timeout_s: float = 1.0):
        super().__init__(display_name, targets)
        if not (0.0 <= text_pacing_s <= 0.100):
            raise ValueError('text pacing out of range')
        self.text_pacing_s = float(text_pacing_s)
        self.activation_timeout_s = float(activation_timeout_s)

    def focus(self, target: str) -> None:
        win = self._target(target)
        atom = self.d.intern_atom('_NET_ACTIVE_WINDOW')
        message = event.ClientMessage(
            window=win, client_type=atom,
            data=(32, [1, X.CurrentTime, 0, 0, 0]),
        )
        self.root.send_event(
            message,
            event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask,
        )
        self.d.flush()
        deadline = time.monotonic() + self.activation_timeout_s
        while time.monotonic() < deadline:
            focus = self.d.get_input_focus().focus
            if getattr(focus, 'id', None) == win.id:
                return
            time.sleep(0.01)
        # A bounded direct-focus fallback is allowed as transport policy, but is
        # still verified and never treated as semantic completion.
        win.set_input_focus(X.RevertToParent, X.CurrentTime)
        self.d.sync()
        focus = self.d.get_input_focus().focus
        if getattr(focus, 'id', None) != win.id:
            raise BackendError('focus activation verification failed')

    def text(self, value: str) -> None:
        # Preserve retained strict-ASCII semantics; only pace delivery here.
        for character in value:
            super().text(character)
            time.sleep(self.text_pacing_s)
