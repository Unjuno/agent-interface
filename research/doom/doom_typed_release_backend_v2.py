"""Typed DOOM backend with telemetry-only ordinary key-up release evidence."""
import time

from Xlib import XK

from doom_typed_release_backend_v1 import Backend as Previous, suite
from input_owner_v11 import InputOwner


class Backend(Previous):
    def __init__(self, session, out, emit, signal_readers):
        super().__init__(session, out, emit, signal_readers)
        # Replace v10 before measured authority. No policy/lease semantics change.
        self.owner.close()
        self.owner = InputOwner(session.name)

    def raw(self, key, down):
        record = self.owner.call('down' if down else 'up', self.lease, key)
        if down:
            self.held.add(key)
            self.emit(record)
            return

        was_backend_held = key in self.held
        self.held.discard(key)
        if not isinstance(record, dict):
            raise AssertionError('InputOwner v11 up must return telemetry')

        record['backend_believed_held'] = was_backend_held
        record['physical_verification_authoritative'] = False
        try:
            code = self.session.d.keysym_to_keycode(XK.string_to_keysym(key))
            if not code:
                raise ValueError('key unavailable on session display')
            bitmap = self.session.d.query_keymap()
            verified_ns = time.perf_counter_ns()
            physical_down = bool(bitmap[code // 8] & (1 << (code % 8)))
            record.update(
                keycode=code,
                physical_key_down=physical_down,
                physical_verified_up=not physical_down,
                physical_verified_ns=verified_ns,
                physical_verification_source='session_display.query_keymap',
            )
        except Exception as exc:
            # Telemetry failure must not turn a successful release into a control
            # failure. The missing verification is explicit and fail-closed.
            record.update(
                physical_key_down=None,
                physical_verified_up=None,
                physical_verified_ns=time.perf_counter_ns(),
                physical_verification_source='session_display.query_keymap',
                physical_verification_error=repr(exc),
            )
        self.emit(record)
