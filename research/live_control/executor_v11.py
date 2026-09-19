"""Executor v3 behavior with validated-program SHA-256 attestation."""
import copy
import hashlib
import json
import threading
import time

from executor_v3 import (
    Cancelled, DecisionRequired, Executor as Previous)
from lease import Lease


def program_sha256(steps):
    encoded = json.dumps(steps, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class Executor(Previous):
    """Keep v3 exception identities and lifecycle; add acceptance attestation."""

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
            self.backend.validate(copied)
            lease.check()
            attestation = program_sha256(copied)
            self.backend.lease = lease
            thread = threading.Thread(
                target=self._run, args=(identifier, copied, lease), daemon=False)
            self.active = (identifier, lease, thread)
            self.used_ids.add(identifier)
            self.emit({"event": "accepted", "id": identifier,
                       "steps": len(copied), "program_sha256": attestation,
                       "valid_until_ns": valid_until_ns,
                       "accepted_ns": time.perf_counter_ns()})
            thread.start()
