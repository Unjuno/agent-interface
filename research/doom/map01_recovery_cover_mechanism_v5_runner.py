"""Formal MAP01 bounded-recovery mechanism v5 runner.

V5 preserves the v4 frozen mechanism and measurement contract, changing only
session event waiting so unrelated events are retained rather than destructively
consumed while awaiting another receipt.
"""
from __future__ import annotations
from collections import deque
import queue
import time

ALLOCATION_ID = "map01-recovery-cover-mechanism-live-v5-01"
WORKFLOW_PATH = ".github/workflows/map01-recovery-cover-mechanism-live-v5-01.yml"


def configure():
    import map01_recovery_cover_matched_v2_runner as base
    from map01_recovery_cover_mechanism_v4_measurement import fallback_input_bounds

    class PreservingJsonSession(base.JsonSession):
        def __init__(self, command):
            super().__init__(command)
            self._pending = deque()

        def wait(self, predicate, timeout: float = 20.0):
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                for _ in range(len(self._pending)):
                    row = self._pending.popleft()
                    if predicate(row):
                        return row
                    self._pending.append(row)
                try:
                    row = self.queue.get(timeout=min(0.1, max(0.01, deadline - time.monotonic())))
                except queue.Empty:
                    if self.process.poll() is not None:
                        assert self.process.stderr is not None
                        raise base.SessionError(self.process.stderr.read().strip() or "session exited")
                    continue
                if predicate(row):
                    return row
                self._pending.append(row)
            raise TimeoutError("session event timeout")

    base.ALLOCATION_ID = ALLOCATION_ID
    base.EXPECTED_WORKFLOW_PATH = WORKFLOW_PATH
    base.fallback_input_bounds = fallback_input_bounds
    base.JsonSession = PreservingJsonSession
    return base


def main() -> None:
    configure().main()


if __name__ == "__main__":
    main()
