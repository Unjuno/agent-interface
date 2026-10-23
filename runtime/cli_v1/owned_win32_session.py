"""Narrow caller journal for the opt-in inert Win32 operation owner.

This adapter keeps original action outcomes separate from cancellation
transactions for the opt-in synthetic guarded-win32 MCP route. It does not
construct a Win32 backend, emit input, or imply that process exit proves release.
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
_TARGET_BINDING_TTL_NS = 60_000_000_000
_MAX_TARGET_BINDINGS = 64


class OwnedWin32SessionOwner:
    """Separate action/cancellation receipts around injected custody components.

    The class is deliberately not a subclass of the X11 owner. Its opt-in MCP
    seam binds a one-use target-generation receipt before caller/model delay,
    then re-reads generation at admission. It does not construct a Win32 backend
    or connect a native input adapter.
    """

    def __init__(self, operation_owner, cancellation_supervisor, *, session_id=None):
        if (not callable(getattr(operation_owner, "admit", None))
                or not callable(getattr(operation_owner, "result", None))
                or not callable(getattr(operation_owner, "mark_unknown", None))
                or not callable(getattr(operation_owner, "authorize_producer_start", None))
                or not callable(getattr(cancellation_supervisor, "cancel", None))
                or not callable(getattr(cancellation_supervisor, "producer_started", None))
                or not callable(getattr(cancellation_supervisor, "close", None))):
            raise ValueError("operation owner and cancellation supervisor interfaces required")
        if session_id is None:
            session_id = uuid.uuid4().hex
        self._validate_id(session_id, "session_id")
        self.session_id = session_id
        self.mode = "guarded-win32"
        self.synthetic_only = True
        self.state = "open"
        self._owner = operation_owner
        self._supervisor = cancellation_supervisor
        self._target_generation_reader = None
        self._lock = threading.RLock()
        self._calls = {}
        self._cancellation_ids = set()
        self._target_bindings = {}

    def bind_target_generation_reader(self, reader):
        """Bind a host-supplied identity query; this adapter never opens Win32 APIs."""
        if not callable(reader):
            raise ValueError("target generation reader required")
        with self._lock:
            if self._calls or self.state != "open":
                raise RuntimeError("target generation reader must be bound before admission")
            self._target_generation_reader = reader

    def current_target_generation(self):
        reader = self._target_generation_reader
        if not callable(reader):
            raise RuntimeError("target generation reader is not configured")
        generation = reader()
        if type(generation) is not str or re.fullmatch(r"[0-9a-f]{64}", generation) is None:
            raise ValueError("configured target generation must be a SHA-256 digest")
        return generation

    def bind_target_generation(self):
        """Issue a one-use generation receipt before an external/model wait."""
        generation = self.current_target_generation()
        binding_id = uuid.uuid4().hex
        now_ns = time.monotonic_ns()
        with self._lock:
            if self.state != "open":
                raise RuntimeError("Win32 session is not open")
            self._target_bindings = {key: value for key, value in self._target_bindings.items()
                if value["expires_at_ns"] > now_ns}
            if len(self._target_bindings) >= _MAX_TARGET_BINDINGS:
                raise RuntimeError("target generation binding capacity exhausted")
            self._target_bindings[binding_id] = {
                "generation": generation,
                "expires_at_ns": now_ns + _TARGET_BINDING_TTL_NS,
            }
        return {"status": "bound", "target_binding_id": binding_id,
                "target_generation": generation,
                "expires_in_ms": _TARGET_BINDING_TTL_NS // 1_000_000,
                "visual_observation": False, "input_dispatched": False,
                "task_success": None, "replay_allowed": False}

    def admit_action_from_binding(self, call_id, action_operation_id,
                                  target_binding_id, *, operation_deadline_ns,
                                  obligations, action_metadata=None):
        self._validate_id(target_binding_id, "target_binding_id")
        with self._lock:
            binding = self._target_bindings.pop(target_binding_id, None)
        if binding is None:
            raise ValueError("target binding is unknown or already consumed")
        if time.monotonic_ns() >= binding["expires_at_ns"]:
            raise ValueError("target binding expired; bind the target again")
        generation = binding["generation"]
        if self.current_target_generation() != generation:
            raise RuntimeError("TARGET_GENERATION_CHANGED")
        # Admission freezes the exact generation observed before the wait.
        return self.admit_action(call_id, action_operation_id, generation,
            operation_deadline_ns=operation_deadline_ns,
            obligations=obligations, action_metadata=action_metadata)

    def close(self):
        with self._lock:
            if self.state == "closed":
                return {"status": "closed", "release_confirmed": False,
                        "task_success": None, "replay_allowed": False}
            for record in self._calls.values():
                phase = self._owner.result(record["action"]["operation_id"]).get("phase")
                if phase != "recovered":
                    return {"status": "busy", "release_confirmed": False,
                            "task_success": None, "replay_allowed": False,
                            "unresolved_operation_id": record["action"]["operation_id"]}
            self.state = "closed"
            self._target_bindings.clear()
        self._supervisor.close()
        return {"status": "closed", "release_confirmed": False,
                "task_success": None, "replay_allowed": False}

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
                elif phase == "cancel_pending":
                    action["status"] = "cancel_pending"
                elif phase == "unknown":
                    action["status"] = "unknown"
        return accepted

    def start_producer(self, call_id, producer_factory):
        """Start an injected gated producer only after custody admission.

        The factory returns (unstarted_process, exact_process_identity,
        authorize_start). The child must wait on its private start gate until
        authorize_start is called after the parent has retained and verified
        the exact child identity. A concurrent cancel wins that race and leaves
        the child gated for the cancellation supervisor to retire.
        """
        if not callable(producer_factory):
            raise ValueError("producer factory required")
        with self._lock:
            record = self._calls.get(call_id)
            if record is None:
                raise ValueError("unknown caller action")
            action = deepcopy(record["action"])
            if action["status"] != "admitted":
                return self.interface_result(call_id)
            record["action"]["status"] = "starting"
        process = None
        try:
            produced = producer_factory(action)
            if (not isinstance(produced, tuple) or len(produced) != 3):
                raise ValueError("producer factory must return process, identity and start gate")
            process, process_identity, authorize_start = produced
            if (not callable(getattr(process, "start", None))
                    or getattr(process, "pid", None) is not None
                    or not callable(authorize_start)):
                raise ValueError("producer must be an unstarted process with a start gate")
            phase = self._owner.result(action["operation_id"]).get("phase")
            if phase not in ("admitted", "cancel_pending"):
                self._close_unstarted_process(process)
                return self.interface_result(call_id)
            process.start()
            if callable(process_identity):
                process_identity = process_identity()
            accepted = self.producer_started(call_id, process,
                process_identity=process_identity)
            phase = self._owner.result(action["operation_id"]).get("phase")
            if accepted:
                authorized = self._owner.authorize_producer_start(
                    action["operation_id"], action["target_generation"],
                    process, authorize_start)
                phase = self._owner.result(action["operation_id"]).get("phase")
                if not authorized and phase != "cancel_pending":
                    self._retire_gated_process(process)
            elif phase != "cancel_pending":
                self._retire_gated_process(process)
            return self.interface_result(call_id)
        except Exception as error:
            try:
                phase = self._owner.result(action["operation_id"]).get("phase")
            except Exception:
                phase = "unknown"
            if phase in ("running", "cancel_pending"):
                try:
                    self.cancel_guarded(call_id,
                        cleanup_deadline_ns=time.monotonic_ns() + _CANCEL_TRANSACTION_NS)
                except Exception:
                    self._owner.mark_unknown(action["operation_id"],
                        action["target_generation"], "producer_start_or_registration_failed")
            else:
                self._owner.mark_unknown(action["operation_id"],
                    action["target_generation"], "producer_start_or_registration_failed")
            with self._lock:
                current = self._calls.get(call_id)
                if current is not None and phase not in ("running", "cancel_pending"):
                    current["action"].update(status="unknown",
                        result={"status": "unknown", "error": repr(error),
                                "task_success": None, "replay_allowed": False})
            if process is not None:
                if getattr(process, "pid", None) is None:
                    self._close_unstarted_process(process)
                elif phase not in ("running", "cancel_pending"):
                    self._retire_gated_process(process)
            return self.interface_result(call_id)

    @staticmethod
    def _close_unstarted_process(process):
        close = getattr(process, "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                pass

    @staticmethod
    def _retire_gated_process(process):
        """Boundedly retire a rejected child that has never passed its start gate."""
        try:
            if process.is_alive():
                process.terminate()
                process.join(0.1)
            if process.is_alive():
                kill = getattr(process, "kill", None)
                if callable(kill):
                    kill()
                    process.join(0.1)
            if process.is_alive() is False:
                process.close()
        except Exception:
            # The start gate stays closed, so failure remains contained and
            # the operation's existing UNKNOWN receipt is preserved.
            return

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
            if record["action"]["status"] not in ("admitted", "starting", "running"):
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

    def list_results(self):
        with self._lock:
            rows = []
            for call_id in reversed(tuple(self._calls)):
                record = self._calls[call_id]
                self._refresh(record)
                rows.append({"call_id": call_id,
                             "operation": "guarded_win32_admit",
                             "state": record["action"]["status"]})
            return rows

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

