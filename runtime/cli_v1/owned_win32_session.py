"""Caller journal and standard-program custody adapter for Win32 sessions.

The synthetic guarded-win32 route uses inert injected components. The
supervised-win32 route composes a native gated producer with separate recovery
and observation helpers. Both keep action outcomes separate from cancellation
transactions; producer exit alone never proves release.
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

    def __init__(self, operation_owner, cancellation_supervisor, *, session_id=None,
                 synthetic_only=True):
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
        if type(synthetic_only) is not bool:
            raise ValueError("synthetic_only must be a boolean")
        self.mode = "guarded-win32" if synthetic_only else "supervised-win32"
        self.synthetic_only = synthetic_only
        self.state = "open"
        self._owner = operation_owner
        self._supervisor = cancellation_supervisor
        self._target_generation_reader = None
        self._lock = threading.RLock()
        self._calls = {}
        self._producer_handles = {}
        self._cancellation_ids = set()
        self._target_bindings = {}
        self._used_authority_leases = set()

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
            raise RuntimeError("TARGET_GENERATION_UNAVAILABLE")
        try:
            generation = reader()
        except Exception as error:
            raise RuntimeError("TARGET_GENERATION_UNAVAILABLE") from error
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
                                  obligations, action_metadata=None,
                                  standard_program=None):
        self._validate_id(target_binding_id, "target_binding_id")
        with self._lock:
            binding = self._target_bindings.pop(target_binding_id, None)
        if binding is None:
            raise ValueError("target binding is unknown or already consumed")
        if time.monotonic_ns() >= binding["expires_at_ns"]:
            raise ValueError("target binding expired; bind the target again")
        generation = binding["generation"]
        try:
            current_generation = self.current_target_generation()
        except Exception as error:
            raise RuntimeError("TARGET_GENERATION_CHANGED") from error
        if current_generation != generation:
            raise RuntimeError("TARGET_GENERATION_CHANGED")
        # Admission freezes the exact generation observed before the wait.
        return self.admit_action(call_id, action_operation_id, generation,
            operation_deadline_ns=operation_deadline_ns,
            obligations=obligations, action_metadata=action_metadata,
            standard_program=standard_program)

    def admit_standard_action(self, call_id, action_operation_id,
                              target_binding_id, program, *,
                              operation_deadline_ns,
                              current_observation_seq,
                              current_binding_revision):
        """Freeze a standard program's target generation and all input obligations."""
        from runtime.guarded_win32_v1.input_obligations import derive_input_obligations
        if type(program) is not dict:
            raise ValueError("standard program must be an object")
        from runtime.core_v1.contract import validate_program
        validate_program(program)
        if (type(current_observation_seq) is not int
                or type(current_binding_revision) is not int
                or program["source"].get("observation_seq") != current_observation_seq
                or program["source"].get("binding_revision") != current_binding_revision):
            raise ValueError("STANDARD_SOURCE_BINDING_MISMATCH")
        program_id = program.get("program_id")
        if type(program_id) is not str or not program_id:
            raise ValueError("standard program ID is required")
        focused_target = None
        action_targets = set()
        target_actions = {"key_chord", "key_state", "text", "pointer_move",
                          "pointer_button", "scroll", "observe"}
        for operation in program["ops"]:
            kind = operation["op"]
            if kind in ("focus", "activate"):
                focused_target = operation["target"]
                action_targets.add(focused_target)
            elif kind in target_actions:
                if not isinstance(focused_target, str):
                    raise ValueError("TARGET_GENERATION_REQUIRES_EXPLICIT_FOCUS")
                action_targets.add(focused_target)
        if len(action_targets) != 1:
            raise ValueError("standard Win32 dispatch requires exactly one focused target")
        target = next(iter(action_targets))
        expected_generations = program["source"].get("target_generations")
        try:
            current_generation = self.current_target_generation()
        except Exception as error:
            raise ValueError("TARGET_GENERATION_UNAVAILABLE") from error
        if expected_generations != {target: current_generation}:
            raise ValueError("TARGET_GENERATION_CHANGED")
        obligations = derive_input_obligations(program)
        return self.admit_action_from_binding(call_id, action_operation_id,
            target_binding_id, operation_deadline_ns=operation_deadline_ns,
            obligations=obligations,
            action_metadata={"source": "interface_dispatch",
                             "program_id": program_id},
            standard_program=program)

    def close(self):
        with self._lock:
            if self.state == "closed":
                return {"status": "closed", "release_confirmed": False,
                        "task_success": None, "replay_allowed": False}
            for record in self._calls.values():
                phase = self._owner.result(record["action"]["operation_id"]).get("phase")
                if phase not in ("recovered", "completed"):
                    return {"status": "busy", "release_confirmed": False,
                            "task_success": None, "replay_allowed": False,
                            "unresolved_operation_id": record["action"]["operation_id"]}
            self.state = "closed"
            self._target_bindings.clear()
        self._supervisor.close()
        return {"status": "closed", "release_confirmed": False,
                "task_success": None, "replay_allowed": False}

    def snapshot(self):
        """Return a small custody summary for standard MCP audit records."""
        with self._lock:
            unresolved = []
            for call_id, record in self._calls.items():
                phase = self._owner.result(record["action"]["operation_id"]).get("phase")
                if phase not in ("recovered", "completed"):
                    unresolved.append(call_id)
            return {"session_id": self.session_id, "mode": self.mode,
                "state": self.state, "synthetic_only": self.synthetic_only,
                "call_count": len(self._calls),
                "unresolved_call_ids": unresolved}

    def admit_action(self, call_id, action_operation_id, target_generation, *,
                     operation_deadline_ns, obligations, action_metadata=None,
                     standard_program=None):
        self._validate_id(call_id, "call_id")
        self._validate_id(action_operation_id, "action_operation_id")
        if action_metadata is not None and type(action_metadata) is not dict:
            raise ValueError("action_metadata must be a dictionary")
        authority_lease = None
        if standard_program is not None:
            if (type(standard_program) is not dict
                    or type(standard_program.get("authority")) is not dict):
                raise ValueError("standard program authority is required")
            authority_lease = standard_program["authority"].get("lease_id")
            if type(authority_lease) is not str or not authority_lease:
                raise ValueError("standard program authority lease is required")
        with self._lock:
            if self.state != "open":
                raise RuntimeError("Win32 session is not open")
            if (authority_lease is not None
                    and authority_lease in self._used_authority_leases):
                raise ValueError("authority lease ID already used")
            used_action_ids = {item["action"]["operation_id"]
                               for item in self._calls.values()}
            if (call_id in self._calls or action_operation_id in used_action_ids
                    or action_operation_id in self._cancellation_ids):
                raise ValueError("call or action operation ID already used")
            custody = self._owner.admit(action_operation_id, target_generation,
                                        operation_deadline_ns, obligations,
                                        start_gate_required=True)
            if authority_lease is not None:
                self._used_authority_leases.add(authority_lease)
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
                "task_effect": None,
                "standard_program": (deepcopy(standard_program)
                                     if standard_program is not None else None),
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
                self._producer_handles[call_id] = process_handle
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
        Recheck target generation before factory work and after process-identity
        waits. These point checks are not atomic with native target changes.
        """
        if not callable(producer_factory):
            raise ValueError("producer factory required")
        with self._lock:
            record = self._calls.get(call_id)
            if record is None:
                raise ValueError("unknown caller action")
            action = deepcopy(record["action"])
            standard_program = deepcopy(record.get("standard_program"))
            if action["status"] != "admitted":
                return self.interface_result(call_id)
            record["action"]["status"] = "starting"
        process = None
        try:
            generation_error = self._start_generation_error(action)
            if generation_error is not None:
                return self._refuse_start_generation(call_id, action, generation_error)
            producer_request = deepcopy(action)
            producer_request["call_id"] = call_id
            if standard_program is not None:
                producer_request["program"] = standard_program
            self._stamp_producer_timing(
                call_id, "factory_requested_monotonic_ns")
            produced = producer_factory(producer_request)
            self._stamp_producer_timing(
                call_id, "factory_returned_monotonic_ns")
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
            self._stamp_producer_timing(
                call_id, "process_start_called_monotonic_ns")
            process.start()
            self._stamp_producer_timing(
                call_id, "process_start_returned_monotonic_ns")
            if callable(process_identity):
                process_identity = process_identity()
            accepted = self.producer_started(call_id, process,
                process_identity=process_identity)
            if accepted:
                self._stamp_producer_timing(
                    call_id, "identity_verified_monotonic_ns")
            phase = self._owner.result(action["operation_id"]).get("phase")
            if accepted:
                # Factory/start/identity queries may block. Recheck after those
                # waits, outside custody locks, while the child is still gated.
                generation_error = self._start_generation_error(action)
                if generation_error is not None:
                    result = self._refuse_start_generation(call_id, action, generation_error)
                    self._retire_gated_process(process)
                    return result
                authorized = self._owner.authorize_producer_start(
                    action["operation_id"], action["target_generation"],
                    process, authorize_start)
                if authorized:
                    self._stamp_producer_timing(
                        call_id, "start_gate_authorized_monotonic_ns")
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

    def _start_generation_error(self, action):
        try:
            current = self.current_target_generation()
        except Exception:
            return "target_generation_unavailable_before_start"
        if current != action["target_generation"]:
            return "target_generation_changed_before_start"
        return None

    def _refuse_start_generation(self, call_id, action, reason):
        # The start gate has never opened. Do not request compensating input
        # against a target whose current identity is no longer established.
        self._owner.mark_unknown(action["operation_id"], action["target_generation"], reason)
        with self._lock:
            self._calls[call_id]["action"].update(status="unknown", result={
                "status": "unknown", "error": reason,
                "task_success": None, "replay_allowed": False})
        return self.interface_result(call_id)

    def _stamp_producer_timing(self, call_id, field):
        with self._lock:
            record = self._calls.get(call_id)
            if record is not None:
                timing = record["action"].setdefault("producer_timing", {})
                timing.setdefault("clock", "time.monotonic_ns")
                timing[field] = time.monotonic_ns()

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

    def complete_action(self, call_id, process_handle, result, *, release_receipt,
                        readback, producer_timing=None):
        """Retain a standard dispatch result after custody confirms normal exit.

        The backend result remains separate from the owner custody receipt.
        Process completion alone cannot confirm release or task success.
        """
        if type(result) is not dict:
            raise ValueError("standard action result must be a dictionary")
        if producer_timing is not None and (
                type(producer_timing) is not dict
                or set(producer_timing) != {"clock", "child_ready_monotonic_ns"}
                or producer_timing["clock"] != "time.monotonic_ns"
                or type(producer_timing["child_ready_monotonic_ns"]) is not int
                or producer_timing["child_ready_monotonic_ns"] <= 0):
            raise ValueError("standard producer timing receipt is invalid")
        with self._lock:
            record = self._calls.get(call_id)
            if record is None:
                raise ValueError("unknown caller action")
            action = record["action"]
            operation_id = action["operation_id"]
            generation = action["target_generation"]
        custody = self._owner.producer_completed(operation_id, generation,
            process_handle, release_receipt=release_receipt, readback=readback)
        with self._lock:
            record = self._calls.get(call_id)
            if record is None or record["action"]["operation_id"] != operation_id:
                raise ValueError("caller action changed during completion")
            action = record["action"]
            action.update(status=custody["phase"], result=deepcopy(result),
                release_confirmed=custody["release_confirmed"],
                task_success=None, replay_allowed=False,
                completion_custody=deepcopy(custody))
            if producer_timing is not None:
                action.setdefault("producer_timing", {}).update(
                    deepcopy(producer_timing))
            return deepcopy(record)

    def complete_exited_action(self, call_id, *, result_reader, readback_reader):
        """Collect one exited producer result and independent neutral readback.

        The result reader runs only after the retained process handle reports an
        exact exit code. It must return separate backend result and release
        receipt fields; the observer receives the bound action and parent exit
        witness. Missing or malformed evidence leaves custody UNKNOWN.
        """
        if not callable(result_reader) or not callable(readback_reader):
            raise ValueError("producer result and independent readback readers required")
        with self._lock:
            record = self._calls.get(call_id)
            process_handle = self._producer_handles.get(call_id)
            if record is None or process_handle is None:
                raise ValueError("unknown caller action or producer")
            action = deepcopy(record["action"])
            if action["status"] != "running" or record["cancellation"] is not None:
                return self.interface_result(call_id)

        def retain_unknown(error_code, error_type=None):
            try:
                phase = self._owner.result(action["operation_id"])["phase"]
            except Exception:
                phase = "unknown"
            if phase == "running":
                self._owner.mark_unknown(action["operation_id"],
                    action["target_generation"], error_code.lower())
            result = {"status": "unknown", "error": error_code,
                      "task_success": None, "replay_allowed": False}
            if error_type is not None:
                result["error_type"] = error_type
            with self._lock:
                current = self._calls.get(call_id)
                if current is None or current["cancellation"] is not None:
                    return self.interface_result(call_id)
                current["action"].update(status="unknown", result=result,
                    release_confirmed=False, task_success=None,
                    replay_allowed=False)
            return self.interface_result(call_id)
        try:
            alive = process_handle.is_alive()
            exit_code = process_handle.exitcode
        except Exception as error:
            return retain_unknown("PRODUCER_EXIT_UNCONFIRMED", type(error).__name__)
        if alive is True:
            return self.interface_result(call_id)
        if alive is not False or type(exit_code) is not int:
            return retain_unknown("PRODUCER_EXIT_UNCONFIRMED")
        exit_confirmed_ns = time.monotonic_ns()
        try:
            packet = result_reader(process_handle)
            if (type(packet) is not dict
                    or not {"result", "release_receipt"} <= set(packet)
                    or not set(packet) <= {"result", "release_receipt",
                                          "producer_timing"}
                    or type(packet["result"]) is not dict
                    or type(packet["release_receipt"]) is not dict):
                raise ValueError("producer result packet schema mismatch")
            producer_timing = packet.get("producer_timing")
            if producer_timing is not None and (
                    type(producer_timing) is not dict
                    or set(producer_timing) != {
                        "clock", "child_ready_monotonic_ns"}
                    or producer_timing["clock"] != "time.monotonic_ns"
                    or type(producer_timing["child_ready_monotonic_ns"]) is not int
                    or producer_timing["child_ready_monotonic_ns"] <= 0):
                raise ValueError("producer timing packet schema mismatch")
            with self._lock:
                current = self._calls.get(call_id)
                if (current is None or current["action"]["status"] != "running"
                        or current["cancellation"] is not None):
                    return self.interface_result(call_id)
            readback = readback_reader({
                "call_id": call_id,
                "operation_id": action["operation_id"],
                "target_generation": action["target_generation"],
                "producer_exit_confirmed_ns": exit_confirmed_ns,
            })
            return self.complete_action(call_id, process_handle,
                packet["result"], release_receipt=packet["release_receipt"],
                readback=readback, producer_timing=producer_timing)
        except Exception as error:
            return retain_unknown("COMPLETION_EVIDENCE_UNCONFIRMED",
                                 type(error).__name__)

    def observe_completed_producer(self, operation_id, target_generation, *,
                                   producer_exit_confirmed_ns, deadline_ns):
        observer = getattr(self._supervisor, "observe_completed", None)
        if not callable(observer):
            raise RuntimeError("normal-completion observer is unavailable")
        return observer(operation_id, target_generation,
            producer_exit_confirmed_ns=producer_exit_confirmed_ns,
            deadline_ns=deadline_ns)

    def begin_task_effect_verification(self, call_id):
        """Reserve one independent oracle attempt without changing action/cancel."""
        with self._lock:
            record = self._calls.get(call_id)
            if record is None:
                raise ValueError("unknown caller action")
            if record["task_effect"] is not None:
                return False
            record["task_effect"] = {"status": "pending", "task_success": None,
                                     "receipt": None,
                                     "requested_monotonic_ns": time.monotonic_ns()}
            return True

    def record_task_effect(self, call_id, receipt):
        required = {"call_id", "operation_id", "target_generation", "oracle_id",
                    "outcome", "observed_monotonic_ns", "evidence_ref"}
        if type(receipt) is not dict or set(receipt) != required:
            raise ValueError("independent task-effect receipt has an invalid schema")
        self._validate_id(receipt["oracle_id"], "oracle_id")
        if (receipt["outcome"] not in ("success", "failure", "unknown")
                or type(receipt["observed_monotonic_ns"]) is not int
                or receipt["observed_monotonic_ns"] <= 0
                or type(receipt["evidence_ref"]) is not str
                or not receipt["evidence_ref"]):
            raise ValueError("independent task-effect receipt has invalid fields")
        with self._lock:
            record = self._calls.get(call_id)
            if record is None:
                raise ValueError("unknown caller action")
            existing = record["task_effect"]
            if existing is None:
                raise ValueError("task-effect oracle attempt was not reserved")
            if existing["status"] != "pending":
                if existing.get("receipt") == receipt:
                    return deepcopy(record)
                raise ValueError("task-effect receipt is immutable")
            action = record["action"]
            if (receipt["call_id"] != call_id
                    or receipt["operation_id"] != action["operation_id"]
                    or receipt["target_generation"] != action["target_generation"]):
                raise ValueError("task-effect receipt belongs to a different action generation")
            received_ns = time.monotonic_ns()
            if not (existing["requested_monotonic_ns"]
                    <= receipt["observed_monotonic_ns"] <= received_ns):
                raise ValueError("task-effect observation is outside the oracle request/receipt window")
            outcome = receipt["outcome"]
            record["task_effect"] = {
                "status": "unknown" if outcome == "unknown" else "verified",
                "task_success": (True if outcome == "success" else
                                 False if outcome == "failure" else None),
                "receipt": deepcopy(receipt),
                "requested_monotonic_ns": existing["requested_monotonic_ns"],
                "receipt_received_monotonic_ns": received_ns,
            }
            return deepcopy(record)

    def fail_task_effect_verification(self, call_id, reason):
        if type(reason) is not str or not reason:
            raise ValueError("task-effect failure reason required")
        with self._lock:
            record = self._calls.get(call_id)
            if record is None:
                raise ValueError("unknown caller action")
            existing = record["task_effect"]
            if existing is None:
                raise ValueError("task-effect oracle attempt was not reserved")
            if existing["status"] != "pending":
                return deepcopy(record)
            record["task_effect"] = {"status": "unknown", "task_success": None,
                                     "receipt": None, "uncertainty": reason,
                                     "requested_monotonic_ns": existing["requested_monotonic_ns"]}
            return deepcopy(record)

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
        action = record.get("action") or {}
        if (record.get("standard_program") is not None
                and action.get("status") in ("running", "cancel_pending")
                and status in ("recovered", "unknown")):
            confirmed = (status == "recovered"
                and cancellation.get("action_operation_id") == action.get("operation_id")
                and cancellation.get("target_generation") == action.get("target_generation")
                and result.get("operation_id") == action.get("operation_id")
                and result.get("target_generation") == action.get("target_generation")
                and result.get("phase") == "recovered"
                and result.get("status") == "recovered"
                and result.get("release_confirmed") is True)
            action_status = "recovered" if confirmed else "unknown"
            action.update(status=action_status, release_confirmed=confirmed,
                task_success=None, replay_allowed=False,
                result={"status": action_status, "input_dispatched": None,
                    "release_confirmed": confirmed,
                    "effect_status": "unknown", "task_success": None,
                    "replay_allowed": False})

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

