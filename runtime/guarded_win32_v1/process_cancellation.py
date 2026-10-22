"""Inert process-lifecycle supervisor for the Win32 operation custody gate.

This module does not import Win32 APIs or send input. Cancellation closes
admission synchronously; a dedicated helper retires the exact producer and
only then starts a gated recovery child. Recovery is accepted only from an
exact child receipt plus independent parent-side neutral readback before the
same cleanup deadline. This synthetic mechanism is not evidence of native
input release or an OS-level hard real-time bound.
"""
from __future__ import annotations

import queue
import multiprocessing
import threading
import time


class OperationCancellationSupervisor:
    def __init__(self, owner, *, recovery_process_factory,
                 observer_process_factory, process_identity_reader,
                 clock_ns=time.monotonic_ns, terminate_grace_s=0.1,
                 kill_grace_s=0.1, poll_interval_s=0.005,
                 startup_timeout_s=2.0):
        required = (
            "request_cancel", "producer_handle_for_retirement", "producer_retired",
            "claim_recovery", "recovery_completed", "result", "mark_unknown",
            "expire_cleanup",
        )
        if (any(not callable(getattr(owner, name, None)) for name in required)
                or not callable(recovery_process_factory)
                or not callable(observer_process_factory)
                or not callable(process_identity_reader)
                or not callable(clock_ns)):
            raise ValueError("owner, child factories, identity and clock required")
        for value, name, allow_zero in (
                (terminate_grace_s, "terminate_grace_s", True),
                (kill_grace_s, "kill_grace_s", True),
                (poll_interval_s, "poll_interval_s", False),
                (startup_timeout_s, "startup_timeout_s", False)):
            if (type(value) not in (int, float) or value < 0
                    or (not allow_zero and value == 0)):
                raise ValueError(name + " must be positive or nonnegative")
        self._owner = owner
        self._recovery_process_factory = recovery_process_factory
        self._observer_process_factory = observer_process_factory
        self._process_identity_reader = process_identity_reader
        self._clock_ns = clock_ns
        self._terminate_grace_s = float(terminate_grace_s)
        self._kill_grace_s = float(kill_grace_s)
        self._poll_interval_s = float(poll_interval_s)
        # One in-flight command, at most one queued command, and room for the
        # shutdown sentinel even when the helper is occupied.
        self._queue = queue.Queue(maxsize=2)
        self._lock = threading.Lock()
        self._scheduled = set()
        self._closed = False
        self._ready = threading.Event()
        self._thread = threading.Thread(target=self._serve,
            name="win32-operation-cancel-supervisor", daemon=True)
        self._thread.start()
        if not self._ready.wait(float(startup_timeout_s)):
            self.close()
            raise RuntimeError("cancellation helper did not start before deadline")

    def cancel(self, operation_id, target_generation, *, cleanup_deadline_ns):
        receipt = self._owner.request_cancel(operation_id, target_generation,
            cleanup_deadline_ns=cleanup_deadline_ns)
        if receipt["phase"] in ("cancel_pending", "producer_retired",
                                "recovery_pending"):
            self._schedule(operation_id, target_generation)
        return self._owner.result(operation_id)

    def producer_started(self, operation_id, target_generation, process_handle,
                         *, process_identity):
        accepted = self._owner.producer_started(operation_id, target_generation,
            process_handle, process_identity=process_identity)
        if not accepted and self._owner.result(operation_id)["phase"] == "cancel_pending":
            self._schedule(operation_id, target_generation)
        return accepted

    def _schedule(self, operation_id, target_generation):
        with self._lock:
            if self._closed:
                self._owner.mark_unknown(operation_id, target_generation,
                    "cancellation_supervisor_closed")
                return
            if operation_id in self._scheduled:
                return
            self._scheduled.add(operation_id)
            try:
                self._queue.put_nowait((operation_id, target_generation))
            except queue.Full:
                self._scheduled.discard(operation_id)
                self._owner.mark_unknown(operation_id, target_generation,
                    "cancellation_supervisor_capacity_exhausted")

    def _serve(self):
        self._ready.set()
        while True:
            item = self._queue.get()
            if item is None:
                return
            operation_id, generation = item
            try:
                self._retire_and_recover(operation_id, generation)
            except BaseException:
                self._owner.mark_unknown(operation_id, generation,
                    "cancellation_supervisor_exception")
            finally:
                with self._lock:
                    self._scheduled.discard(operation_id)

    def _retire_and_recover(self, operation_id, generation):
        record = self._owner.result(operation_id)
        if record["phase"] != "cancel_pending":
            return
        deadline_ns = record["cleanup_deadline_ns"]
        producer = self._owner.producer_handle_for_retirement(operation_id, generation)
        while producer is None and self._clock_ns() < deadline_ns:
            # Cancellation may win the race with process.start(). Keep custody
            # in this helper until the late handle is registered or the same
            # absolute cleanup deadline expires.
            time.sleep(self._bounded_wait(deadline_ns, self._poll_interval_s))
            producer = self._owner.producer_handle_for_retirement(
                operation_id, generation)
        if producer is None:
            self._owner.expire_cleanup(operation_id, generation)
            return
        if not self._retire_process(producer, deadline_ns):
            self._owner.mark_unknown(operation_id, generation,
                "producer_retirement_unconfirmed")
            return
        if not self._owner.producer_retired(operation_id, generation, producer):
            self._owner.mark_unknown(operation_id, generation,
                "producer_identity_or_exit_unconfirmed")
            return
        request = self._owner.claim_recovery(operation_id, generation)
        if request is None:
            self._owner.expire_cleanup(operation_id, generation)
            return
        self._run_recovery(operation_id, generation, request)

    def _retire_process(self, process, deadline_ns):
        try:
            if process.is_alive():
                process.terminate()
                process.join(self._bounded_wait(deadline_ns, self._terminate_grace_s))
            if process.is_alive():
                kill = getattr(process, "kill", None)
                if not callable(kill) or self._clock_ns() >= deadline_ns:
                    return False
                kill()
                process.join(self._bounded_wait(deadline_ns, self._kill_grace_s))
            return process.is_alive() is False and type(process.exitcode) is int
        except BaseException:
            return False

    def _run_recovery(self, operation_id, generation, request):
        process = receive = None
        start_gate = multiprocessing.get_context().Event()
        try:
            if self._clock_ns() >= request["deadline_ns"]:
                self._owner.expire_cleanup(operation_id, generation)
                return
            process, receive = self._recovery_process_factory(request, start_gate)
            if (not callable(getattr(process, "start", None))
                    or not callable(getattr(process, "join", None))
                    or not callable(getattr(process, "is_alive", None))
                    or not hasattr(process, "exitcode")
                    or getattr(process, "pid", None) is not None
                    or not callable(getattr(receive, "poll", None))
                    or not callable(getattr(receive, "recv", None))):
                raise ValueError("factory must return unstarted process and receive pipe")
            process.start()
            identity = self._process_identity_reader(process)
            if (type(identity) is not dict
                    or set(identity) != {"pid", "creation_time_100ns"}
                    or type(identity["pid"]) is not int or identity["pid"] != process.pid
                    or type(identity["creation_time_100ns"]) is not int
                    or identity["creation_time_100ns"] <= 0):
                raise ValueError("recovery process identity not verified on retained handle")
            if self._clock_ns() >= request["deadline_ns"]:
                self._retire_process(process, request["deadline_ns"])
                self._owner.expire_cleanup(operation_id, generation)
                return
            # Recovery worker must wait on this gate before any input effect.
            start_gate.set()
            # Reserve the terminal slice for terminate/kill/reap instead of
            # waiting until the whole transaction budget has already elapsed.
            recovery_cutoff_ns = request["deadline_ns"] - int(
                (self._terminate_grace_s + self._kill_grace_s) * 1_000_000_000)
            while process.is_alive() and self._clock_ns() < recovery_cutoff_ns:
                process.join(self._bounded_wait(request["deadline_ns"],
                                                 self._poll_interval_s))
            if process.is_alive():
                self._retire_process(process, request["deadline_ns"])
                self._owner.mark_unknown(operation_id, generation,
                    "recovery_process_exceeded_execution_window")
                return
            if (process.exitcode != 0 or self._clock_ns() >= request["deadline_ns"]
                    or not receive.poll(self._bounded_wait(request["deadline_ns"], 0))):
                self._owner.mark_unknown(operation_id, generation,
                    "recovery_child_exit_or_receipt_unconfirmed")
                return
            receipt = receive.recv()
            valid = (type(receipt) is dict
                and receipt.get("operation_id") == operation_id
                and receipt.get("target_generation") == generation
                and receipt.get("recovery_id") == request["recovery_id"]
                and receipt.get("release_accepted") is True)
            if not valid or self._clock_ns() >= request["deadline_ns"]:
                self._owner.mark_unknown(operation_id, generation,
                    "recovery_receipt_invalid_or_late")
                return
            readback = self._run_observer(operation_id, generation, request)
            if readback is None:
                return
            self._owner.recovery_completed(operation_id, generation,
                request["recovery_id"], release_accepted=True, readback=readback)
        except BaseException:
            # The start gate is still closed unless normal validation reached
            # its explicit set(). Retire any child whose factory/start/identity
            # path failed, so a gated worker is not left behind as an orphan.
            if process is not None:
                self._stop_gated_child(process)
            self._owner.mark_unknown(operation_id, generation,
                "recovery_process_or_readback_unconfirmed")
        finally:
            start_gate.clear()
            if receive is not None:
                try:
                    receive.close()
                except BaseException:
                    pass
            if process is not None:
                try:
                    if not process.is_alive():
                        process.close()
                except BaseException:
                    pass

    def _run_observer(self, operation_id, generation, request):
        process = receive = None
        try:
            process, receive = self._observer_process_factory(request)
            if (not callable(getattr(process, "start", None))
                    or not callable(getattr(process, "join", None))
                    or not callable(getattr(process, "is_alive", None))
                    or not hasattr(process, "exitcode")
                    or getattr(process, "pid", None) is not None
                    or not callable(getattr(receive, "poll", None))
                    or not callable(getattr(receive, "recv", None))):
                raise ValueError("observer factory must return unstarted process and pipe")
            process.start()
            identity = self._process_identity_reader(process)
            if (type(identity) is not dict
                    or set(identity) != {"pid", "creation_time_100ns"}
                    or type(identity["pid"]) is not int or identity["pid"] != process.pid
                    or type(identity["creation_time_100ns"]) is not int
                    or identity["creation_time_100ns"] <= 0):
                raise ValueError("observer identity not verified on retained handle")
            cutoff = request["deadline_ns"] - int(
                (self._terminate_grace_s + self._kill_grace_s) * 1_000_000_000)
            while process.is_alive() and self._clock_ns() < cutoff:
                process.join(self._bounded_wait(request["deadline_ns"],
                                                 self._poll_interval_s))
            if process.is_alive():
                self._retire_process(process, request["deadline_ns"])
                self._owner.mark_unknown(operation_id, generation,
                    "independent_readback_observer_exceeded_execution_window")
                return None
            if (process.exitcode != 0 or self._clock_ns() >= request["deadline_ns"]
                    or not receive.poll(self._bounded_wait(request["deadline_ns"], 0))):
                self._owner.mark_unknown(operation_id, generation,
                    "independent_readback_receipt_missing_or_late")
                return None
            readback = receive.recv()
            if (type(readback) is not dict
                    or readback.get("operation_id") != operation_id
                    or readback.get("target_generation") != generation
                    or readback.get("recovery_id") != request["recovery_id"]):
                self._owner.mark_unknown(operation_id, generation,
                    "independent_readback_identity_mismatch")
                return None
            return readback
        except BaseException:
            if process is not None:
                self._stop_gated_child(process)
            self._owner.mark_unknown(operation_id, generation,
                "independent_readback_observer_unconfirmed")
            return None
        finally:
            if receive is not None:
                try:
                    receive.close()
                except BaseException:
                    pass
            if process is not None:
                try:
                    if not process.is_alive():
                        process.close()
                except BaseException:
                    pass

    @staticmethod
    def _stop_gated_child(process):
        try:
            if not process.is_alive():
                return
            process.terminate()
            process.join(0.05)
            if process.is_alive():
                kill = getattr(process, "kill", None)
                if callable(kill):
                    kill()
                    process.join(0.05)
        except BaseException:
            pass

    def _bounded_wait(self, deadline_ns, cap_s):
        remaining = max(0.0, (deadline_ns - self._clock_ns()) / 1_000_000_000)
        return min(float(cap_s), remaining)

    def close(self):
        with self._lock:
            if self._closed:
                return
            self._closed = True
            try:
                self._queue.put_nowait(None)
            except queue.Full:
                pass
        self._thread.join(1.0)
