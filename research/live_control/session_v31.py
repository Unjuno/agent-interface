"""Use short session aliases for model-facing target handles."""
from scoped_target_handle_v3 import TargetHandleStore
from session_v30 import Backend as Previous, suite


class Backend(Previous):
    def __init__(self, session, out, emit):
        super().__init__(session, out, emit)
        self.handles = TargetHandleStore("x11:" + session.name)
