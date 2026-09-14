"""Executor v4 resolves explicit coordinate frames before whole-program validation."""
import copy
import threading
import time

from executor_v3 import Executor as Previous
from lease import Lease


class Executor(Previous):
    def submit(self, identifier, steps, expected_sequence, valid_until_ns):
        with self.lock:
            if self.closed or self.active is not None:
                raise ValueError("closed or busy; no implicit queue")
            if type(expected_sequence) is not int or expected_sequence != self.backend.sequence:
                raise ValueError("latest observation sequence required before input")
            if not isinstance(identifier, str) or not identifier or identifier in self.used_ids:
                raise ValueError("new nonempty id required")
            lease = Lease(valid_until_ns)
            lease.check()
            copied = copy.deepcopy(steps)
            prepared, resolutions = self.backend.prepare(copied, identifier)
            self.backend.validate(prepared)
            lease.check()
            cancel = lease
            self.backend.lease = lease
            thread = threading.Thread(target=self._run,
                                      args=(identifier, prepared, cancel), daemon=False)
            self.active = (identifier, cancel, thread)
            self.used_ids.add(identifier)
            for resolution in resolutions:
                self.emit({**resolution, "id": identifier,
                           "resolved_ns": time.perf_counter_ns()})
            self.emit({"event": "accepted", "id": identifier,
                       "steps": len(prepared), "coordinate_resolutions": len(resolutions),
                       "valid_until_ns": valid_until_ns,
                       "accepted_ns": time.perf_counter_ns()})
            thread.start()
