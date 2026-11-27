"""Gated native Win32 producer for one frozen standard program."""
from __future__ import annotations

import ctypes
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import sys
import threading
import time

from runtime.guarded_win32_v1.win32_process_identity import Win32ProcessIdentityReader


def _write_packet(path, packet):
    encoded = json.dumps(packet, ensure_ascii=False, separators=(",", ":"),
                         allow_nan=False).encode("utf-8")
    with Path(path).open("xb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())


def _release_receipt(result):
    if type(result) is not dict:
        return {"verified": False, "keys_down": [], "buttons_down": [],
                "keys_unknown": ["producer_result_missing"],
                "buttons_unknown": []}
    detail = result.get("execution")
    if type(detail) is dict:
        releases = detail.get("releases")
        if type(releases) is list and releases and type(releases[-1]) is dict:
            return releases[-1]
    release = result.get("release")
    if type(release) is dict:
        return release
    return {"verified": False, "keys_down": [], "buttons_down": [],
            "keys_unknown": ["producer_release_receipt_missing"],
            "buttons_unknown": []}


def _run_standard_program(start_gate, targets, action, packet_path,
                         program_action_counter, program_operation_receipts):
    if not start_gate.wait():
        return
    producer_ready_ns = time.monotonic_ns()
    program = action["program"]
    source = program["source"]
    packet = {
        "call_id": action["call_id"],
        "operation_id": action["operation_id"],
        "target_generation": action["target_generation"],
        "producer_timing": {
            "clock": "time.monotonic_ns",
            "child_ready_monotonic_ns": producer_ready_ns,
        },
    }
    backend = session = None
    try:
        if sys.platform != "win32":
            raise OSError("native Win32 producer requires Windows")
        from runtime.backends.win32_v1.backend import Win32Backend
        from runtime.backends.win32_v1.session import Win32RuntimeSession
        backend = Win32Backend(targets,
            program_emission_counter=program_action_counter,
            program_operation_receipts=program_operation_receipts)
        session = Win32RuntimeSession(backend)
        result = session.dispatch(program,
            current_observation_seq=source["observation_seq"],
            current_binding_revision=source["binding_revision"])
        packet.update(result=result, release_receipt=_release_receipt(result))
    except BaseException as error:
        packet.update(result={"status": "runtime_failed",
            "error_type": type(error).__name__, "detail": str(error)[:512]},
            release_receipt={"verified": False, "keys_down": [],
                "buttons_down": [], "keys_unknown": ["producer_exception"],
                "buttons_unknown": []})
    finally:
        if backend is not None:
            try:
                packet["backend_close"] = backend.close()
            except BaseException as error:
                packet["backend_close"] = {"status": "unknown",
                                           "error_type": type(error).__name__}
        try:
            _write_packet(packet_path, packet)
        except BaseException:
            # Missing or partial output is retained as an unconfirmed producer
            # result by the parent. Never retry a possibly emitted program.
            pass


def _run_prestarted_standard_worker(connection, targets, action_counter,
                                    operation_receipts, max_operations):
    """Wait idle before authority, accept one bound request, then retire."""
    connection.send({"status": "ready", "protocol": "win32-producer-v1"})
    try:
        request = connection.recv()
        if (type(request) is not dict
                or set(request) != {"action", "packet_path", "operation_count",
                                    "request_sha256"}):
            return
        action = request["action"]
        operation_count = request["operation_count"]
        if (type(action) is not dict
                or type(operation_count) is not int
                or not 0 < operation_count <= max_operations
                or type(request["packet_path"]) is not str
                or type(request["request_sha256"]) is not str):
            return
        encoded = json.dumps({"action": action,
            "packet_path": request["packet_path"],
            "operation_count": operation_count}, sort_keys=True,
            separators=(",", ":"), ensure_ascii=False,
            allow_nan=False).encode("utf-8")
        digest = hashlib.sha256(encoded).hexdigest()
        if digest != request["request_sha256"]:
            return
        identity = {"call_id": action.get("call_id"),
            "operation_id": action.get("operation_id"),
            "target_generation": action.get("target_generation"),
            "request_sha256": digest}
        connection.send({"status": "prepared", **identity})
        authorization = connection.recv()
        if (type(authorization) is not dict
                or authorization != {"status": "authorize", **identity}):
            return
        if hasattr(action_counter, "value"):
            action_counter.value = 0
        for index in range(operation_count * 4):
            operation_receipts[index] = 0
        gate = threading.Event()
        gate.set()
        _run_standard_program(gate, targets, action, request["packet_path"],
                              action_counter, operation_receipts)
    finally:
        connection.close()


class NativeWin32StandardProducerFactory:
    """Create one gated child and retain its single-use result packet reader."""

    def __init__(self, targets, output_directory, *, context=None,
                 process_identity_reader=None, prestarted=False,
                 worker_startup_timeout_s=60.0, max_operations=2048):
        if sys.platform != "win32":
            raise OSError("native Win32 producer requires Windows")
        if (type(targets) is not dict or not targets
                or any(type(name) is not str or type(hwnd) is not int or hwnd <= 0
                       for name, hwnd in targets.items())):
            raise ValueError("explicit target names and native HWNDs required")
        self._targets = dict(targets)
        self._root = Path(output_directory).resolve()
        self._root.mkdir(parents=True, exist_ok=True)
        self._context = context or multiprocessing.get_context("spawn")
        self._identity_reader = process_identity_reader or Win32ProcessIdentityReader()
        if (type(prestarted) is not bool
                or type(worker_startup_timeout_s) not in (int, float)
                or worker_startup_timeout_s <= 0
                or type(max_operations) is not int or max_operations <= 0):
            raise ValueError("invalid prestarted worker configuration")
        self.prestarted = prestarted
        self._worker_startup_timeout_s = float(worker_startup_timeout_s)
        self._request_ack_timeout_s = 1.0
        self._max_operations = max_operations
        self._lock = threading.Lock()
        self._worker_start_lock = threading.RLock()
        self._process_data = {}
        self._consumed = set()
        self._worker = None
        self._worker_connection = None
        self._worker_ready = False
        self._closed = False
        if self.prestarted:
            self._start_prestarted_worker()

    def __call__(self, action):
        required = {"call_id", "operation_id", "target_generation", "program"}
        if type(action) is not dict or not required <= set(action):
            raise ValueError("admitted standard Win32 action required")
        call_id = action["call_id"]
        if (type(call_id) is not str or len(call_id) != 32
                or any(ch not in "0123456789abcdef" for ch in call_id)):
            raise ValueError("standard action call ID is invalid")
        program = action["program"]
        if type(program) is not dict or type(program.get("source")) is not dict:
            raise ValueError("frozen standard program required")
        program_action_counter = self._context.RawValue(ctypes.c_long, 0)
        if ctypes.addressof(program_action_counter) % 4 != 0:
            raise RuntimeError("native producer action counter is misaligned")
        operations = program.get("ops")
        if type(operations) is not list or not operations:
            raise ValueError("standard Win32 program operations are invalid")
        if self.prestarted:
            return self._assign_prestarted_worker(action, operations)
        program_operation_receipts = self._context.RawArray(
            ctypes.c_long, len(operations) * 4)
        if ctypes.addressof(program_operation_receipts) % 4 != 0:
            raise RuntimeError("native producer operation receipt buffer is misaligned")
        directory = self._root / call_id
        directory.mkdir(exist_ok=False)
        packet_path = directory / "producer-result.json"
        gate = self._context.Event()
        process = self._context.Process(target=_run_standard_program,
            args=(gate, self._targets, action, str(packet_path),
                  program_action_counter, program_operation_receipts), daemon=True)
        with self._lock:
            if id(process) in self._process_data:
                raise RuntimeError("producer process identity collision")
            self._process_data[id(process)] = {
                "call_id": call_id,
                "operation_id": action["operation_id"],
                "target_generation": action["target_generation"],
                "packet_path": packet_path,
                "program_action_counter": program_action_counter,
                "program_operation_receipts": program_operation_receipts,
                "program_operation_count": len(operations),
            }
        return process, lambda: self._identity_reader(process), gate.set

    def _start_prestarted_worker(self):
        with self._worker_start_lock:
            with self._lock:
                if self._closed:
                    return
                if (self._worker_ready is True and self._worker is not None
                        and self._worker.is_alive() is True):
                    return
            parent, child = self._context.Pipe(duplex=True)
            try:
                action_counter = self._context.RawValue(ctypes.c_long, 0)
                operation_receipts = self._context.RawArray(
                    ctypes.c_long, self._max_operations * 4)
                process = self._context.Process(
                    target=_run_prestarted_standard_worker,
                    args=(child, self._targets, action_counter,
                          operation_receipts, self._max_operations), daemon=True)
            except BaseException:
                parent.close()
                child.close()
                raise
            try:
                process.start()
                child.close()
                if not parent.poll(self._worker_startup_timeout_s):
                    raise TimeoutError("prestarted Win32 producer readiness timed out")
                ready = parent.recv()
                if ready != {"status": "ready", "protocol": "win32-producer-v1"}:
                    raise RuntimeError("prestarted Win32 producer readiness mismatch")
            except BaseException:
                try:
                    if getattr(process, "pid", None) is not None and process.is_alive():
                        process.terminate()
                        process.join(1.0)
                finally:
                    parent.close()
                raise
            with self._lock:
                self._worker = process
                self._worker_connection = parent
                self._worker_action_counter = action_counter
                self._worker_operation_receipts = operation_receipts
                self._worker_ready = True

    def ensure_ready(self):
        """Confirm a ready slot before the caller admits an action lease."""
        with self._worker_start_lock:
            with self._lock:
                if (self._worker_ready is True and self._worker is not None
                        and self._worker.is_alive() is True):
                    return True
                process, connection = self._worker, self._worker_connection
                if process is not None and process.is_alive() is True:
                    return False
                self._worker = None
                self._worker_connection = None
                self._worker_ready = False
            if connection is not None:
                connection.close()
            try:
                self._start_prestarted_worker()
            except Exception:
                return False
            return True

    def _replenish_after_retirement(self, process):
        if not self.prestarted or process.is_alive() is not False:
            return
        with self._worker_start_lock:
            with self._lock:
                if self._worker is not process:
                    return
                if self._closed:
                    return
                old_connection = self._worker_connection
                self._worker = None
                self._worker_connection = None
                self._worker_ready = False
            if old_connection is not None:
                old_connection.close()
            threading.Thread(target=self._start_prestarted_worker,
                name="win32-producer-prewarm", daemon=True).start()

    def _assign_prestarted_worker(self, action, operations):
        if len(operations) > self._max_operations:
            raise ValueError("standard Win32 program exceeds worker operation capacity")
        call_id = action["call_id"]
        directory = self._root / call_id
        directory.mkdir(exist_ok=False)
        packet_path = directory / "producer-result.json"
        with self._lock:
            process = self._worker
            connection = self._worker_connection
            if (not self._worker_ready or process is None or connection is None
                    or process.is_alive() is not True):
                raise RuntimeError("prestarted Win32 producer is unavailable")
            self._worker_ready = False
            body = {"action": action, "packet_path": str(packet_path),
                "operation_count": len(operations)}
            encoded = json.dumps(body, sort_keys=True, separators=(",", ":"),
                ensure_ascii=False, allow_nan=False).encode("utf-8")
            digest = hashlib.sha256(encoded).hexdigest()
            try:
                connection.send({**body, "request_sha256": digest})
                if not connection.poll(self._request_ack_timeout_s):
                    raise TimeoutError("prestarted Win32 producer did not prepare request")
                prepared = connection.recv()
                expected = {"status": "prepared", "call_id": action["call_id"],
                    "operation_id": action["operation_id"],
                    "target_generation": action["target_generation"],
                    "request_sha256": digest}
                if prepared != expected:
                    raise RuntimeError(
                        "prestarted Win32 producer request identity mismatch")
            except BaseException:
                if process.is_alive():
                    process.terminate()
                    process.join(1.0)
                connection.close()
                self._worker = None
                self._worker_connection = None
                self._worker_ready = False
                raise
            self._process_data[id(process)] = {
                "call_id": call_id, "operation_id": action["operation_id"],
                "target_generation": action["target_generation"],
                "packet_path": packet_path,
                "program_action_counter": self._worker_action_counter,
                "program_operation_receipts": self._worker_operation_receipts,
                "program_operation_count": len(operations),
                "request_sha256": digest, "connection": connection,
            }

        def authorize():
            connection.send({"status": "authorize", "call_id": call_id,
                "operation_id": action["operation_id"],
                "target_generation": action["target_generation"],
                "request_sha256": digest})

        return process, lambda: self._identity_reader(process), authorize

    def close(self):
        with self._worker_start_lock:
            with self._lock:
                self._closed = True
                process, connection = self._worker, self._worker_connection
                self._worker_ready = False
                self._worker = None
                self._worker_connection = None
        if process is None:
            return {"status": "closed", "worker_retired": True}
        if process.is_alive():
            try:
                if connection is not None:
                    connection.send({"status": "close"})
                process.join(1.0)
            except (EOFError, OSError):
                pass
            if process.is_alive():
                process.terminate()
                process.join(1.0)
        if connection is not None:
            connection.close()
        retired = process.is_alive() is False and type(process.exitcode) is int
        return {"status": "closed" if retired else "unknown",
                "worker_retired": retired}

    def read_program_actions_lower_bound(self, process):
        """Read OS-accepted program input actions after child retirement."""
        with self._lock:
            data = self._process_data.get(id(process))
            if data is None:
                raise ValueError("unknown native producer process")
            counter = data["program_action_counter"]
        if (type(counter) is not ctypes.c_long
                or ctypes.addressof(counter) % 4 != 0):
            raise RuntimeError("native producer action counter is invalid")
        value = counter.value
        if type(value) is not int or value < 0:
            raise RuntimeError("native producer action counter is invalid")
        return value

    def read_program_operation_receipts(self, process):
        """Read crash-tolerant per-operation boundary and native-input receipts."""
        with self._lock:
            data = self._process_data.get(id(process))
            if data is None:
                raise ValueError("unknown native producer process")
            if process.is_alive() is not False or type(process.exitcode) is not int:
                raise ValueError("native producer retirement is unconfirmed")
            buffer = data["program_operation_receipts"]
            count = data["program_operation_count"]
        if len(buffer) < count * 4 or ctypes.addressof(buffer) % 4 != 0:
            raise RuntimeError("native producer operation receipt buffer is invalid")
        phases = {0: "not_started", 1: "boundary_check", 2: "operation_running",
            3: "sendinput_in_flight", 4: "sendinput_returned", 5: "completed",
            6: "lease_refused_before_sendinput", 7: "sendinput_raised_or_rejected",
            8: "local_action_in_flight", 9: "local_action_returned"}
        operations = []
        for index in range(count):
            offset = index * 4
            phase, attempts, returned, local_actions = (
                int(buffer[offset + part]) for part in range(4))
            if (phase not in phases or min(attempts, returned, local_actions) < 0
                    or returned > attempts):
                raise RuntimeError("native producer operation receipt is invalid")
            operations.append({"operation_index": index,
                "phase": phases[phase], "sendinput_attempts": attempts,
                "sendinput_returned_count": returned,
                "local_action_count": local_actions})
        receipt = {"schema": "win32-program-operation-receipts-v1",
            "status": "observed", "operations": operations,
            "observed_monotonic_ns": time.monotonic_ns(),
            "counter_scope": "per-operation SendInput returns and local SetCursorPos actions; not application effect"}
        return receipt

    def read_result(self, process):
        with self._lock:
            data = self._process_data.get(id(process))
            if data is None:
                raise ValueError("unknown native producer process")
            if id(process) in self._consumed:
                raise ValueError("native producer result already consumed")
        if process.is_alive() is not False or type(process.exitcode) is not int:
            raise RuntimeError("native producer exit is unconfirmed")
        try:
            packet = json.loads(data["packet_path"].read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise RuntimeError("native producer result packet unavailable") from error
        expected = {"call_id": data["call_id"],
                    "operation_id": data["operation_id"],
                    "target_generation": data["target_generation"]}
        if (type(packet) is not dict or any(packet.get(key) != value
                                           for key, value in expected.items())
                or type(packet.get("result")) is not dict
                or type(packet.get("release_receipt")) is not dict
                or type(packet.get("producer_timing")) is not dict
                or set(packet["producer_timing"])
                    != {"clock", "child_ready_monotonic_ns"}
                or packet["producer_timing"].get("clock")
                    != "time.monotonic_ns"
                or type(packet["producer_timing"]["child_ready_monotonic_ns"])
                    is not int
                or packet["producer_timing"]["child_ready_monotonic_ns"] <= 0):
            raise RuntimeError("native producer result identity or schema mismatch")
        with self._lock:
            self._consumed.add(id(process))
        result = {"result": packet["result"],
                "release_receipt": packet["release_receipt"],
                "producer_timing": packet["producer_timing"]}
        return result
