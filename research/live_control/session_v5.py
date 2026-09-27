"""Development backend with independent input expiry; frozen v4 image path."""
import session_v4 as previous
from input_owner import InputOwner

suite = previous.suite


class Backend(previous.Backend):
    def __init__(self, session, out, emit):
        super().__init__(session, out, emit)
        self.owner = InputOwner(session.name)

    def raw(self, key, down):
        record = self.owner.call('down' if down else 'up', self.lease, key)
        if down:
            self.held.add(key)
            # This callback may block. The owner still checks its own lease.
            self.emit(record)
        else:
            self.held.discard(key)

    def release_all(self):
        result = self.owner.call('release', getattr(self, 'lease', None))
        self.held.clear()
        return result

    def close(self):
        self.owner.close()
