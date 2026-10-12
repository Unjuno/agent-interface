"""Versioned local RPC boundary for an InputOwner process.

The wire codec is deliberately narrow. It carries the existing lease identity
and observed focus/surface binding; it does not define new input authority.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import select
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lease_release_v1 import Lease


SCHEMA = "input-owner-rpc-v1"
REQUEST_FIELDS = {"schema", "request_id", "op", "lease", "key"}
LEASE_FIELDS = {
    "deadline_ns", "intent_token", "expected_focus", "expected_surface",
    "expected_geometry", "cancel_requested", "focus_invalid",
}
OPERATIONS = frozenset({
    "down", "up", "up_batch", "release", "input_state", "surface_context",
    "move", "button_down", "button_up", "wheel", "continue_move", "close",
})
DOOM_KEYS = frozenset({"Left", "Right", "Up", "Down", "a", "d", "e",
                       "space", "Shift_L"})
MAX_FRAME = 1_048_576
RESPONSE_SCHEMA = "input-owner-rpc-response-v1"
READY_SCHEMA = "input-owner-rpc-ready-v1"
EVENT_SCHEMA = "input-owner-rpc-event-v1"


def encode_lease(lease):
    if lease is None:
        return None
    token = getattr(lease, "intent_token", None)
    cancel = getattr(lease, "cancel", None)
    if (type(getattr(lease, "deadline", None)) is not int
            or not isinstance(token, str) or not token or len(token) > 128
            or not callable(getattr(cancel, "is_set", None))):
        raise ValueError("deadline, intent token, and cancel event required")
    focus = getattr(lease, "expected_focus", None)
    surface = getattr(lease, "expected_surface", None)
    geometry = getattr(lease, "expected_geometry", None)
    if focus is not None and (type(focus) is not int or focus <= 1):
        raise ValueError("observed focus must be a client window ID")
    if surface is not None and (type(surface) is not int or surface <= 1):
        raise ValueError("observed surface must be a client window ID")
    if geometry is not None and (
            type(geometry) not in (list, tuple) or len(geometry) != 4
            or any(type(value) is not int for value in geometry)):
        raise ValueError("observed surface geometry must contain four integers")
    return {
        "deadline_ns": lease.deadline,
        "intent_token": token,
        "expected_focus": focus,
        "expected_surface": surface,
        "expected_geometry": list(geometry) if geometry is not None else None,
        "cancel_requested": bool(cancel.is_set()),
        "focus_invalid": bool(getattr(lease, "focus_invalid", False)),
    }


def decode_lease(dto, leases):
    if type(dto) is not dict or set(dto) != LEASE_FIELDS:
        raise ValueError("exact lease fields required")
    deadline = dto["deadline_ns"]
    token = dto["intent_token"]
    focus = dto["expected_focus"]
    surface = dto["expected_surface"]
    geometry = dto["expected_geometry"]
    if type(deadline) is not int:
        raise ValueError("integer lease deadline required")
    if not isinstance(token, str) or not token or len(token) > 128:
        raise ValueError("valid intent token required")
    if focus is not None and (type(focus) is not int or focus <= 1):
        raise ValueError("observed focus must be a client window ID")
    if surface is not None and (type(surface) is not int or surface <= 1):
        raise ValueError("observed surface must be a client window ID")
    if geometry is not None and (
            type(geometry) is not list or len(geometry) != 4
            or any(type(value) is not int for value in geometry)):
        raise ValueError("observed surface geometry must contain four integers")
    if type(dto["cancel_requested"]) is not bool or type(dto["focus_invalid"]) is not bool:
        raise ValueError("lease state flags must be booleans")

    lease = leases.get(token)
    if lease is None:
        lease = Lease(deadline)
        lease.intent_token = token
        lease.expected_focus = focus
        lease.expected_surface = surface
        lease.expected_geometry = list(geometry) if geometry is not None else None
        lease.focus_invalid = dto["focus_invalid"]
        leases[token] = lease
    elif (lease.deadline != deadline or lease.expected_focus != focus
          or lease.expected_surface != surface
          or lease.expected_geometry != (list(geometry) if geometry is not None else None)):
        raise ValueError("lease identity binding changed")
    if dto["cancel_requested"]:
        lease.cancel.set()
    lease.focus_invalid = lease.focus_invalid or dto["focus_invalid"]
    return lease


def validate_request(request, expected_id):
    if type(request) is not dict or set(request) != REQUEST_FIELDS:
        raise ValueError("exact request fields required")
    if request["schema"] != SCHEMA:
        raise ValueError("unsupported input-owner RPC schema")
    request_id = request["request_id"]
    if type(request_id) is not int or request_id != expected_id or request_id < 1:
        raise ValueError("request id is stale or out of order")
    op = request["op"]
    if not isinstance(op, str) or op not in OPERATIONS:
        raise ValueError("operation not allowlisted")
    lease = request["lease"]
    key = request["key"]
    lease_required = op in {"down", "up", "up_batch", "release", "move", "button_down",
                            "button_up", "wheel", "continue_move"}
    if lease_required and type(lease) is not dict:
        raise ValueError("lease required for input operation")
    if lease is not None and type(lease) is not dict:
        raise ValueError("lease must be an object or null")
    if lease is not None:
        # Validate without allocating a second lease object here.
        decode_lease(lease, {})
    if op in ("down", "up"):
        if not isinstance(key, str) or key not in DOOM_KEYS:
            raise ValueError("key not allowlisted")
    elif op == "up_batch":
        if (type(key) is not list or not key
                or any(not isinstance(item, str) or item not in DOOM_KEYS for item in key)
                or len(key) != len(set(key))):
            raise ValueError("unique allowlisted key batch required")
    elif op in ("button_down", "button_up"):
        if type(key) is not int or key not in (1, 2, 3):
            raise ValueError("button must be 1..3")
    elif op == "wheel":
        if type(key) is not int or key == 0 or abs(key) > 10:
            raise ValueError("wheel count must be -10..10 excluding zero")
    elif op == "move":
        if (type(key) is not dict or set(key) != {"x", "y"}
                or any(type(key[name]) is not int for name in ("x", "y"))):
            raise ValueError("move requires exact integer x/y")
    elif op == "continue_move":
        fields = {"owner_id", "expected_revision", "x", "y", "reply_until_ns"}
        if (type(key) is not dict or set(key) != fields
                or not isinstance(key["owner_id"], str)
                or any(type(key[name]) is not int for name in fields - {"owner_id"})):
            raise ValueError("invalid continuation request")
    elif op == "surface_context":
        if type(key) is not int or key <= 1:
            raise ValueError("client surface ID required")
    elif key is not None:
        raise ValueError("operation does not accept a key payload")
    if op == "down":
        binding = lease["expected_focus"]
        if type(binding) is not int or binding <= 1:
            raise ValueError("observed focus required for keyboard admission")
        if lease["deadline_ns"] <= time.perf_counter_ns():
            raise ValueError("expired lease cannot admit input")
    if op in {"move", "button_down", "button_up", "wheel", "continue_move"}:
        if (type(lease["expected_focus"]) is not int
                or type(lease["expected_surface"]) is not int
                or type(lease["expected_geometry"]) is not list):
            raise ValueError("observed focus, surface, and geometry required")
    return request


def _send_frame(sock, value):
    encoded = (json.dumps(value, separators=(",", ":"), sort_keys=True) + "\n").encode()
    if len(encoded) > MAX_FRAME:
        raise ValueError("RPC frame exceeds limit")
    sock.sendall(encoded)


def _receive_frame(sock, buffer, timeout):
    deadline = time.monotonic() + timeout
    while True:
        newline = buffer.find(b"\n")
        if newline >= 0:
            if newline + 1 > MAX_FRAME:
                raise ValueError("RPC frame exceeds limit")
            line = bytes(buffer[:newline])
            del buffer[:newline + 1]
            return json.loads(line.decode("utf-8"))
        if len(buffer) >= MAX_FRAME:
            raise ValueError("unterminated RPC frame exceeds limit")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("RPC response deadline")
        ready, _, _ = select.select([sock], [], [], remaining)
        if not ready:
            raise TimeoutError("RPC response deadline")
        chunk = sock.recv(min(65536, MAX_FRAME - len(buffer) + 1))
        if not chunk:
            if buffer:
                raise ValueError("partial RPC frame at EOF")
            raise EOFError("input-owner RPC peer closed")
        buffer.extend(chunk)


def _error_payload(exc):
    result = {"type": type(exc).__name__, "message": str(exc)[:1000], "attrs": {}}
    for name in ("owner_explicit_keyup_record", "release_batch_publication",
                 "cancelled_pending_ups"):
        value = getattr(exc, name, None)
        if value is not None:
            try:
                json.dumps(value)
            except (TypeError, ValueError):
                continue
            result["attrs"][name] = value
    return result


def _exception_from_payload(payload):
    from executor_v3 import Cancelled, DecisionRequired
    from lease import Expired

    classes = {cls.__name__: cls for cls in (
        ValueError, RuntimeError, TimeoutError, AssertionError, KeyError,
        Cancelled, DecisionRequired, Expired,
    )}
    name = payload.get("type") if type(payload) is dict else None
    message = payload.get("message") if type(payload) is dict else None
    cls = classes.get(name, RuntimeError)
    exc = cls(message if isinstance(message, str) else "remote input-owner error")
    attrs = payload.get("attrs", {}) if type(payload) is dict else {}
    if type(attrs) is dict:
        for key, value in attrs.items():
            if key in {"owner_explicit_keyup_record", "release_batch_publication",
                       "cancelled_pending_ups"}:
                setattr(exc, key, value)
    return exc


def _receipt_is_verified(receipt):
    releases = receipt.get("release_records") if type(receipt) is dict else None
    return bool(
        type(releases) is list and len(releases) == 1
        and receipt.get("schema") == "input-owner-recovery-v1"
        and receipt.get("receipt_fsynced") is True
        and receipt.get("owner_thread_stopped") is True
        and receipt.get("close_error") is None
        and all(
            type(row) is dict and row.get("event") == "owner_release"
            and row.get("verified") is True and row.get("keys_down") == []
            and row.get("buttons_down") == [] and row.get("keys_unknown") == []
            and row.get("key_state_errors") == []
            for row in releases
        )
    )


def read_recovery_receipt(path, expected_display=None):
    receipt = json.loads(Path(path).read_text(encoding="utf-8"))
    if expected_display is not None and receipt.get("display") != expected_display:
        raise ValueError("recovery receipt display identity mismatch")
    if not _receipt_is_verified(receipt):
        raise RuntimeError("input-owner recovery receipt is missing or unverified")
    return receipt


class InputOwnerProcess:
    """Drop-in process boundary for the measurement-only InputOwner API."""

    def __init__(self, display_name, out, *, rpc_timeout=4.0,
                 owner_service_class="input_transition_owner_v4.InputOwner"):
        if os.name != "posix" or not hasattr(socket, "socketpair"):
            raise RuntimeError("process input owner requires local POSIX socketpair support")
        self.display_name = display_name
        self.out = Path(out)
        self.out.mkdir(parents=True, exist_ok=True)
        self.receipt_path = self.out / "input-owner-recovery-v1.json"
        if self.receipt_path.exists():
            raise FileExistsError("input-owner receipt path already exists")
        self.rpc_timeout = rpc_timeout
        if owner_service_class not in {
                "input_transition_owner_v4.InputOwner",
                "input_transition_owner_v5.InputOwner"}:
            raise ValueError("owner service class is not allowlisted")
        self._owner_service_class = owner_service_class
        self._rpc_lock = threading.Lock()
        self._records_lock = threading.Lock()
        self._records = []
        self._records_version = 0
        self._leases = {}
        self._leases_lock = threading.Lock()
        self._lease_cancel_threads = {}
        self._lease_cancel_stop = threading.Event()
        self._next_request_id = 1
        self._closed = False
        self._event_stop = threading.Event()
        self._rpc_buffer = bytearray()
        self._stderr_path = self.receipt_path.with_suffix(".stderr.log")
        client_rpc, service_rpc = socket.socketpair()
        client_events, service_events = socket.socketpair()
        stderr_file = self._stderr_path.open("wb")
        service_path = str(Path(__file__).resolve())
        try:
            self.process = subprocess.Popen(
                [sys.executable, service_path, "--input-owner-service",
                 str(display_name), str(self.receipt_path),
                 str(service_rpc.fileno()), str(service_events.fileno()),
                 self._owner_service_class],
                pass_fds=(service_rpc.fileno(), service_events.fileno()),
                close_fds=True, start_new_session=True,
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=stderr_file,
            )
        except BaseException:
            client_rpc.close(); service_rpc.close()
            client_events.close(); service_events.close(); stderr_file.close()
            raise
        service_rpc.close()
        service_events.close()
        stderr_file.close()
        self._rpc = client_rpc
        self._events = client_events
        self._out_dir = self.out
        try:
            ready = _receive_frame(self._rpc, self._rpc_buffer, self.rpc_timeout)
            if (type(ready) is not dict or ready.get("schema") != READY_SCHEMA
                    or ready.get("display") != display_name):
                raise RuntimeError("input-owner service readiness handshake invalid")
            if type(ready.get("startup_error")) is dict:
                raise _exception_from_payload(ready["startup_error"])
            if (not isinstance(ready.get("owner_id"), str) or not ready["owner_id"]):
                raise RuntimeError("input-owner service readiness handshake invalid")
            self.owner_id = ready["owner_id"]
            self.service_pid = ready["pid"]
            self._sync_records(ready.get("records_version", 0), ready.get("records", []))
        except BaseException:
            self._rpc.close(); self._events.close()
            try:
                self.process.wait(timeout=self.rpc_timeout)
            except subprocess.TimeoutExpired:
                # Do not kill a service that may be in release cleanup.
                pass
            raise
        self._event_thread = threading.Thread(
            target=self._event_loop, name="input-owner-process-events", daemon=False)
        self._event_thread.start()
        self._cancel_thread = threading.Thread(
            target=self._cancel_loop, name="input-owner-process-cancel", daemon=True)
        self._cancel_thread.start()

    @property
    def records(self):
        with self._records_lock:
            return [dict(record) for record in self._records]

    def _sync_records(self, version, records):
        if type(version) is not int or version < 0 or type(records) is not list:
            raise ValueError("malformed owner-record snapshot")
        callbacks = []
        with self._records_lock:
            if version < self._records_version or len(records) != version:
                return
            if version == self._records_version:
                return
            prior = self._records_version
            self._records = [dict(record) if type(record) is dict else record
                             for record in records]
            self._records_version = version
            for record in self._records[prior:]:
                token = record.get("intent_token") if type(record) is dict else None
                with self._leases_lock:
                    lease = self._leases.get(token)
                if (lease is not None and record.get("event") == "owner_release"
                        and callable(getattr(lease, "record_interruption", None))):
                    callbacks.append((lease, record))
        for lease, record in callbacks:
            lease.record_interruption(record)

    def _event_loop(self):
        buffer = bytearray()
        while not self._event_stop.is_set():
            try:
                event = _receive_frame(self._events, buffer, .25)
            except TimeoutError:
                continue
            except (EOFError, OSError, ValueError, json.JSONDecodeError):
                return
            if type(event) is not dict or event.get("schema") != EVENT_SCHEMA:
                return
            try:
                self._sync_records(event.get("records_version"), event.get("records"))
            except (TypeError, ValueError):
                return

    def _cancel_loop(self):
        while not self._lease_cancel_stop.wait(.01):
            with self._leases_lock:
                leases = list(self._leases.items())
            for token, lease in leases:
                if not lease.cancel.is_set():
                    continue
                with self._leases_lock:
                    sent = self._lease_cancel_threads.get(token)
                    if sent is None or sent.is_set():
                        continue
                # Cancellation is an explicit owner RPC, so a parent-side
                # cancellation reaches the autonomous owner watcher promptly.
                try:
                    self.call("input_state", lease)
                except BaseException:
                    pass
                finally:
                    with self._leases_lock:
                        event = self._lease_cancel_threads.get(token)
                        if event is not None:
                            event.set()
    def call(self, operation, lease=None, key=None):
        if self._closed and operation != "close":
            raise RuntimeError("input-owner process is closed")
        lease_wire = encode_lease(lease)
        if lease is not None:
            with self._leases_lock:
                self._leases[lease_wire["intent_token"]] = lease
                self._lease_cancel_threads.setdefault(lease_wire["intent_token"], threading.Event())
        with self._rpc_lock:
            request_id = self._next_request_id
            request = {"schema": SCHEMA, "request_id": request_id,
                       "op": operation, "lease": lease_wire, "key": key}
            validate_request(request, request_id)
            self._next_request_id += 1
            try:
                _send_frame(self._rpc, request)
                response = _receive_frame(self._rpc, self._rpc_buffer, self.rpc_timeout)
            except (OSError, EOFError, TimeoutError, ValueError) as exc:
                raise RuntimeError("input-owner RPC outcome unknown") from exc
            fields = {"schema", "request_id", "ok", "result", "records_version", "records"}
            if type(response) is not dict or set(response) not in (fields, fields | {"error"}):
                raise RuntimeError("input-owner RPC response fields invalid")
            if (response.get("schema") != RESPONSE_SCHEMA
                    or response.get("request_id") != request_id
                    or type(response.get("ok")) is not bool):
                raise RuntimeError("input-owner RPC response identity invalid")
            self._sync_records(response.get("records_version"), response.get("records"))
            if not response["ok"]:
                raise _exception_from_payload(response.get("error", {}))
            return response.get("result")

    def close(self):
        if self._closed:
            return None
        error = None
        try:
            self.call("close")
        except BaseException as exc:
            error = exc
        self._closed = True
        self._event_stop.set()
        self._lease_cancel_stop.set()
        self._cancel_thread.join(timeout=1)
        try:
            return_code = self.process.wait(timeout=self.rpc_timeout)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("input-owner process exit not observed; do not reuse display") from exc
        finally:
            try: self._rpc.close()
            except OSError: pass
            try: self._events.close()
            except OSError: pass
            self._event_thread.join(timeout=self.rpc_timeout)
        if error is not None:
            raise error
        if return_code != 0:
            raise RuntimeError(f"input-owner process exited {return_code}; do not reuse display")
        read_recovery_receipt(self.receipt_path, self.display_name)
        return None


def _write_receipt(path, receipt):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    data = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def _owner_service(display_name, receipt_path, rpc_fd, event_fd):
    rpc = socket.socket(fileno=rpc_fd)
    events = socket.socket(fileno=event_fd)
    try:
        module_name, class_name = sys.argv[6].rsplit(".", 1)
        if (module_name, class_name) == ("input_transition_owner_v4", "InputOwner"):
            from input_transition_owner_v4 import InputOwner as Owner
        elif (module_name, class_name) == ("input_transition_owner_v5", "InputOwner"):
            from input_transition_owner_v5 import InputOwner as Owner
        else:
            raise ValueError("owner service class is not allowlisted")
        owner = Owner(display_name)
    except BaseException as exc:
        try:
            _send_frame(rpc, {"schema": READY_SCHEMA, "display": display_name,
                              "startup_error": _error_payload(exc)})
        finally:
            rpc.close(); events.close()
        return 4
    stop_events = threading.Event()
    event_errors = []
    last_sent = [0]
    leases = {}
    expected_id = 1
    records_lock = threading.Lock()

    def publish_records():
        while not stop_events.is_set():
            try:
                records = owner.records
                with records_lock:
                    version = len(records)
                    if version > last_sent[0]:
                        _send_frame(events, {"schema": EVENT_SCHEMA,
                                             "records_version": version,
                                             "records": records})
                        last_sent[0] = version
            except (OSError, ValueError, TypeError) as exc:
                event_errors.append(type(exc).__name__)
                return
            stop_events.wait(.002)

    event_thread = threading.Thread(
        target=publish_records, name="input-owner-record-publisher", daemon=True)
    records = owner.records
    _send_frame(rpc, {"schema": READY_SCHEMA, "owner_id": owner.owner_id,
                      "display": display_name, "pid": os.getpid(),
                      "records_version": len(records), "records": records})
    event_thread.start()
    buffer = bytearray()
    reason = "rpc_eof"
    close_error = None
    pending_response = None
    closed = False
    exit_code = 0
    while True:
        try:
            frame = _receive_frame(rpc, buffer, .1)
        except TimeoutError:
            continue
        except EOFError:
            reason = "rpc_eof"
            break
        except BaseException as exc:
            reason = "invalid_frame"
            pending_response = {"request_id": None, "ok": False,
                                "error": _error_payload(exc), "result": None}
            exit_code = 2
            break
        try:
            request = validate_request(frame, expected_id)
            lease = decode_lease(request["lease"], leases) if request["lease"] is not None else None
        except BaseException as exc:
            reason = "invalid_request"
            pending_response = {"request_id": frame.get("request_id") if type(frame) is dict else None,
                                "ok": False, "error": _error_payload(exc), "result": None}
            exit_code = 2
            break
        expected_id += 1
        if request["op"] == "close":
            reason = "requested_close"
            try:
                owner.close()
                result = None
            except BaseException as exc:
                close_error = _error_payload(exc)
                result = None
                exit_code = 1
            closed = True
            pending_response = {"request_id": request["request_id"],
                                "ok": close_error is None, "result": result,
                                "error": close_error}
            break
        try:
            result = owner.call(request["op"], lease, request["key"])
            response = {"request_id": request["request_id"], "ok": True,
                        "result": result}
        except BaseException as exc:
            response = {"request_id": request["request_id"], "ok": False,
                        "result": None, "error": _error_payload(exc)}
        current_records = owner.records
        response.update({"schema": RESPONSE_SCHEMA,
                         "records_version": len(current_records),
                         "records": current_records})
        try:
            _send_frame(rpc, response)
        except OSError:
            reason = "rpc_eof"
            break

    if not closed:
        try:
            owner.close()
        except BaseException as exc:
            close_error = _error_payload(exc)
            exit_code = 1
    stop_events.set()
    event_thread.join(timeout=2)
    records = owner.records
    inner = getattr(owner, "_inner", None)
    stopped = getattr(inner, "stopped", None)
    thread_stopped = bool(stopped is not None and stopped.is_set())
    release_records = [record for record in records
                       if type(record) is dict and record.get("event") == "owner_release"]
    receipt = {
        "schema": "input-owner-recovery-v1",
        "display": display_name,
        "service_pid": os.getpid(),
        "trigger": reason,
        "closed_ns": time.perf_counter_ns(),
        "owner_id": owner.owner_id,
        "owner_thread_stopped": thread_stopped,
        "release_records": release_records,
        "owner_records": records,
        "close_error": close_error,
        "event_publisher_errors": event_errors,
        "receipt_fsynced": True,
    }
    receipt["recovery_verified"] = _receipt_is_verified(receipt)
    try:
        _write_receipt(receipt_path, receipt)
    except BaseException:
        exit_code = 3
    if pending_response is not None:
        final_records = owner.records
        pending_response.update({"schema": RESPONSE_SCHEMA,
                                 "records_version": len(final_records),
                                 "records": final_records})
        try:
            _send_frame(rpc, pending_response)
        except OSError:
            pass
    try:
        rpc.close(); events.close()
    except OSError:
        pass
    return exit_code


if __name__ == "__main__" and len(sys.argv) == 7 and sys.argv[1] == "--input-owner-service":
    raise SystemExit(_owner_service(sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])))
