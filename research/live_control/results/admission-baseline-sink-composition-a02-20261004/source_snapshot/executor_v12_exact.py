"""Attested Executor with asynchronous, lease-bound physical-release publication."""
import copy
import threading
import time

from executor_v5 import Executor as Previous
from executor_v11 import program_sha256
from lease_release_v1 import Lease


class Executor(Previous):
    def __init__(self, backend, emit):
        super().__init__(backend, emit)
        self.release_watchers = []
        self.published_release_ids = set()

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
            worker = threading.Thread(
                target=self._run, args=(identifier, copied, lease), daemon=False)
            self.active = (identifier, lease, worker)
            self.used_ids.add(identifier)
            self.emit({"event": "accepted", "id": identifier,
                       "steps": len(copied), "program_sha256": attestation,
                       "intent_token": lease.intent_token,
                       "valid_until_ns": valid_until_ns,
                       "accepted_ns": time.perf_counter_ns()})
            worker.start()

    def _publish_release(self, identifier, lease):
        cause = lease.wait_interruption(2.0)
        if cause is None:
            return
        record = cause.get("record")
        if (type(record) is not dict or record.get("event") != "owner_release" or
                record.get("reason") not in ("cancelled", "stop_requested")):
            return
        with self.lock:
            if self.active is None or self.active[0] != identifier:
                return
            if identifier in self.published_release_ids:
                return
            self.published_release_ids.add(identifier)
            event = {"event": "input_released", "id": identifier,
                   "intent_token": cause["intent_token"],
                   "owner_release": record,
                   "published_ns": time.perf_counter_ns(),
                   "program_terminal_pending": True,
                   "grants_input_authority": False}
            if (record.get("verified") is not True or
                    record.get("keys_down") != [] or
                    record.get("buttons_down") != []):
                event["event"] = "input_release_unverified"
            self.emit(event)

    def cancel(self, identifier):
        with self.lock:
            matched = self.active is not None and self.active[0] == identifier
            lease = self.active[1] if matched else None
            if matched:
                lease.set()
            event = {"event": "cancel_requested", "id": identifier,
                     "matched": matched, "requested_ns": time.perf_counter_ns()}
            self.emit(event)
            if matched:
                watcher = threading.Thread(
                    target=self._publish_release, args=(identifier, lease), daemon=False)
                self.release_watchers.append(watcher)
                watcher.start()
            return matched

    def close(self):
        super().close()
        for watcher in self.release_watchers:
            watcher.join()
