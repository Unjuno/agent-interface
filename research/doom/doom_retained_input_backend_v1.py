"""Typed DOOM backend with explicit input-release transition evidence."""
from doom_typed_coast_backend_v1 import Backend as Previous, suite
from input_transition_owner_v1 import InputOwner


class Backend(Previous):
    def __init__(self, session, out, emit, signal_readers):
        super().__init__(session, out, emit, signal_readers)
        self.owner.close()
        self.owner = InputOwner(session.name)

    def raw(self, key, down):
        was_backend_owned = key in self.held
        expected_after = None if down else len(self.held) - (1 if was_backend_owned else 0)
        record = self.owner.call("down" if down else "up", self.lease, key)
        if down:
            self.held.add(key)
        else:
            self.held.discard(key)
            if isinstance(record, dict) and record.get("event") == "input_release_transition":
                record["backend_owned_before_release"] = was_backend_owned
                record["expected_owned_count_after"] = expected_after
                record["owner_transition_verified"] = (
                    was_backend_owned and record.get("owned_count_after") == expected_after)
        if record is not None:
            self.emit(record)
