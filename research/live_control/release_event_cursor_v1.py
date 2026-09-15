"""Bounded non-consuming cursor for action release and terminal delivery."""
import json
import threading
import time
from collections import deque

from release_event_scope_v1 import boundary, validate_scope


class EventCursor:
    def __init__(self, capacity=256):
        self.capacity = capacity; self.records = deque(); self.sequence = 0
        self.closed = False; self.condition = threading.Condition()

    def append(self, record):
        encoded = json.dumps(record, allow_nan=False)
        with self.condition:
            if self.closed: raise ValueError("stream closed")
            self.sequence += 1; self.records.append((self.sequence, encoded))
            if len(self.records) > self.capacity: self.records.popleft()
            self.condition.notify_all(); return self.sequence

    def close(self):
        with self.condition: self.closed = True; self.condition.notify_all()

    def read_until(self, after, events, timeout=5, action_id=None):
        if type(after) is not int or after < 0: raise ValueError("cursor required")
        if type(timeout) not in (int, float) or not 0 <= timeout <= 30:
            raise ValueError("timeout 0..30 required")
        if not isinstance(events, list) or not events: raise ValueError("events required")
        validate_scope(action_id, events); deadline = time.monotonic() + timeout
        with self.condition:
            while True:
                oldest = self.records[0][0] if self.records else self.sequence + 1
                if after > self.sequence: raise ValueError("future cursor")
                if after < oldest - 1:
                    return {"status": "gap", "records": [], "cursor": after,
                            "oldest": oldest, "latest": self.sequence}
                rows = []; cursor = after; status = None
                for sequence, encoded in self.records:
                    if sequence <= after: continue
                    row = json.loads(encoded); rows.append(row); cursor = sequence
                    status = boundary(row, events, action_id)
                    if status: break
                remaining = deadline - time.monotonic()
                if status or self.closed or remaining <= 0:
                    return {"status": status or ("closed" if self.closed else "timeout"),
                            "records": rows, "cursor": cursor,
                            "cursor_returned_ns": time.perf_counter_ns(),
                            "authority": "none"}
                self.condition.wait(remaining)
