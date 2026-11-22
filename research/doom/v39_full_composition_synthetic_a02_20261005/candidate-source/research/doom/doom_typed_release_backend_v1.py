"""Typed DOOM backend opting into lease-bound InputOwner v10 release evidence."""
from doom_typed_coast_backend_v1 import Backend as Previous, suite
from input_owner_v10 import InputOwner


class Backend(Previous):
    def __init__(self, session, out, emit, signal_readers):
        super().__init__(session, out, emit, signal_readers)
        # Replacement occurs before measured capture or authority. The inherited
        # owner is closed empty; all subsequent binding/input uses owner v10.
        self.owner.close()
        self.owner = InputOwner(session.name)
