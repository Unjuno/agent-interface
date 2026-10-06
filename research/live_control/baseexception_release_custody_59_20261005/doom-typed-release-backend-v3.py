"""DOOM typed backend composing v11 release telemetry with cancellation-aware owner cleanup."""
from __future__ import annotations

from doom_typed_release_backend_v2 import Backend as Previous, suite
from input_owner_v13 import InputOwner


class Backend(Previous):
    def __init__(self, session, out, emit, signal_readers):
        super().__init__(session, out, emit, signal_readers)
        # V2 installs the telemetry-only v11 wrapper; replace the empty owner
        # with v13, which retains the same release receipt and adds cancel cause.
        self.owner.close()
        self.owner = InputOwner(session.name)
