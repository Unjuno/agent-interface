"""Opt-in research spans; no deadlines, recovery decisions or inputs are changed.

Spans stay in bounded process-local memory. Helpers flush only after their
original service loop returns; the server must flush after transport shutdown.
Instrumentation has overhead and is not evidence of uninstrumented latency.
"""
from __future__ import annotations
from contextlib import contextmanager
from functools import wraps
import json
import os
from pathlib import Path
import sys
import threading
import time
import uuid

_active = None


def _request_fields(request):
    if type(request) is not dict:
        return {}
    return {key: request[key] for key in
        ("operation_id", "target_generation", "recovery_id", "request_id")
        if type(request.get(key)) is str}


class StageTrace:
    def __init__(self, output_dir, *, limit=1024, clock_ns=time.perf_counter_ns):
        self.output_dir = Path(output_dir).resolve()
        if not self.output_dir.is_dir():
            raise ValueError("existing attempt-owned trace directory required")
        if type(limit) is not int or not 1 <= limit <= 2048:
            raise ValueError("trace limit must be in 1..2048")
        self._limit = limit
        self._clock = clock_ns
        self._spans = []
        self._dropped = 0
        self._lock = threading.Lock()
        self._local = threading.local()
        self._patches = []
        self._seen = set()
        self._output = None
        self._nonce = uuid.uuid4().hex

    @contextmanager
    def scope(self, fields):
        previous = getattr(self._local, "fields", {})
        self._local.fields = {**previous, **fields}
        try:
            yield
        finally:
            self._local.fields = previous

    def first(self, key):
        with self._lock:
            if key in self._seen:
                return False
            if len(self._seen) >= self._limit:
                self._dropped += 1
                return False
            self._seen.add(key)
            return True

    def invoke(self, stage, operation, args, kwargs, fields=None):
        metadata = {**getattr(self._local, "fields", {}), **(fields or {})}
        started = self._clock()
        error_type = None
        result = None
        try:
            result = operation(*args, **kwargs)
            return result
        except BaseException as error:
            error_type = type(error).__name__
            raise
        finally:
            ended = self._clock()
            span = {**metadata, "stage": stage, "start_ns": started,
                "end_ns": ended, "thread_id": threading.get_ident(),
                "outcome": "raised" if error_type else "returned",
                "error_type": error_type}
            if type(result) in (bool, int):
                span["scalar_result"] = result
            if type(result) is dict and type(result.get("release_accepted")) is bool:
                span["release_accepted"] = result["release_accepted"]
            with self._lock:
                if len(self._spans) < self._limit:
                    self._spans.append(span)
                else:
                    self._dropped += 1

    def patch(self, owner, name, stage, *, details=None, predicate=None, scoped=False):
        original = getattr(owner, name)
        @wraps(original)
        def wrapped(*args, **kwargs):
            if predicate is not None and not predicate(args, kwargs):
                return original(*args, **kwargs)
            fields = details(args, kwargs) if details else {}
            if scoped:
                with self.scope(fields):
                    return self.invoke(stage, original, args, kwargs)
            return self.invoke(stage, original, args, kwargs, fields)
        setattr(owner, name, wrapped)
        self._patches.append((owner, name, original, wrapped))
        return original

    def flush(self):
        with self._lock:
            if self._output is not None:
                return self._output
            path = self.output_dir / f"stage-trace-{os.getpid()}-{self._nonce}.json"
            payload = {"schema": "win32-recovery-stage-trace-v1", "pid": os.getpid(),
                "executable": sys.executable, "python": sys.version,
                "clock": "time.perf_counter_ns",
                "injected_clock": self._clock is not time.perf_counter_ns,
                "clock_info": vars(time.get_clock_info("perf_counter")),
                "monotonic_clock_info": vars(time.get_clock_info("monotonic")),
                "span_limit": self._limit, "dropped_spans": self._dropped,
                "input_authority": False, "spans": list(self._spans)}
            with path.open("x", encoding="utf-8", newline="\n") as stream:
                json.dump(payload, stream, indent=2, sort_keys=True)
                stream.write("\n")
            self._output = path
            return path

    def uninstall(self):
        global _active
        for owner, name, original, wrapped in reversed(self._patches):
            if getattr(owner, name) is wrapped:
                setattr(owner, name, original)
        self._patches.clear()
        if _active is self:
            _active = None


