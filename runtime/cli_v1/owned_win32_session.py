"""Caller journal and standard-program custody adapter for Win32 sessions.

The synthetic guarded-win32 route uses inert injected components. The
supervised-win32 route composes a native gated producer with separate recovery
and observation helpers. Both keep action outcomes separate from cancellation
transactions; producer exit alone never proves release.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import re
import threading
import time
import uuid


_IDENTIFIER = re.compile(r"^[0-9a-f]{32}$")
_PENDING_PHASES = {"cancel_pending", "producer_retired", "recovery_pending"}
_CANCEL_TRANSACTION_NS = 3_000_000_000
_ORPHAN_RECOVERY_WINDOW_NS = 5_000_000_000
_MAX_LATE_INPUT_HORIZON_NS = 60_000_000_000
_TARGET_BINDING_TTL_NS = 60_000_000_000
_MAX_TARGET_BINDINGS = 64


def _input_dispatched_from_result(result):
    """Project dispatch evidence using the same precedence as the MCP result."""
    if type(result) is not dict:
        return None
    execution = result.get("execution")
    program_emissions = (execution.get("program_emissions")
        if type(execution) is dict else None)
    if type(program_emissions) is not int:
        program_emissions = result.get("program_emissions")
    if type(program_emissions) is int:
        return program_emissions > 0
    if type(result.get("input_dispatched")) is bool:
        return result["input_dispatched"]
    emissions = execution.get("emissions") if type(execution) is dict else None
    return emissions > 0 if type(emissions) is int else None


class OwnedWin32SessionOwner:
    """Separate action/cancellation receipts around injected custody components.

    The class is deliberately not a subclass of the X11 owner. Its opt-in MCP
    seam binds a one-use target-generation receipt before caller/model delay,
    then re-reads generation at admission. It does not construct a Win32 backend
    or connect a native input adapter.
    """

    def __init__(self, operation_owner, cancellation_supervisor, *, session_id=None,
                 synthetic_only=True, custody_fence=None):
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
        if custody_fence is not None and (synthetic_only or any(
                not callable(getattr(custody_fence, name, None))
                for name in ("admit", "update", "require_recovery_source",
                             "resolve", "abort_unstarted",
                             "confirm_producer_absent", "close"))):
            raise ValueError("persistent custody fence requires supervised-win32 mode")
        self._custody_fence = custody_fence
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
        self._orphan_recovery_sources = set()
        self._orphan_recovery_fenced_generations = set()
        self._orphan_recovery_unresolved = False

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
        try:
            self._supervisor.close()
        finally:
            if self._custody_fence is not None:
                self._custody_fence.close()
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
            if self._orphan_recovery_unresolved:
                raise ValueError("ORPHAN_RECOVERY_UNRESOLVED")
            if (type(target_generation) is str
                    and target_generation in self._orphan_recovery_fenced_generations):
                raise ValueError("FRESH_TARGET_GENERATION_REQUIRED")
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
            if self._custody_fence is not None:
                try:
                    self._custody_fence.admit(action_operation_id,
                        target_generation, list(obligations))
                except Exception:
                    # No producer has been constructed or started. Keep this
                    # local owner unusable if the cross-process fence refuses.
                    self._owner.mark_unknown(action_operation_id,
                        target_generation, "persistent_custody_fence_admission_failed")
                    raise
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
        owner_result = self._owner.result(operation_id)
        phase = owner_result["phase"]
        if (self._custody_fence is not None
                and type(owner_result.get("producer_identity")) is dict):
            fence_phase = (phase if phase in ("running", "cancel_pending", "unknown")
                           else "unknown")
            self._custody_fence.update(operation_id, generation,
                phase=fence_phase,
                producer_identity=owner_result["producer_identity"],
                gate_state="identity_verified")
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

    def capture_program_emission_progress(self, call_id, reader):
        """Retain an OS-accepted input action lower bound, not task effect."""
        if not callable(reader):
            raise ValueError("program action progress reader required")
        with self._lock:
            record = self._calls.get(call_id)
            if record is None:
                raise ValueError("unknown caller action")
            action = record["action"]
            if ("program_actions_lower_bound" in action
                    or action.get("program_actions_capture_status")
                    in ("capturing", "observed", "unavailable")):
                return deepcopy(record)
            action["program_actions_capture_status"] = "capturing"
            process_handle = self._producer_handles.get(call_id)
            operation_id = record["action"]["operation_id"]
            generation = record["action"]["target_generation"]
        if process_handle is None:
            raise ValueError("caller action has no retained producer")
        count = reader(process_handle)
        if type(count) is not int or count < 0:
            raise ValueError("program action lower bound must be a nonnegative integer")
        observed_ns = time.monotonic_ns()
        with self._lock:
            record = self._calls.get(call_id)
            if (record is None
                    or record["action"]["operation_id"] != operation_id
                    or record["action"]["target_generation"] != generation
                    or self._producer_handles.get(call_id) is not process_handle):
                raise ValueError("caller action changed during progress capture")
            action = record["action"]
            previous = action.get("program_actions_lower_bound", 0)
            if count < previous:
                raise ValueError("program action lower bound cannot decrease")
            action["program_actions_lower_bound"] = count
            action["program_actions_observed_monotonic_ns"] = observed_ns
            action["program_actions_capture_status"] = "observed"
            action.pop("program_actions_capture_error_type", None)
            action.pop("program_actions_capture_error_code", None)
            if count > 0:
                action["input_dispatched"] = True
            result = action.get("result")
            if type(result) is dict:
                result["program_actions_lower_bound"] = count
                result["program_actions_observed_monotonic_ns"] = observed_ns
                if count > 0:
                    result["input_dispatched"] = True
        if self._custody_fence is not None and count > 0:
            self._custody_fence.update(operation_id, generation,
                input_dispatched=True)
        with self._lock:
            record = self._calls.get(call_id)
            if record is None:
                raise ValueError("caller action disappeared during progress capture")
            return deepcopy(record)

    def record_program_emission_progress_failure(self, call_id, error):
        """Expose a bounded reason when the post-recovery counter is unavailable."""
        if not isinstance(error, Exception):
            raise TypeError("progress capture error must be an exception")
        message_codes = {
            "progress_reader_unavailable": "progress_reader_unavailable",
            "caller action has no retained producer": "producer_handle_missing",
            "unknown native producer process": "producer_registry_miss",
            "native producer action counter is invalid": "counter_invalid",
            "program action lower bound must be a nonnegative integer": "counter_value_invalid",
            "program action lower bound cannot decrease": "counter_regressed",
            "caller action changed during progress capture": "action_binding_changed",
            "caller action disappeared during progress capture": "action_record_missing",
            "CUSTODY_FENCE_NO_UNRESOLVED_ACTION": "persistent_fence_not_pending",
        }
        message = str(error)
        code = message_codes.get(message, "capture_failed")
        with self._lock:
            record = self._calls.get(call_id)
            if record is None:
                raise ValueError("unknown caller action")
            action = record["action"]
            action["program_actions_capture_status"] = "unavailable"
            action["program_actions_capture_error_type"] = type(error).__name__
            action["program_actions_capture_error_code"] = code
            return deepcopy(record)

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
            if self._custody_fence is not None:
                self._custody_fence.update(action["operation_id"],
                    action["target_generation"], phase="starting")
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
                phase = self._owner.result(action["operation_id"]).get("phase")
                authorized = False
                if phase == "running":
                    if self._custody_fence is not None:
                        self._custody_fence.update(action["operation_id"],
                            action["target_generation"],
                            gate_state="authorization_attempted")
                    authorized = self._owner.authorize_producer_start(
                        action["operation_id"], action["target_generation"],
                        process, authorize_start)
                if authorized:
                    if self._custody_fence is not None:
                        self._custody_fence.update(action["operation_id"],
                            action["target_generation"], gate_state="authorized")
                    self._stamp_producer_timing(
                        call_id, "start_gate_authorized_monotonic_ns")
                phase = self._owner.result(action["operation_id"]).get("phase")
                if not authorized and phase != "cancel_pending":
                    self._retire_gated_process(process)
                    self._record_uncertain_start(call_id, action,
                        "producer_start_gate_unconfirmed")
            elif phase != "cancel_pending":
                retired = self._retire_gated_process(process)
                self._record_not_dispatched_after_expired_start(
                    call_id, action, process_identity, retired)
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
        if self._custody_fence is not None:
            try:
                # This method is reached only before the parent's gated start
                # callback is authorized; the producer has emitted no input.
                process = self._producer_handles.get(call_id)
                absent = True
                if process is not None and getattr(process, "pid", None) is not None:
                    producer_identity = self._owner.result(
                        action["operation_id"]).get("producer_identity")
                    if type(producer_identity) is not dict:
                        absent = False
                    else:
                        absent = self._custody_fence.confirm_producer_absent(
                            producer_identity) is True
                if absent:
                    self._custody_fence.abort_unstarted(action["operation_id"],
                        action["target_generation"],
                        start_gate_verified_closed=True, input_dispatched=False,
                        producer_absent_verified=True)
            except Exception:
                pass
        with self._lock:
            self._calls[call_id]["action"].update(status="unknown",
                release_confirmed=False, task_success=None, replay_allowed=False,
                result={"status": "unknown", "error": reason,
                    "input_dispatched": False, "release_confirmed": False,
                    "task_success": None, "replay_allowed": False})
        return self.interface_result(call_id)

    def _stamp_producer_timing(self, call_id, field):
        with self._lock:
            record = self._calls.get(call_id)
            if record is not None:
                timing = record["action"].setdefault("producer_timing", {})
                timing.setdefault("clock", "time.monotonic_ns")
                timing[field] = time.monotonic_ns()

    def _record_not_dispatched_after_expired_start(
            self, call_id, action, process_identity, producer_retired):
        """Expose a no-input result only for an expired, never-opened gate."""
        if producer_retired is not True:
            return
        try:
            custody = self._owner.result(action["operation_id"])
        except Exception:
            return
        if (custody.get("phase") != "unknown"
                or custody.get("uncertainty") != "producer_start_after_deadline"
                or custody.get("producer_gate_state") != "closed"
                or custody.get("producer_identity") != process_identity):
            return
        if self._custody_fence is not None:
            try:
                absent = self._custody_fence.confirm_producer_absent(
                    process_identity)
                if absent is not True:
                    return
                self._custody_fence.abort_unstarted(
                    action["operation_id"], action["target_generation"],
                    start_gate_verified_closed=True, input_dispatched=False,
                    producer_absent_verified=True)
            except Exception:
                return
        result = {
            "status": "not_dispatched",
            "reason": "authority_expired_before_start_gate",
            "input_dispatched": False,
            "release_confirmed": False,
            "task_success": None,
            "replay_allowed": False,
        }
        with self._lock:
            record = self._calls.get(call_id)
            if (record is None
                    or record["action"].get("operation_id")
                        != action.get("operation_id")):
                return
            record["action"].update(status="not_dispatched", result=result,
                input_dispatched=False, release_confirmed=False,
                task_success=None, replay_allowed=False)

    def _record_uncertain_start(self, call_id, action, reason):
        """Keep failed gated startup conservative when no no-input proof exists."""
        try:
            custody = self._owner.result(action["operation_id"])
            if custody.get("phase") == "running":
                custody = self._owner.mark_unknown(action["operation_id"],
                    action["target_generation"], reason)
            if self._custody_fence is not None:
                self._custody_fence.update(action["operation_id"],
                    action["target_generation"], phase="unknown")
        except Exception:
            custody = {}
        result = {"status": "unknown", "error": reason,
            "input_dispatched": None, "release_confirmed": False,
            "task_success": None, "replay_allowed": False}
        with self._lock:
            record = self._calls.get(call_id)
            if (record is None
                    or record["action"].get("operation_id")
                        != action.get("operation_id")):
                return
            record["action"].update(status="unknown", result=result,
                input_dispatched=None, release_confirmed=False,
                task_success=None, replay_allowed=False)

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
            if process.is_alive() is not False or type(process.exitcode) is not int:
                return False
            process.close()
            return True
        except Exception:
            # The start gate stays closed, so failure remains contained and
            # the operation's existing UNKNOWN receipt is preserved.
            return False

    def cancel_guarded(self, call_id, *, cancellation_operation_id=None,
                       cleanup_deadline_ns=None,
                       _automatic_completion_recovery=False,
                       _completion_error_type=None):
        if type(_automatic_completion_recovery) is not bool:
            raise ValueError("automatic completion recovery marker must be boolean")
        if (_completion_error_type is not None
                and (type(_completion_error_type) is not str
                     or not _completion_error_type)):
            raise ValueError("completion error type must be a nonempty string")
        if cleanup_deadline_ns is None:
            cleanup_deadline_ns = time.monotonic_ns() + _CANCEL_TRANSACTION_NS
        if type(cleanup_deadline_ns) is not int:
            raise ValueError("cleanup_deadline_ns must be an integer")
        late_input_horizon_ns = getattr(
            self._supervisor, "late_input_horizon_ns", 0)
        now_ns = time.monotonic_ns()
        if (type(late_input_horizon_ns) is int and late_input_horizon_ns > 0
                and cleanup_deadline_ns > now_ns):
            cleanup_deadline_ns = max(cleanup_deadline_ns,
                now_ns + _CANCEL_TRANSACTION_NS + late_input_horizon_ns)
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
            if _automatic_completion_recovery:
                cancellation["automatic_completion_recovery"] = True
                cancellation["completion_error_type"] = _completion_error_type
            record["cancellation"] = cancellation
            try:
                # Admission already persisted unresolved custody before the
                # producer could start. Schedule bounded recovery before a
                # phase-only disk write can delay producer retirement or UP.
                result = self._supervisor.cancel(
                    action["operation_id"], action["target_generation"],
                    cleanup_deadline_ns=cleanup_deadline_ns)
                cancellation["result"] = deepcopy(result)
                if self._custody_fence is not None:
                    try:
                        self._custody_fence.update(action["operation_id"],
                            action["target_generation"], phase="cancel_pending")
                    except Exception:
                        # The prior durable row remains unresolved. Only the
                        # verified recovery path in _refresh may resolve it.
                        pass
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
            for field in ("release_confirmed", "task_success", "replay_allowed"):
                if field in result:
                    action[field] = deepcopy(result[field])
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
        if self._custody_fence is not None:
            if (custody.get("phase") == "completed"
                    and custody.get("release_confirmed") is True):
                horizon_ns = custody.get("late_input_horizon_ns")
                release_ns = custody.get(
                    "late_input_release_received_monotonic_ns")
                observation_start_ns = custody.get(
                    "late_input_observation_start_ns")
                if observation_start_ns is None:
                    observation_start_ns = custody.get(
                        "late_input_observation_start_monotonic_ns")
                end_ns = custody.get("late_input_observation_end_monotonic_ns")
                if end_ns is None:
                    end_ns = custody.get("late_input_observation_end_ns")
                first_observation_ns = custody.get(
                    "late_input_first_observation_monotonic_ns")
                if first_observation_ns is None:
                    first_observation_ns = observation_start_ns
                horizon_start_ns = (release_ns if type(release_ns) is int
                    else observation_start_ns)
                count = custody.get("late_input_observation_count")
                max_gap_ns = custody.get("late_input_max_observed_gap_ns")
                allowed_gap_ns = custody.get("late_input_max_sample_gap_ns")
                horizon_verified = (type(horizon_ns) is int
                    and 0 < horizon_ns <= _MAX_LATE_INPUT_HORIZON_NS
                    and type(observation_start_ns) is int
                    and type(first_observation_ns) is int
                    and first_observation_ns >= observation_start_ns
                    and type(allowed_gap_ns) is int and allowed_gap_ns > 0
                    and first_observation_ns - observation_start_ns <= allowed_gap_ns
                    and type(end_ns) is int
                    and end_ns - horizon_start_ns >= horizon_ns
                    and type(count) is int and count >= 2
                    and type(max_gap_ns) is int and max_gap_ns >= 0
                    and type(allowed_gap_ns) is int and allowed_gap_ns > 0
                    and max_gap_ns <= allowed_gap_ns)
                if horizon_verified:
                    self._custody_fence.resolve(operation_id, generation,
                        release_confirmed=True,
                        late_input_horizon_required=True,
                        late_input_horizon_verified=True)
                else:
                    self._custody_fence.update(operation_id, generation,
                        phase="unknown")
                    custody = dict(custody)
                    custody.update(phase="unknown", status="unknown",
                        release_confirmed=True,
                        late_input_horizon_validation_error=(
                            "normal_completion_horizon_unverified"))
            else:
                self._custody_fence.update(operation_id, generation,
                    phase="unknown")
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
            if record is None:
                raise ValueError("unknown caller action")
            action = deepcopy(record["action"])
            if action["status"] != "running" or record["cancellation"] is not None:
                return self.interface_result(call_id)
            process_handle = self._producer_handles.get(call_id)
            if process_handle is None:
                raise ValueError("running caller action has no retained producer")

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

        def recover_unconfirmed_completion(error_type):
            """Schedule bounded release while the action is still UNKNOWN-capable.

            A dead native producer with no trustworthy completion packet may
            have left OS input down. Start the existing cancellation recovery
            before marking the operation UNKNOWN so the supervisor can retire
            the exact producer and release its frozen obligations. The action
            and release receipt remain separate in the public result.
            """
            with self._lock:
                current = self._calls.get(call_id)
                if (current is None or current.get("standard_program") is None
                        or current.get("cancellation") is not None
                        or current["action"].get("status") != "running"):
                    return False
                operation_id = current["action"]["operation_id"]
                generation = current["action"]["target_generation"]
            try:
                custody = self._owner.result(operation_id)
                phase = custody.get("phase")
            except Exception:
                return False
            completion_observer_failed = (
                phase == "unknown"
                and type(custody.get("uncertainty")) is str
                and custody["uncertainty"].startswith((
                    "normal_completion_observer_",
                    "normal_completion_horizon_"))
            )
            if phase != "running" and not completion_observer_failed:
                return False
            try:
                self.cancel_guarded(call_id,
                    cleanup_deadline_ns=(time.monotonic_ns()
                        + _CANCEL_TRANSACTION_NS),
                    _automatic_completion_recovery=True,
                    _completion_error_type=error_type)
            except Exception:
                return False
            return True
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
            release_receipt = packet["release_receipt"]
            release_verified = (release_receipt.get("verified") is True
                and release_receipt.get("keys_down") == []
                and release_receipt.get("buttons_down") == []
                and release_receipt.get("keys_unknown") == []
                and release_receipt.get("buttons_unknown") == [])
            if (not release_verified
                    and recover_unconfirmed_completion(
                        "UnverifiedProducerReleaseReceipt")):
                return self.interface_result(call_id)
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
            readback_verified = (type(readback) is dict
                and readback.get("operation_id") == action["operation_id"]
                and readback.get("target_generation")
                    == action["target_generation"]
                and readback.get("producer_exit_confirmed_ns")
                    == exit_confirmed_ns
                and readback.get("neutral") is True)
            if (not readback_verified
                    and recover_unconfirmed_completion(
                        "UnverifiedProducerNeutralReadback")):
                return self.interface_result(call_id)
            return self.complete_action(call_id, process_handle,
                packet["result"], release_receipt=packet["release_receipt"],
                readback=readback, producer_timing=producer_timing)
        except Exception as error:
            recover_unconfirmed_completion(type(error).__name__)
            return retain_unknown("COMPLETION_EVIDENCE_UNCONFIRMED",
                                 type(error).__name__)

    def observe_completed_producer(self, operation_id, target_generation, *,
                                   producer_exit_confirmed_ns, deadline_ns):
        observer = getattr(self._supervisor, "observe_completed", None)
        if not callable(observer):
            raise RuntimeError("normal-completion observer is unavailable")
        horizon_ns = getattr(self._supervisor, "late_input_horizon_ns", 0)
        deadline_ns = max(deadline_ns,
            time.monotonic_ns() + _CANCEL_TRANSACTION_NS + horizon_ns)
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
            view = deepcopy(record)
            action = view.get("action")
            if type(action) is dict:
                input_dispatched = _input_dispatched_from_result(
                    action.get("result"))
                if input_dispatched is not None:
                    # This belongs to the retained action. The MCP envelope's
                    # input_dispatched field describes the results query itself.
                    action["input_dispatched"] = input_dispatched
            return view

    def recover_orphaned_input(self, *, source_operation_id,
                               source_target_generation, obligations,
                               source_custody_record,
                               recovery_target_generation=None):
        """Release one externally documented orphan without rewriting its action.

        This entry point is only for a fresh supervised-Win32 session. The
        supplied source action remains UNKNOWN; recovery is a separate bounded
        transaction. Its separately observed recovery generation must match
        the configured target used for release, while the source generation
        remains bound to the durable unknown action.
        """
        try:
            self._validate_id(source_operation_id, "source_operation_id")
        except ValueError as error:
            return self._orphan_recovery_refusal("source_operation_id_invalid",
                                                  str(error))
        if (type(source_target_generation) is not str
                or re.fullmatch(r"[0-9a-f]{64}", source_target_generation) is None):
            return self._orphan_recovery_refusal("target_generation_invalid")
        if recovery_target_generation is None:
            recovery_target_generation = source_target_generation
        if (type(recovery_target_generation) is not str
                or re.fullmatch(r"[0-9a-f]{64}", recovery_target_generation) is None):
            return self._orphan_recovery_refusal(
                "recovery_target_generation_invalid")
        if (not isinstance(obligations, (list, tuple)) or not obligations
                or any(type(item) is not str or not item for item in obligations)
                or len(set(obligations)) != len(obligations)):
            return self._orphan_recovery_refusal("obligations_invalid")
        if type(source_custody_record) is not dict:
            return self._orphan_recovery_refusal("custody_record_invalid")
        try:
            custody_bytes = json.dumps(source_custody_record, sort_keys=True,
                separators=(",", ":"), ensure_ascii=False,
                allow_nan=False).encode("utf-8")
        except (TypeError, ValueError):
            return self._orphan_recovery_refusal("custody_record_not_json")
        if len(custody_bytes) > 65536:
            return self._orphan_recovery_refusal("custody_record_too_large")
        dispatch = source_custody_record.get("dispatch")
        if (source_custody_record.get("classification")
                != "UNKNOWN_RELEASE_UNCONFIRMED_STOPPED"
                or source_custody_record.get("operation_id") != source_operation_id
                or source_custody_record.get("target_generation")
                    != source_target_generation
                or source_custody_record.get("obligations") != list(obligations)
                or source_custody_record.get("do_not_replay") is not True
                or source_custody_record.get("observed_producer_live") is not False
                or type(source_custody_record.get(
                    "late_server_request_possible")) is not bool
                or type(dispatch) is not dict
                or (dispatch.get("input_dispatched") is not None
                    and type(dispatch.get("input_dispatched")) is not bool)
                or dispatch.get("release_confirmed") is not False
                or dispatch.get("task_success") is not None
                or dispatch.get("replay_allowed") is not False):
            return self._orphan_recovery_refusal("custody_record_mismatch")
        source_custody_sha256 = hashlib.sha256(custody_bytes).hexdigest()
        if self.synthetic_only:
            return self._orphan_recovery_refusal("native_supervised_win32_required")
        recover = getattr(self._supervisor, "recover_orphaned_input", None)
        if self._custody_fence is None and dispatch.get("input_dispatched") is False:
            return self._orphan_recovery_refusal("known_no_dispatch_requires_persistent_custody")
        if dispatch.get("input_dispatched") is True and not callable(recover):
            return self._orphan_recovery_refusal("orphan_recovery_unavailable")
        if self._custody_fence is not None and not callable(recover):
            # A closed/identity-only gate may still be resolved as no-dispatch.
            pass

        durable_pending = None
        if self._custody_fence is not None:
            try:
                durable = self._custody_fence.require_recovery_source(
                    source_operation_id, source_target_generation,
                    list(obligations))
            except Exception as error:
                return self._orphan_recovery_refusal(
                    "persistent_custody_source_mismatch", type(error).__name__)
            pending = durable.get("pending") if type(durable) is dict else None
            if type(pending) is not dict:
                return self._orphan_recovery_refusal(
                    "persistent_custody_state_invalid")
            if (pending.get("late_input_horizon_required") is not True
                    or source_custody_record[
                        "late_server_request_possible"] is not True):
                return self._orphan_recovery_refusal(
                    "persistent_custody_late_input_horizon_required")
            durable_pending = pending
            durable_dispatched = pending.get("input_dispatched")
            source_dispatched = dispatch.get("input_dispatched")
            gate_state = durable_pending.get("gate_state")
            dispatch_mismatch = (
                durable_dispatched is True and source_dispatched is False
                or durable_dispatched is False and source_dispatched is True)
            if (dispatch_mismatch and gate_state not in (
                    "authorization_attempted", "authorized")):
                return self._orphan_recovery_refusal(
                    "persistent_custody_dispatch_mismatch")
            if (durable_pending.get("gate_state") in ("closed", "identity_verified")
                    and durable_dispatched is not True
                    and source_dispatched is not True):
                if durable_pending.get("gate_state") == "identity_verified":
                    identity = durable_pending.get("producer_identity")
                    try:
                        absent = self._custody_fence.confirm_producer_absent(identity)
                    except Exception as error:
                        return self._orphan_recovery_refusal(
                            "persistent_custody_producer_unverified",
                            type(error).__name__)
                    if absent is not True:
                        return self._orphan_recovery_refusal(
                            "persistent_custody_producer_still_live")
                with self._lock:
                    if self.state != "open" or self._calls:
                        return self._orphan_recovery_refusal(
                            "fresh_empty_session_required")
                    if source_operation_id in self._orphan_recovery_sources:
                        return self._orphan_recovery_refusal(
                            "source_recovery_already_attempted")
                    self._orphan_recovery_sources.add(source_operation_id)
                    try:
                        current_generation = self.current_target_generation()
                    except Exception:
                        return self._orphan_recovery_refusal(
                            "current_target_generation_unavailable")
                    if current_generation != recovery_target_generation:
                        return self._orphan_recovery_refusal(
                            "recovery_target_generation_mismatch")
                    try:
                        self._custody_fence.abort_unstarted(
                            source_operation_id, source_target_generation,
                            start_gate_verified_closed=True,
                            input_dispatched=False,
                            producer_absent_verified=(
                                durable_pending.get("gate_state") == "closed"
                                or absent is True))
                    except Exception as error:
                        return self._orphan_recovery_refusal(
                            "persistent_custody_unstarted_clear_failed",
                            type(error).__name__)
                    self._orphan_recovery_fenced_generations.add(
                        source_target_generation)
                return {
                    "status": "not_dispatched",
                    "recovery_status": "not_dispatched",
                    "source_operation_id": source_operation_id,
                    "source_target_generation": source_target_generation,
                    "source_custody_canonical_sha256": source_custody_sha256,
                    "source_action_status": "unknown",
                    "release_confirmed": False,
                    "recovery_id": None,
                    "recovery_receipt": None,
                    "task_success": None,
                    "replay_allowed": False,
                    "next_action_requires_fresh_generation": True,
                }
            if durable_pending.get("gate_state") not in (
                    "authorization_attempted", "authorized"):
                return self._orphan_recovery_refusal(
                    "persistent_custody_dispatch_gate_mismatch")
            # Once authorization was attempted, absence of an emission witness
            # cannot prove that the producer sent nothing. Retire the exact
            # durable producer and run obligation-bound release/readback even
            # when both source and journal dispatch counters are False/unknown.
            identity = durable_pending.get("producer_identity")
            try:
                absent = self._custody_fence.confirm_producer_absent(identity)
            except Exception as error:
                return self._orphan_recovery_refusal(
                    "persistent_custody_producer_unverified",
                    type(error).__name__)
            if absent is not True:
                return self._orphan_recovery_refusal(
                    "persistent_custody_producer_still_live")

        with self._lock:
            if self.state != "open" or self._calls:
                return self._orphan_recovery_refusal(
                    "fresh_empty_session_required")
            if self._orphan_recovery_unresolved:
                return self._orphan_recovery_refusal(
                    "orphan_recovery_unresolved")
            if source_operation_id in self._orphan_recovery_sources:
                return self._orphan_recovery_refusal(
                    "source_recovery_already_attempted")
            self._orphan_recovery_sources.add(source_operation_id)
            try:
                current_generation = self.current_target_generation()
            except Exception:
                return self._orphan_recovery_refusal(
                    "current_target_generation_unavailable")
            if current_generation != recovery_target_generation:
                return self._orphan_recovery_refusal(
                    "recovery_target_generation_mismatch")
            recovery_id = uuid.uuid4().hex
            deadline_ns = time.monotonic_ns() + _ORPHAN_RECOVERY_WINDOW_NS
            # Once a valid orphan recovery reaches the native supervisor, no
            # action may be admitted until its terminal custody is known.
            self._orphan_recovery_unresolved = True
            try:
                if callable(recover):
                    recovery_args = (source_operation_id,
                        source_target_generation, recovery_id, deadline_ns,
                        list(obligations))
                    if recovery_target_generation == source_target_generation:
                        receipt = recover(*recovery_args)
                    else:
                        receipt = recover(*recovery_args,
                            recovery_target_generation=recovery_target_generation)
                else:
                    receipt = {"status": "unavailable"}
            except Exception as error:
                receipt = {"status": "unknown",
                           "reason": type(error).__name__}
            confirmed = (type(receipt) is dict
                and receipt.get("status") == "recovered"
                and receipt.get("operation_id") == source_operation_id
                and receipt.get("source_target_generation",
                    receipt.get("target_generation")) == source_target_generation
                and receipt.get("recovery_target_generation",
                    receipt.get("target_generation")) == recovery_target_generation
                and receipt.get("recovery_id") == recovery_id
                and receipt.get("release_confirmed") is True)
            if (confirmed and source_custody_record[
                    "late_server_request_possible"] is True):
                horizon_ns = receipt.get("late_input_horizon_ns")
                release_ns = receipt.get(
                    "late_input_release_received_monotonic_ns")
                start_ns = receipt.get(
                    "late_input_observation_start_monotonic_ns")
                end_ns = receipt.get("late_input_observation_end_monotonic_ns")
                count = receipt.get("late_input_observation_count")
                max_gap_ns = receipt.get("late_input_max_observed_gap_ns")
                allowed_gap_ns = receipt.get("late_input_max_sample_gap_ns")
                confirmed = (receipt.get("late_input_horizon_verified") is True
                    and type(horizon_ns) is int
                    and 0 < horizon_ns <= _MAX_LATE_INPUT_HORIZON_NS
                    and type(release_ns) is int and release_ns >= 0
                    and type(start_ns) is int and start_ns >= release_ns
                    and type(allowed_gap_ns) is int and allowed_gap_ns > 0
                    and start_ns - release_ns <= allowed_gap_ns
                    and type(end_ns) is int and end_ns - release_ns >= horizon_ns
                    and type(count) is int and count >= 2
                    and type(max_gap_ns) is int and max_gap_ns >= 0
                    and max_gap_ns <= allowed_gap_ns)
            if confirmed and self._custody_fence is not None:
                try:
                    self._custody_fence.resolve(source_operation_id,
                        source_target_generation, release_confirmed=True,
                        late_input_horizon_required=source_custody_record[
                            "late_server_request_possible"],
                        late_input_horizon_verified=(
                            source_custody_record[
                                "late_server_request_possible"] is False
                            or receipt.get("late_input_horizon_verified") is True),
                        fence_generations=list(dict.fromkeys((
                            source_target_generation,
                            recovery_target_generation))))
                except Exception:
                    confirmed = False
            if confirmed:
                self._orphan_recovery_fenced_generations.add(
                    source_target_generation)
                self._orphan_recovery_fenced_generations.add(
                    recovery_target_generation)
                self._orphan_recovery_unresolved = False
            return {
                "status": "recovered" if confirmed else "unknown",
                "recovery_status": "recovered" if confirmed else "unknown",
                "source_operation_id": source_operation_id,
                "source_target_generation": source_target_generation,
                "recovery_target_generation": recovery_target_generation,
                "source_custody_canonical_sha256": source_custody_sha256,
                "source_action_status": "unknown",
                "release_confirmed": bool(confirmed),
                "recovery_id": recovery_id,
                "recovery_receipt": deepcopy(receipt),
                "task_success": None,
                "replay_allowed": False,
                "next_action_requires_fresh_generation": True,
            }

    @staticmethod
    def _orphan_recovery_refusal(reason, detail=None):
        result = {"status": "refused", "recovery_status": "refused",
                  "reason": reason,
                  "source_action_status": "unknown",
                  "release_confirmed": False, "task_success": None,
                  "replay_allowed": False}
        if detail is not None:
            result["detail"] = detail
        return result

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
        # Keep the recovery send diagnostics on the retained action as well as
        # on the cancellation owner snapshot. These rows describe API attempts;
        # they do not upgrade release confirmation or task effect.
        attempts = result.get("recovery_release_key_up_attempts")
        if type(attempts) is list:
            action_result = action.get("result")
            if type(action_result) is dict:
                action_result["recovery_release_key_up_attempts"] = deepcopy(attempts)
            action["recovery_release_key_up_attempts"] = deepcopy(attempts)
        automatic_completion_recovery = (
            cancellation.get("automatic_completion_recovery") is True)
        if automatic_completion_recovery:
            action_result = action.get("result")
            if type(action_result) is not dict:
                action_result = {}
            input_dispatched = action.get("input_dispatched")
            if type(input_dispatched) is not bool:
                input_dispatched = (action_result.get("input_dispatched")
                    if type(action_result.get("input_dispatched")) is bool
                    else None)
            action.update(status="unknown", input_dispatched=input_dispatched,
                release_confirmed=False, task_success=None,
                replay_allowed=False)
            action_result.update(status="unknown",
                input_dispatched=input_dispatched, release_confirmed=False,
                error="COMPLETION_EVIDENCE_UNCONFIRMED",
                effect_status="unknown", task_success=None,
                replay_allowed=False)
            error_type = cancellation.get("completion_error_type")
            if type(error_type) is str and error_type:
                action_result["error_type"] = error_type
            action["result"] = action_result
        confirmed = (status == "recovered"
            and cancellation.get("action_operation_id") == action.get("operation_id")
            and cancellation.get("target_generation") == action.get("target_generation")
            and result.get("operation_id") == action.get("operation_id")
            and result.get("target_generation") == action.get("target_generation")
            and result.get("phase") == "recovered"
            and result.get("status") == "recovered"
            and result.get("release_confirmed") is True)
        task_effect = record.get("task_effect")
        task_effect_verified = (type(task_effect) is dict
            and task_effect.get("status") == "verified")
        if (confirmed and record.get("standard_program") is None
                and not task_effect_verified):
            action["status"] = "recovered"
            action["release_confirmed"] = True
            action["task_success"] = None
            action["replay_allowed"] = False
            action_result = action.get("result")
            if type(action_result) is not dict:
                action_result = {"status": "recovered",
                    "release_confirmed": True, "task_success": None,
                    "replay_allowed": False}
                action["result"] = action_result
            if type(attempts) is list:
                action_result["recovery_release_key_up_attempts"] = deepcopy(attempts)
        if (not automatic_completion_recovery
                and record.get("standard_program") is not None
                and action.get("status") in ("running", "cancel_pending")
                and status in ("recovered", "unknown")):
            action_status = "recovered" if confirmed else "unknown"
            action.update(status=action_status, release_confirmed=confirmed,
                task_success=None, replay_allowed=False,
                obligations=(deepcopy(result.get("obligations", []))
                    if confirmed and type(result.get("obligations")) is list
                    else []),
                result={"status": action_status, "input_dispatched": None,
                    "release_confirmed": confirmed,
                    "obligations": (deepcopy(result.get("obligations", []))
                        if confirmed and type(result.get("obligations")) is list
                        else []),
                    "recovery_release_key_up_attempts": deepcopy(attempts)
                        if type(attempts) is list else None,
                    "effect_status": "unknown", "task_success": None,
                    "replay_allowed": False})
        horizon_verified = None
        if confirmed and "late_input_horizon_ns" in result:
            horizon_ns = result.get("late_input_horizon_ns")
            release_ns = result.get("late_input_release_received_ns")
            start_ns = result.get("late_input_observation_start_ns")
            end_ns = result.get("late_input_observation_end_ns")
            count = result.get("late_input_observation_count")
            max_gap_ns = result.get("late_input_max_observed_gap_ns")
            allowed_gap_ns = result.get("late_input_max_sample_gap_ns")
            horizon_verified = (type(horizon_ns) is int
                and 0 < horizon_ns <= _MAX_LATE_INPUT_HORIZON_NS
                and type(release_ns) is int
                and type(start_ns) is int and start_ns >= release_ns
                and type(allowed_gap_ns) is int and allowed_gap_ns > 0
                and start_ns - release_ns <= allowed_gap_ns
                and type(end_ns) is int and end_ns - release_ns >= horizon_ns
                and type(count) is int and count >= 2
                and type(max_gap_ns) is int and max_gap_ns >= 0
                and max_gap_ns <= allowed_gap_ns
                and result.get("late_input_validation_error") is None)
            # Publish the same bounded-horizon decision that is used to
            # resolve durable custody. Exact-call result readers must not
            # have to infer a private owner decision from release alone.
            result = dict(result)
            result["late_input_horizon_verified"] = horizon_verified
            cancellation["result"] = deepcopy(result)
        if self._custody_fence is not None:
            operation_id = action.get("operation_id")
            generation = action.get("target_generation")
            try:
                if confirmed:
                    progress_captured = (
                        "program_actions_lower_bound" in action
                        or action.get("program_actions_capture_status")
                        in ("observed", "unavailable"))
                    if not progress_captured:
                        # Keep the durable pending row until the caller has
                        # attempted its one-shot producer progress read. A
                        # later exact-results readback can finish this step
                        # after asynchronous recovery has retired the child.
                        return
                    if type(horizon_verified) is not bool:
                        horizon_verified = False
                    self._custody_fence.resolve(operation_id, generation,
                        release_confirmed=True,
                        late_input_horizon_required=True,
                        late_input_horizon_verified=horizon_verified)
                else:
                    phase_to_store = ("unknown" if status == "unknown" else
                        "recovery_pending" if result.get("phase") == "recovery_pending" else
                        "cancel_pending")
                    self._custody_fence.update(operation_id, generation,
                        phase=phase_to_store)
            except Exception:
                # Preserve the durable unresolved record if the local receipt
                # cannot safely advance it.
                try:
                    self._custody_fence.update(operation_id, generation,
                        phase="unknown")
                except Exception:
                    pass

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

