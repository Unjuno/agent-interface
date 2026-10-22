"""Narrow caller journal for the opt-in inert Win32 operation owner.

This adapter keeps original action outcomes separate from cancellation
transactions so a future guarded-win32 MCP route can expose both through the
existing result lookup. It does not construct a Win32 backend, emit input, or
imply that process exit proves release.
"""
from __future__ import annotations

from copy import deepcopy
import re
import threading
import time
import uuid


_IDENTIFIER = re.compile(r"^[0-9a-f]{32}$")
_PENDING_PHASES = {"cancel_pending", "producer_retired", "recovery_pending"}
_CANCEL_TRANSACTION_NS = 3_000_000_000


class OwnedWin32SessionOwner:
    """Separate action/cancellation receipts around injected custody components.

    The class is deliberately not a subclass of the X11 owner. Its admission
    and producer-start methods are a future caller seam; the current route does
    not instantiate it and no Win32 input adapter is connected.
    """

    def __init__(self, operation_owner, cancellation_supervisor, *, session_id=None):
        if (not callable(getattr(operation_owner, "admit", None))
                or not callable(getattr(operation_owner, "result", None))
                or not callable(getattr(operation_owner, "mark_unknown", None))
                or not callable(getattr(cancellation_supervisor, "cancel", None))
                or not callable(getattr(cancellation_supervisor, "producer_started", None))):
            raise ValueError("operation owner and cancellation supervisor interfaces required")
        if session_id is None:
            session_id = uuid.uuid4().hex
        self._validate_id(session_id, "session_id")
        self.session_id = session_id
        self.mode = "guarded-win32"
        self.state = "open"
        self._owner = operation_owner
        self._supervisor = cancellation_supervisor
        self._lock = threading.RLock()
        self._calls = {}
        self._cancellation_ids = set()

    def admit_action(self, call_id, action_operation_id, target_generation, *,
                     operation_deadline_ns, obligations, action_metadata=None):
        self._validate_id(call_id, "call_id")
        self._validate_id(action_operation_id, "action_operation_id")
        if action_metadata is not None and type(action_metadata) is not dict:
            raise ValueError("action_metadata must be a dictionary")
        with self._lock:
            if self.state != "open":
                raise RuntimeError("Win32 session is not open")
            used_action_ids = {item["action"]["operation_id"]
                               for item in self._calls.values()}
            if (call_id in self._calls or action_operation_id in used_action_ids
                    or action_operation_id in self._cancellation_ids):
                raise ValueError("call or action operation ID already used")
            custody = self._owner.admit(action_operation_id, target_generation,
                                        operation_deadline_ns, obligations)
            self._calls[call_id] = {
                "call_id": call_id,
                "action": {
                    "operation_id": action_operation_id,
                    "target_generation": target_generation,
                    "status": custody["status"],
                    "metadata": deepcopy(action_metadata or {}),
                    "result": None,
                },
                "cancellation": None,
            }
            return self.interface_result(call_id)

    def producer_started(self, call_id, process_handle, *, process_identity):
        with self._lock:
            record = self._calls.get(call_id)
            if record is None:
                raise ValueError("unknown caller action")
            operation_id = record["action"]["operation_id"]
            generation = record["action"]["target_generation"]
        # Identity queries may block. Keep them outside the caller-journal lock
        # so a concurrent cancel can still close admission promptly.
        accepted = self._supervisor.producer_started(
            operation_id, generation, process_handle,
            process_identity=process_identity)
        phase = self._owner.result(operation_id)["phase"]
        with self._lock:
            record = self._calls.get(call_id)
            if record is not None:
                action = record["action"]
                if action["operation_id"] != operation_id:
                    return False
                if phase == "running":
                    action["status"] = "running"
                elif phase == "unknown":
                    action["status"] = "unknown"
        return accepted

    def cancel_guarded(self, call_id, *, cancellation_operation_id=None,
                       cleanup_deadline_ns=None):
        if cleanup_deadline_ns is None:
            cleanup_deadline_ns = time.monotonic_ns() + _CANCEL_TRANSACTION_NS
        if type(cleanup_deadline_ns) is not int:
            raise ValueError("cleanup_deadline_ns must be an integer")
        with self._lock:
            record = self._calls.get(call_id)
            if record is None:
                return self._public_cancel_result(call_id, None)
            cancellation = record["cancellation"]
            if cancellation is not None:
                self._refresh(record)
                return self._public_cancel_result(call_id, cancellation)
            if record["action"]["status"] not in ("admitted", "running"):
                return self._public_cancel_result(call_id, None)
            if cancellation_operation_id is None:
                cancellation_operation_id = uuid.uuid4().hex
            self._validate_id(cancellation_operation_id, "cancellation_operation_id")
            used_action_ids = {item["action"]["operation_id"]
                               for item in self._calls.values()}
            if (cancellation_operation_id in self._cancellation_ids
                    or cancellation_operation_id in used_action_ids):
                raise ValueError("cancellation operation ID already used")
            self._cancellation_ids.add(cancellation_operation_id)
            action = record["action"]
            cancellation = {
                "operation_id": cancellation_operation_id,
                "action_operation_id": action["operation_id"],
                "target_generation": action["target_generation"],
                "status": "pending",
                "release_confirmed": False,
                "task_success": None,
                "replay_allowed": False,
                "result": None,
            }
            record["cancellation"] = cancellation
            try:
                result = self._supervisor.cancel(
                    action["operation_id"], action["target_generation"],
                    cleanup_deadline_ns=cleanup_deadline_ns)
                cancellation["result"] = deepcopy(result)
                self._refresh(record)
            except BaseException as error:
                cancellation.update(status="unknown", error=repr(error),
                    result={"status": "unknown", "release_confirmed": False,
                            "task_success": None, "replay_allowed": False})
                if not isinstance(error, Exception):
                    raise
            return self._public_cancel_result(call_id, cancellation)

    def record_action_result(self, call_id, result):
        if type(result) is not dict:
            raise ValueError("action result must be a dictionary")
        with self._lock:
            record = self._calls.get(call_id)
            if record is None:
                raise ValueError("unknown caller action")
            action = record["action"]
            action["result"] = deepcopy(result)
            action["status"] = result.get("status", "unknown")
            return self.interface_result(call_id)

    def interface_result(self, call_id):
        with self._lock:
            record = self._calls.get(call_id)
            if record is None:
                return None
            self._refresh(record)
            return deepcopy(record)

    def _refresh(self, record):
        cancellation = record.get("cancellation")
        if cancellation is None:
            return
        try:
            result = self._owner.result(cancellation["action_operation_id"])
        except Exception as error:
            cancellation.update(status="unknown", error=repr(error),
                release_confirmed=False, task_success=None, replay_allowed=False)
            return
        phase = result.get("phase")
        status = ("pending" if phase in _PENDING_PHASES else
                  "recovered" if phase == "recovered" else "unknown")
        cancellation.update(status=status, owner_phase=phase,
            release_confirmed=result.get("release_confirmed") is True,
            task_success=None, replay_allowed=False,
            result=deepcopy(result))

    @staticmethod
    def _public_cancel_result(call_id, cancellation):
        if cancellation is None:
            return {"status": "not_active", "call_id": call_id,
                    "release_confirmed": False, "task_success": None,
                    "replay_allowed": False}
        return {
            "status": cancellation["status"],
            "call_id": call_id,
            "operation_id": cancellation["operation_id"],
            "cancellation": deepcopy(cancellation),
            "release_confirmed": cancellation["release_confirmed"],
            "task_success": None,
            "replay_allowed": False,
        }

    @staticmethod
    def _validate_id(value, name):
        if type(value) is not str or _IDENTIFIER.fullmatch(value) is None:
            raise ValueError(name + " must be 32 lowercase hexadecimal characters")

