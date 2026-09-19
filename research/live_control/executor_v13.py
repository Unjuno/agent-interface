"""Publish lease-bound physical release for cancel, focus, surface or expiry."""
import copy
import threading
import time

from executor_v3 import Cancelled, DecisionRequired
from executor_v12 import Executor as Previous
from lease import Expired


INTERRUPTION_REASONS = frozenset(
    ("cancelled", "stop_requested", "focus_changed", "surface_changed", "expired"))


class Executor(Previous):
    def __init__(self, backend, emit):
        super().__init__(backend, emit)
        self.release_watch_stops = {}

    def submit(self, identifier, steps, expected_sequence, valid_until_ns):
        stop = threading.Event()
        self.release_watch_stops[identifier] = stop
        try:
            super().submit(identifier, steps, expected_sequence, valid_until_ns)
        except BaseException:
            self.release_watch_stops.pop(identifier, None)
            raise
        with self.lock:
            lease = self.active[1]
        watcher = threading.Thread(
            target=self._watch_release,
            args=(identifier, lease, stop), daemon=False)
        self.release_watchers.append(watcher)
        watcher.start()

    def _release_event(self, identifier, cause):
        record = cause.get("record") if type(cause) is dict else None
        if (type(record) is not dict or record.get("event") != "owner_release" or
                record.get("reason") not in INTERRUPTION_REASONS):
            return None
        event = {"event": "input_released", "id": identifier,
                 "intent_token": cause["intent_token"],
                 "owner_release": record,
                 "published_ns": time.perf_counter_ns(),
                 "program_terminal_pending": True,
                 "grants_input_authority": False}
        if (record.get("verified") is not True or record.get("keys_down") != [] or
                record.get("buttons_down") != []):
            event["event"] = "input_release_unverified"
        return event

    def _publish_cause_once(self, identifier, lease, *, require_active=True):
        cause = lease.interruption_snapshot()
        event = self._release_event(identifier, cause)
        if event is None:
            return None
        with self.lock:
            if require_active and (self.active is None or self.active[0] != identifier):
                return None
            if identifier in self.published_release_ids:
                return None
            self.published_release_ids.add(identifier)
            self.emit(event)
        return event

    def _watch_release(self, identifier, lease, stop):
        while not stop.is_set():
            if lease.wait_interruption(.01) is not None:
                self._publish_cause_once(identifier, lease)
                return

    def cancel(self, identifier):
        # The submit-time watcher covers explicit cancellation and autonomous
        # owner invalidation uniformly; do not create v12's second watcher.
        with self.lock:
            matched = self.active is not None and self.active[0] == identifier
            if matched:
                self.active[1].set()
            self.emit({"event": "cancel_requested", "id": identifier,
                       "matched": matched, "requested_ns": time.perf_counter_ns()})
            return matched

    def _run(self, identifier, steps, lease):
        status = "completed"; error = None; completed = 0; decision_reason = None
        try:
            for index, step in enumerate(steps):
                if lease.is_set(): raise Cancelled()
                self.emit({"event": "step_started", "id": identifier, "step": index,
                           "operation": step["op"], "issued_ns": time.perf_counter_ns()})
                self.backend.execute(step, lease, identifier, index)
                if lease.is_set(): raise Cancelled()
                completed += 1
                self.emit({"event": "step_completed", "id": identifier, "step": index,
                           "completed_ns": time.perf_counter_ns()})
        except Expired:
            status = "expired"
        except DecisionRequired as exc:
            status = "needs_decision"; decision_reason = str(exc) or None
        except Cancelled:
            status = "cancelled"
        except Exception as exc:
            status = "failed"; error = repr(exc)
        finally:
            # An owner-originated focus/surface event is already available here.
            # For explicit cancellation, allow one owner polling interval before
            # final cleanup so its independently verified record can win.
            if lease.interruption_snapshot() is None and lease.cancel.is_set():
                lease.wait_interruption(.02)
            self._publish_cause_once(identifier, lease)
            try:
                release = self.backend.release_all()
                if release.get("verified") is not True:
                    status = "failed"; error = "input release not verified"
            except Exception as exc:
                release = {"verified": False, "error": repr(exc)}
                status = "failed"
            if status == "completed":
                try:
                    if lease.is_set(): raise Cancelled()
                except Expired:
                    status = "expired"
                except DecisionRequired as exc:
                    status = "needs_decision"; decision_reason = str(exc) or None
                except Cancelled:
                    status = "cancelled"
            interruption = lease.interruption_snapshot()
            if status == "needs_decision" and decision_reason is None and interruption is not None:
                reason = interruption["record"].get("reason")
                if reason in ("focus_changed", "surface_changed"):
                    decision_reason = reason
            # Catch an interruption recorded during final cleanup, before the
            # terminal makes program_terminal_pending false.
            self._publish_cause_once(identifier, lease)
            with self.lock:
                self.emit({"event": "terminal", "id": identifier, "status": status,
                           "error": error, "steps_completed": completed,
                           "release": release, "interruption": interruption,
                           "decision_reason": decision_reason,
                           "terminal_ns": time.perf_counter_ns(),
                           "semantic_completion": "program status only; task scoring is separate"})
                self.active = None
            stop = self.release_watch_stops.get(identifier)
            if stop is not None:
                stop.set()

    def close(self):
        super().close()
        for stop in self.release_watch_stops.values():
            stop.set()
        for watcher in self.release_watchers:
            watcher.join()
