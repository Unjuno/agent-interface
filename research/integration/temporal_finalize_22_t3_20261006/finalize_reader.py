"""Explicit, bounded tail validation over the unchanged T2 parser/reader.

Linux exclusive pipe ownership only. A prior history receipt is never rewritten.
EOF plus the parser's close record establishes transport completion, not current
world state, source authenticity, task completion, or permission to act/retry.
"""
from __future__ import annotations
import copy
import os
import time
from timed_reader import TimedReader


class FinalizingReader(TimedReader):
    def __init__(self, fd: int):
        super().__init__(fd)
        self.finalize_number = 0

    def finalize(self, deadline_ns: int) -> dict:
        """Consume the remaining bounded protocol; timeout retains partial state.

        This is an explicit caller operation, not a new wait for historical truth.
        An already expired deadline reads nothing, even if data is buffered in OS.
        Like wait(), this API requires no concurrent use of the owned descriptor.
        """
        if type(deadline_ns) is not int or deadline_ns < 0:
            raise ValueError('absolute monotonic integer deadline required')
        if self.closed:
            raise ValueError('reader closed')
        self.finalize_number += 1
        started = time.monotonic_ns()
        reads, messages = [], []

        def result(outcome):
            return {'finalize_id': self.finalize_number, 'outcome': outcome,
                    'started_ns': started, 'deadline_ns': deadline_ns,
                    'returned_ns': time.monotonic_ns(), 'phase': self.stream.phase,
                    'epoch': self.stream.epoch, 'accepted_events': self.stream.count,
                    'partial_bytes': len(self.stream.buffer),
                    'historical_result': copy.deepcopy(self.stream.states),
                    'transport_complete': self.stream.phase == 'CLOSED',
                    'reads': reads, 'messages': messages,
                    'authority': 'none', 'input_dispatched': False, 'task_success': None}

        while True:
            now = time.monotonic_ns()
            if now >= deadline_ns:
                return result('FINALIZE_TIMEOUT_UNRESOLVED')
            if self.stream.phase == 'ERROR':
                return result('TRANSPORT_ERROR')
            if self.stream.phase == 'CLOSED':
                return result('TRANSPORT_COMPLETE')
            # Historical SATISFIED/EXPIRED is deliberately not an exit condition.
            # Clamp each select interval without changing the absolute deadline.
            if not self.selector.select(min(deadline_ns-now, 1_000_000_000)/1_000_000_000):
                continue
            if time.monotonic_ns() >= deadline_ns:
                continue
            before = time.monotonic_ns()
            try:
                data = os.read(self.fd, 4096)
            except BlockingIOError:
                continue
            after = time.monotonic_ns()
            reads.append({'start_ns': before, 'end_ns': after, 'hex': data.hex()})
            messages.extend(self.stream.feed(data) if data else self.stream.finish())
