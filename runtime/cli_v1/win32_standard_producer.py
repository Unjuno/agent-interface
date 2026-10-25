"""Gated native Win32 producer for one frozen standard program."""
from __future__ import annotations

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


def _run_standard_program(start_gate, targets, action, packet_path):
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
        backend = Win32Backend(targets)
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


class NativeWin32StandardProducerFactory:
    """Create one gated child and retain its single-use result packet reader."""

    def __init__(self, targets, output_directory, *, context=None,
                 process_identity_reader=None):
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
        self._lock = threading.Lock()
        self._process_data = {}
        self._consumed = set()

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
        directory = self._root / call_id
        directory.mkdir(exist_ok=False)
        packet_path = directory / "producer-result.json"
        gate = self._context.Event()
        process = self._context.Process(target=_run_standard_program,
            args=(gate, self._targets, action, str(packet_path)), daemon=True)
        with self._lock:
            if id(process) in self._process_data:
                raise RuntimeError("producer process identity collision")
            self._process_data[id(process)] = {
                "call_id": call_id,
                "operation_id": action["operation_id"],
                "target_generation": action["target_generation"],
                "packet_path": packet_path,
            }
        return process, lambda: self._identity_reader(process), gate.set

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
        return {"result": packet["result"],
                "release_receipt": packet["release_receipt"],
                "producer_timing": packet["producer_timing"]}
