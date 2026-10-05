"""Release socket with copied server-side request registration receipts."""
import copy

from release_event_socket_v1 import ReleaseEventSocket as Previous


class ReleaseEventSocket(Previous):
    def request_receipts(self):
        with self._condition:
            return copy.deepcopy(self.requests)
