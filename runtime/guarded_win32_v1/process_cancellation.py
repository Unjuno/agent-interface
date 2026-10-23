"""Inert process-lifecycle supervisor for the Win32 operation custody gate.

This module does not import Win32 APIs or send input. Recovery and observation
helpers start and report ready before operations are admitted. Cancellation
closes admission synchronously, retires the exact producer, then reuses those
helpers for recovery and independent neutral-state readback. This synthetic
mechanism is not evidence of native input release or an OS-level hard
real-time bound.
"""
from __future__ import annotations

import queue
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
        self._startup_timeout_s = float(startup_timeout_s)
        self._helpers = {}
        self._thread = None
        try:
            self._helpers["recovery"] = self._start_helper(
                "recovery", self._recovery_process_factory)
            self._helpers["observer"] = self._start_helper(
                "observer", self._observer_process_factory)
        except BaseException as error:
            self._close_helpers()
            raise RuntimeError(
                "prestarted cancellation helper failed readiness: " + str(error)
            ) from error
        self._ready = threading.Event()
        self._thread = threading.Thread(target=self._serve,
            name="win32-operation-cancel-supervisor", daemon=True)
        self._thread.start()
        if not self._ready.wait(self._startup_timeout_s):
            self.close()
            raise RuntimeError("cancellation helper did not start before deadline")

    def _start_helper(self, name, factory):
        process = connection = None
        try:
            process, connection = factory()
            if (not callable(getattr(process, "start", None))
                    or not callable(getattr(process, "join", None))
                    or not callable(getattr(process, "is_alive", None))
                    or not hasattr(process, "exitcode")
                    or getattr(process, "pid", None) is not None
                    or not all(callable(getattr(connection, attr, None))
                               for attr in ("poll", "recv", "send", "close"))):
                raise ValueError("helper factory must return an unstarted process and duplex connection")
            process.start()
            identity = self._process_identity_reader(process)
            if not self._valid_process_identity(process, identity):
                raise ValueError(name + " helper process identity is invalid")
            if (not connection.poll(self._startup_timeout_s)
                    or not process.is_alive()):
                raise TimeoutError(name + " helper readiness timed out")
            ready = connection.recv()
            if (ready != {"status": "ready", "helper": name}
                    or not process.is_alive()
                    or self._process_identity_reader(process) != identity):
                raise ValueError(name + " helper readiness or identity mismatched")
            return {"process": process, "connection": connection,
                    "identity": identity, "available": True,
                    "lock": threading.Lock()}
        except BaseException:
            if process is not None:
                self._stop_gated_child(process)
                try:
                    if not process.is_alive():
                        process.close()
                except BaseException:
                    pass
            if connection is not None:
                try:
                    connection.close()
                except BaseException:
                    pass
            raise

    @staticmethod
    def _valid_process_identity(process, identity):
        return (type(identity) is dict
            and set(identity) == {"pid", "creation_time_100ns"}
            and type(identity["pid"]) is int
            and identity["pid"] == process.pid
            and type(identity["creation_time_100ns"]) is int
            and identity["creation_time_100ns"] > 0)

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

    def _exchange_helper(self, name, request, deadline_ns):
        helper = self._helpers[name]
        process = helper["process"]
        connection = helper["connection"]
        request_id = request["request_id"]
        cutoff_ns = deadline_ns - int(
            (self._terminate_grace_s + self._kill_grace_s) * 1_000_000_000)
        with helper["lock"]:
            try:
                if (not helper["available"] or not process.is_alive()
                        or self._process_identity_reader(process) != helper["identity"]):
                    raise RuntimeError("prestarted helper is unavailable or identity changed")
                connection.send(request)
                result = completion = None
                while self._clock_ns() < cutoff_ns:
                    if not connection.poll(self._bounded_wait(cutoff_ns,
                                                               self._poll_interval_s)):
                        continue
                    message = connection.recv()
                    if type(message) is not dict:
                        raise ValueError("helper returned a non-object message")
                    if message.get("control") == "operation_complete":
                        if (completion is not None
                                or message.get("request_id") != request_id):
                            raise ValueError("helper completion identity mismatched")
                        completion = message
                    elif result is None:
                        result = message
                    else:
                        raise ValueError("helper returned duplicate result messages")
                    if result is not None and completion is not None:
                        break
                if (result is None or completion is None
                        or self._clock_ns() >= deadline_ns
                        or not process.is_alive()
                        or self._process_identity_reader(process) != helper["identity"]):
                    raise TimeoutError("helper result, completion or identity unconfirmed")
                return result
            except BaseException:
                helper["available"] = False
                self._retire_process(process, deadline_ns)
                raise

    def _invalidate_helper(self, name, deadline_ns):
        helper = self._helpers[name]
        with helper["lock"]:
            helper["available"] = False
            self._retire_process(helper["process"], deadline_ns)

    def _run_recovery(self, operation_id, generation, request):
        if self._clock_ns() >= request["deadline_ns"]:
            self._owner.expire_cleanup(operation_id, generation)
            return
        recovery_request = dict(request)
        recovery_request["request_id"] = request["recovery_id"]
        try:
            receipt = self._exchange_helper("recovery", recovery_request,
                                            request["deadline_ns"])
        except TimeoutError:
            self._owner.mark_unknown(operation_id, generation,
                "recovery_process_exceeded_execution_window")
            return
        except BaseException:
            self._owner.mark_unknown(operation_id, generation,
                "recovery_process_or_readback_unconfirmed")
            return
        valid = (type(receipt) is dict
            and receipt.get("operation_id") == operation_id
            and receipt.get("target_generation") == generation
            and receipt.get("recovery_id") == request["recovery_id"]
            and receipt.get("release_accepted") is True)
        if not valid or self._clock_ns() >= request["deadline_ns"]:
            self._invalidate_helper("recovery", request["deadline_ns"])
            self._owner.mark_unknown(operation_id, generation,
                "recovery_receipt_invalid_or_late")
            return
        readback = self._run_observer(operation_id, generation, request)
        if readback is None:
            return
        self._owner.recovery_completed(operation_id, generation,
            request["recovery_id"], release_accepted=True, readback=readback)

    def _run_observer(self, operation_id, generation, request):
        observation_request = dict(request)
        observation_request["request_id"] = request["recovery_id"]
        try:
            readback = self._exchange_helper("observer", observation_request,
                                             request["deadline_ns"])
        except TimeoutError:
            self._owner.mark_unknown(operation_id, generation,
                "independent_readback_observer_exceeded_execution_window")
            return None
        except BaseException:
            self._owner.mark_unknown(operation_id, generation,
                "independent_readback_observer_unconfirmed")
            return None
        if (type(readback) is not dict
                or readback.get("operation_id") != operation_id
                or readback.get("target_generation") != generation
                or readback.get("recovery_id") != request["recovery_id"]):
            self._invalidate_helper("observer", request["deadline_ns"])
            self._owner.mark_unknown(operation_id, generation,
                "independent_readback_identity_mismatch")
            return None
        return readback

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
        if self._thread is not None:
            self._thread.join(1.0)
        self._close_helpers()

    def _close_helpers(self):
        for helper in self._helpers.values():
            process = helper["process"]
            connection = helper["connection"]
            helper["available"] = False
            if process.is_alive():
                try:
                    connection.send(None)
                    process.join(min(0.1, self._startup_timeout_s))
                except BaseException:
                    pass
            if process.is_alive():
                deadline_ns = self._clock_ns() + int(
                    (self._terminate_grace_s + self._kill_grace_s + 0.1)
                    * 1_000_000_000)
                self._retire_process(process, deadline_ns)
            try:
                connection.close()
            except BaseException:
                pass
            try:
                if not process.is_alive():
                    process.close()
            except BaseException:
                pass
        self._helpers.clear()
