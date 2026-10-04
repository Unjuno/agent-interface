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
        self._external_emit = emit
        self.emit = self._emit_with_release_barrier
        self.release_watchers = []
        self.release_publication_attempted_ids = set()
        self.published_release_ids = set()
        self.release_publication_errors = {}
        self.terminal_publication_errors = {}
        self.admission_publication_errors = {}

    def _emit_with_release_barrier(self, event):
        if type(event) is dict and event.get("event") == "terminal":
            active = self.active
            if active is not None and active[0] == event.get("id"):
                cause = active[1].interruption_snapshot()
                self._publish_release_cause(active[0], active[1], cause)
                failure = self.release_publication_errors.get(active[0])
                if failure is not None:
                    event["input_release_publication"] = {
                        "status": "delivery_unknown", "error": failure}
                event["terminal_ns"] = time.perf_counter_ns()
        if type(event) is dict and event.get("event") == "terminal":
            try:
                self._external_emit(event)
            except Exception as exc:
                self.terminal_publication_errors[event.get("id")] = {
                    "status": "delivery_unknown",
                    "error": {"type": type(exc).__name__}}
                raise
            self.terminal_publication_errors.pop(event.get("id"), None)
            self.release_publication_errors.pop(event.get("id"), None)
        else:
            try:
                self._external_emit(event)
            except Exception as exc:
                if (type(event) is dict and
                        event.get("event") in ("input_released", "input_release_unverified")):
                    identifier = event.get("id")
                    self.release_publication_errors[identifier] = {
                        "type": type(exc).__name__, "message": str(exc)}
                    return
                raise
            if (type(event) is dict and
                    event.get("event") in ("input_released", "input_release_unverified")):
                self.release_publication_errors.pop(event.get("id"), None)

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
            try:
                self.emit({"event": "accepted", "id": identifier,
                           "steps": len(copied), "program_sha256": attestation,
                           "intent_token": lease.intent_token,
                           "valid_until_ns": valid_until_ns,
                           "accepted_ns": time.perf_counter_ns()})
            except Exception as exc:
                # The sink may have accepted the event before losing its ack.
                # Keep the slot occupied, but do not start input without a
                # confirmed admission publication.
                self.admission_publication_errors[identifier] = {
                    "status": "delivery_unknown",
                    "error": {"type": type(exc).__name__}}
                raise
            worker.start()

    def _publish_release(self, identifier, lease):
        cause = lease.wait_interruption(2.0)
        self._publish_release_cause(identifier, lease, cause)

    def _publish_release_cause(self, identifier, lease, cause):
        if cause is None:
            return
        record = cause.get("record")
        if (type(record) is not dict or record.get("event") != "owner_release" or
                record.get("reason") not in ("cancelled", "stop_requested")):
            return
        with self.lock:
            if self.active is None or self.active[0] != identifier:
                return
            # ExecutorV13 can publish the same interruption through its own
            # watcher before this inherited terminal barrier runs.
            if (identifier in self.release_publication_attempted_ids or
                    identifier in self.published_release_ids):
                return
            # A sink can accept the event and still lose its acknowledgement.
            # Keep the boundary at-most-once and report delivery uncertainty.
            self.release_publication_attempted_ids.add(identifier)
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
            try:
                self._external_emit(event)
            except Exception as exc:
                self.release_publication_errors[identifier] = {
                    "type": type(exc).__name__, "message": str(exc)}
                return
            self.published_release_ids.add(identifier)
            self.release_publication_errors.pop(identifier, None)

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
        # A failed accepted-event publication leaves the fail-closed active
        # slot's worker unstarted. The base close path unconditionally joins
        # it, which raises RuntimeError for that state.
        with self.lock:
            self.closed = True
            job = self.active
            if job is not None:
                job[1].set()
        if job is not None and job[2].ident is not None:
            job[2].join()
        for watcher in self.release_watchers:
            watcher.join()
