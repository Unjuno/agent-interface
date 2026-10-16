"""Release socket v2 receipts with semantic-probe-aware event cursor."""
from release_event_cursor_v2 import EventCursor
from release_event_socket_v2 import ReleaseEventSocket as Previous


class ReleaseEventSocket(Previous):
    def __init__(self):
        super().__init__()
        self.cursor = EventCursor()