class TracedLock:
    """Transparent lock proxy that times waits only inside recovery exchange."""
    def __init__(self, lock, trace):
        self._lock = lock
        self._trace = trace

    def acquire(self, *args, **kwargs):
        if getattr(self._trace._local, "fields", {}).get("role") == "recovery_exchange":
            return self._trace.invoke("helper.lock.acquire", self._lock.acquire,
                                      args, kwargs)
        return self._lock.acquire(*args, **kwargs)

    def release(self):
        if getattr(self._trace._local, "fields", {}).get("role") == "recovery_exchange":
            return self._trace.invoke("helper.lock.release", self._lock.release,
                                      (), {})
        return self._lock.release()


def install(output_dir):
    """Explicitly instrument the current interpreter before helper spawning."""
    global _active
    if _active is not None:
        if _active.output_dir != Path(output_dir).resolve():
            raise RuntimeError("a different stage trace is already installed")
        return _active
    trace = StageTrace(output_dir)
    from runtime.cli_v1 import win32_supervisor_helpers as helpers
    from runtime.cli_v1.owned_win32_session import OwnedWin32SessionOwner
    from runtime.cli_v1.win32_custody_fence import Win32CustodyFence
    from runtime.guarded_win32_v1.process_cancellation import OperationCancellationSupervisor
    from runtime.guarded_win32_v1.operation_owner import OperationOwner
    from runtime.backends.win32_v1.backend import Win32Backend
    from runtime.guarded_win32_v1.win32_process_identity import Win32ProcessIdentityReader
    from multiprocessing.connection import _ConnectionBase
    from multiprocessing.process import BaseProcess

    def arg(args, kwargs, index, name):
        return args[index] if len(args) > index else kwargs.get(name)
    def identity(args, kwargs):
        return {"operation_id": arg(args, kwargs, 1, "operation_id"),
                "target_generation": arg(args, kwargs, 2, "target_generation")}
    trace.patch(OwnedWin32SessionOwner, "cancel_guarded", "caller.cancel",
        details=lambda a, k: {"call_id": arg(a, k, 1, "call_id")})
    trace.patch(Win32CustodyFence, "update", "custody.cancel_pending_write",
        predicate=lambda a, k: k.get("phase") == "cancel_pending", details=identity)
    trace.patch(OperationCancellationSupervisor, "cancel", "supervisor.cancel", details=identity)
    trace.patch(OperationOwner, "request_cancel", "owner.request_cancel", details=identity)
    trace.patch(OperationCancellationSupervisor, "_retire_and_recover",
        "supervisor.retire_and_recover", details=identity)
    trace.patch(OperationCancellationSupervisor, "_retire_process", "producer.retire",
        details=lambda a, k: {"producer_pid": getattr(arg(a, k, 1, "process"), "pid", None)})
    trace.patch(OperationCancellationSupervisor, "_exchange_helper", "recovery.exchange",
        scoped=True,
        predicate=lambda a, k: arg(a, k, 1, "name") == "recovery",
        details=lambda a, k: {**_request_fields(arg(a, k, 2, "request")),
                             "role": "recovery_exchange"})
    trace.patch(OperationCancellationSupervisor, "_send_helper_request", "recovery.send",
        predicate=lambda a, k: getattr(trace._local, "fields", {}).get("role") == "recovery_exchange",
        details=lambda a, k: _request_fields(arg(a, k, 2, "request")))
    trace.patch(Win32ProcessIdentityReader, "__call__", "helper.identity",
        predicate=lambda a, k: getattr(trace._local, "fields", {}).get("role") == "recovery_exchange",
        details=lambda a, k: {"helper_pid": getattr(arg(a, k, 1, "process"), "pid", None)})
    trace.patch(BaseProcess, "is_alive", "helper.process_alive",
        predicate=lambda a, k: getattr(trace._local, "fields", {}).get("role") == "recovery_exchange",
        details=lambda a, k: {"helper_pid": getattr(arg(a, k, 0, "self"), "pid", None)})
    trace.patch(_ConnectionBase, "poll", "helper.pipe_poll",
        predicate=lambda a, k: getattr(trace._local, "fields", {}).get("role")
            in ("recovery_exchange", "recovery_helper"),
        details=lambda a, k: {"timeout": arg(a, k, 1, "timeout")})
    trace.patch(_ConnectionBase, "recv", "helper.pipe_recv",
        predicate=lambda a, k: getattr(trace._local, "fields", {}).get("role")
            in ("recovery_exchange", "recovery_helper"))
    trace.patch(OperationCancellationSupervisor, "_run_observer", "observer.first_exchange",
        predicate=lambda a, k: trace.first(("parent-observe", arg(a, k, 1, "operation_id"))),
        details=identity)
    trace.patch(helpers, "_recover", "helper.recover", scoped=True,
        details=lambda a, k: {**_request_fields(arg(a, k, 0, "request")), "role": "recovery"})
    trace.patch(helpers, "_observe", "helper.first_observe",
        predicate=lambda a, k: trace.first(("child-observe", _request_fields(arg(a, k, 0, "request")).get("operation_id"))),
        details=lambda a, k: _request_fields(arg(a, k, 0, "request")))
    active_recovery = lambda a, k: getattr(trace._local, "fields", {}).get("role") == "recovery"
    for name, stage in (("target_generation", "backend.generation"),
                        ("release_all", "backend.release_all")):
        trace.patch(Win32Backend, name, stage, predicate=active_recovery)
    trace.patch(Win32Backend, "_key_down_state", "backend.key_readback", predicate=active_recovery,
        details=lambda a, k: {"virtual_key": arg(a, k, 1, "vk")})
    trace.patch(Win32Backend, "_send_key", "backend.key_up", predicate=active_recovery,
        details=lambda a, k: {"virtual_key": arg(a, k, 1, "vk"),
            "down": arg(a, k, 2, "down"), "encoding": arg(a, k, 3, "encoding")})
    original_init = Win32Backend.__init__
    @wraps(original_init)
    def initialize(backend, *args, **kwargs):
        if not active_recovery((), {}):
            return original_init(backend, *args, **kwargs)
        result = trace.invoke("backend.construct", original_init, (backend, *args), kwargs)
        trace.patch(backend.user32, "SendInput", "native.SendInput",
            details=lambda a, k: {"event_count": arg(a, k, 0, "cInputs")})
        return result
    Win32Backend.__init__ = initialize
    trace._patches.append((Win32Backend, "__init__", original_init, initialize))
    original_helper = helpers._helper_main
    @wraps(original_helper)
    def helper_main(*args, **kwargs):
        kind = arg(args, kwargs, 0, "kind")
        role = "recovery_helper" if kind == "recovery" else "observer_helper"
        with trace.scope({"role": role, "helper_kind": kind}):
            try:
                return trace.invoke("helper.lifecycle", original_helper, args, kwargs,
                                    {"helper_kind": kind})
            finally:
                trace.flush()
    helpers._helper_main = helper_main
    trace._patches.append((helpers, "_helper_main", original_helper, helper_main))
    original_supervisor_init = OperationCancellationSupervisor.__init__
    @wraps(original_supervisor_init)
    def supervisor_init(supervisor, *args, **kwargs):
        result = original_supervisor_init(supervisor, *args, **kwargs)
        for helper in supervisor._helpers.values():
            helper["lock"] = TracedLock(helper["lock"], trace)
        return result
    OperationCancellationSupervisor.__init__ = supervisor_init
    trace._patches.append((OperationCancellationSupervisor, "__init__",
                           original_supervisor_init, supervisor_init))
    _active = trace
    return trace
