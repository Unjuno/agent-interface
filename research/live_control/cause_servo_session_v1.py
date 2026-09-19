"""Compose existing patch servo with the cause-recording owner; no new policy."""
from session_v21 import Backend as Previous, suite, SERVO_SCHEMA
from cause_session_v1 import Backend as OwnerSetup
from pointer_reply_v2 import PointerReply


class Backend(Previous):
    def __init__(self, session, out, emit):
        OwnerSetup.__init__(self, session, out, emit)
        self.replies = PointerReply()
