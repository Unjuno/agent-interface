"""Pure custody gate for opt-in Win32 operations.

This module deliberately imports no Win32 API and sends no input. The parent
caller records exact child-process identity and may request recovery only after
the matching producer has a confirmed exit and before the cleanup deadline.
"""
from __future__ import annotations

import copy
import re
import threading
import uuid


_GENERATION = re.compile(r"^[0-9a-f]{64}$")


class OwnerRefused(ValueError):
    """The owner cannot safely admit or advance this operation."""

    def __init__(self, message, *, code="OWNER_REFUSED", operation_id=None):
        super().__init__(message)
        self.code = code
        self.operation_id = operation_id


class OperationOwner:
    """Parent-side state gate; the identity reader must query the owned handle.

    It must not reopen the process by PID: the retained handle is the evidence
    that binds the queried creation time to this exact child across PID reuse.
    """

    def __init__(self, *, clock_ns, process_identity_reader):
        if not callable(clock_ns) or not callable(process_identity_reader):
            raise ValueError("monotonic clock and process identity reader required")
        self._clock_ns = clock_ns
        self._process_identity_reader = process_identity_reader
        self._lock = threading.RLock()
        self._records = {}
        self._producer_handles = {}
        self._orphan_handles = []
        self._active_operation_id = None

    def admit(self, operation_id, target_generation, deadline_ns, obligations,
              *, start_gate_required=False):
        self._validate_operation(operation_id, target_generation)
        if type(start_gate_required) is not bool:
            raise OwnerRefused("start gate requirement must be boolean")
        if type(deadline_ns) is not int or deadline_ns <= self._clock_ns():
            raise OwnerRefused("operation deadline must be in the future")
        if (not isinstance(obligations, (list, tuple))
                or any(type(item) is not str or not item for item in obligations)
                or len(set(obligations)) != len(obligations)):
            raise OwnerRefused("unique frozen input obligations required")
        with self._lock:
            if operation_id in self._records:
                raise OwnerRefused("operation ID already used")
            prior = (self._records.get(self._active_operation_id)
                     if self._active_operation_id is not None else None)
            if prior is not None:
                if prior["status"] != "recovered":
                    raise OwnerRefused(
                        "prior producer or cleanup remains unresolved",
                        code="INPUT_PRODUCER_UNRESOLVED",
                        operation_id=prior["operation_id"])
                if target_generation == prior["target_generation"]:
                    raise OwnerRefused("fresh target generation required after cancellation")
            record = {
                "operation_id": operation_id,
                "target_generation": target_generation,
                "deadline_ns": deadline_ns,
                "obligations": tuple(obligations),
                "status": "admitted",
                "producer_identity": None,
                "producer_exit_code": None,
                # Direct producers have no known closed gate. Only a caller
                # that guarantees a parent-owned gate may declare it closed.
                "producer_gate_state": "closed" if start_gate_required else "untracked",
                "cleanup_deadline_ns": None,
                "recovery_id": None,
                "release_confirmed": False,
                "task_success": None,
                "replay_allowed": False,
                "uncertainty": None,
            }
            self._records[operation_id] = record
            self._active_operation_id = operation_id
            return self._public(record)

    def producer_started(self, operation_id, target_generation, process_handle,
                         *, process_identity):
        with self._lock:
            record = self._records.get(operation_id)
            if (record is None
                    or record["target_generation"] != target_generation
                    or record["producer_identity"] is not None
                    or operation_id in self._producer_handles):
                self._orphan_handles.append(process_handle)
                if record is not None:
                    record["status"] = "unknown"
                return False
            self._producer_handles[operation_id] = process_handle
        try:
            identity = self._process_identity(process_identity)
            if (type(getattr(process_handle, "pid", None)) is not int
                    or process_handle.pid != identity["pid"]
                    or not callable(getattr(process_handle, "is_alive", None))
                    or not hasattr(process_handle, "exitcode")):
                raise OwnerRefused("invalid producer process handle")
        except Exception:
            with self._lock:
                record = self._records.get(operation_id)
                if record is not None:
                    record["status"] = "unknown"
            return False
        try:
            current_identity = self._process_identity_reader(process_handle)
            alive = process_handle.is_alive()
        except Exception:
            current_identity = None
            alive = None
        with self._lock:
            record = self._matching(operation_id, target_generation)
            if (record["producer_identity"] is not None
                    or self._producer_handles.get(operation_id) is not process_handle):
                return False
            record["producer_identity"] = identity
            if current_identity != identity or alive is not True:
                record["status"] = "unknown"
                return False
            if self._clock_ns() >= record["deadline_ns"]:
                record["status"] = "unknown"
                return False
            if record["status"] == "admitted":
                record["status"] = "running"
                return True
            # Cancellation won the race with child startup. Retain its exact
            # identity so the owner can await retirement, but never authorize it.
            return False

    def authorize_producer_start(self, operation_id, target_generation,
                                 process_handle, open_start_gate):
        """Atomically open the child gate only while this producer is admitted.

        ``open_start_gate`` must be a nonblocking parent-owned event/set call.
        Running it under the custody lock orders authorization against cancel:
        either the gate opens before cancellation closes admission, or cancel
        wins and the gated child remains unable to emit input.
        """
        if not callable(open_start_gate):
            raise OwnerRefused("parent-owned producer start gate required")
        with self._lock:
            record = self._matching(operation_id, target_generation)
            if (record["status"] != "running"
                    or self._producer_handles.get(operation_id) is not process_handle
                    or self._clock_ns() >= record["deadline_ns"]):
                return False
            try:
                # A gate callback could open the gate and then raise. Never
                # reinterpret an attempted callback as proof it stayed closed.
                record["producer_gate_state"] = "authorization_attempted"
                open_start_gate()
            except Exception:
                record["status"] = "unknown"
                record["uncertainty"] = "producer_start_gate_unconfirmed"
                return False
            return True

    def producer_handle_for_retirement(self, operation_id, target_generation):
        """Return the parent's retained handle for cancellation cleanup only."""
        with self._lock:
            record = self._matching(operation_id, target_generation)
            if record["status"] != "cancel_pending":
                return None
            return self._producer_handles.get(operation_id)

    def request_cancel(self, operation_id, target_generation, *, cleanup_deadline_ns):
        with self._lock:
            record = self._matching(operation_id, target_generation)
            if (record["cleanup_deadline_ns"] is not None
                    and record["status"] in ("cancel_pending", "producer_retired",
                                              "recovery_pending", "recovered",
                                              "unknown")):
                return self._public(record)
            if record["status"] not in ("admitted", "running"):
                raise OwnerRefused("operation has no cancellable producer")
            if (type(cleanup_deadline_ns) is not int
                    or cleanup_deadline_ns <= self._clock_ns()):
                record["status"] = "unknown"
                record["cleanup_deadline_ns"] = cleanup_deadline_ns
                return self._public(record)
            record["status"] = "cancel_pending"
            record["cleanup_deadline_ns"] = cleanup_deadline_ns
            return self._public(record)

    def producer_retired(self, operation_id, target_generation, process_handle):
        with self._lock:
            record = self._matching(operation_id, target_generation)
            if (record["status"] != "cancel_pending"
                    or record["producer_identity"] is None
                    or self._producer_handles.get(operation_id) is not process_handle):
                return False
            expected_identity = dict(record["producer_identity"])
        try:
            alive = process_handle.is_alive()
            exit_code = process_handle.exitcode
            current_identity = self._process_identity_reader(process_handle)
        except Exception:
            alive = None
            exit_code = None
            current_identity = None
        with self._lock:
            record = self._matching(operation_id, target_generation)
            if (record["status"] != "cancel_pending"
                    or self._producer_handles.get(operation_id) is not process_handle):
                return False
            if alive is True:
                return False
            if (alive is not False or type(exit_code) is not int
                    or current_identity != expected_identity
                    or record["producer_identity"] != expected_identity):
                record["status"] = "unknown"
                record["uncertainty"] = "producer_exit_or_identity_unconfirmed"
                return False
            record["producer_exit_code"] = exit_code
            if self._clock_ns() >= record["cleanup_deadline_ns"]:
                record["status"] = "unknown"
                record["uncertainty"] = "cleanup_deadline_expired_before_retirement"
                return False
            record["status"] = "producer_retired"
            return True

    def mark_unknown(self, operation_id, target_generation, reason):
        if type(reason) is not str or not reason:
            raise OwnerRefused("uncertainty reason required")
        with self._lock:
            record = self._matching(operation_id, target_generation)
            if record["status"] != "recovered":
                record["status"] = "unknown"
                record["uncertainty"] = reason
            return self._public(record)

    def expire_cleanup(self, operation_id, target_generation):
        with self._lock:
            record = self._matching(operation_id, target_generation)
            if (record["cleanup_deadline_ns"] is not None
                    and type(record["cleanup_deadline_ns"]) is int
                    and self._clock_ns() >= record["cleanup_deadline_ns"]
                    and record["status"] in ("cancel_pending", "producer_retired",
                                              "recovery_pending")):
                record["status"] = "unknown"
                record["uncertainty"] = "cleanup_deadline_expired"
            return self._public(record)

    def claim_recovery(self, operation_id, target_generation):
        with self._lock:
            record = self._matching(operation_id, target_generation)
            if (record["status"] != "producer_retired"
                    or self._clock_ns() >= record["cleanup_deadline_ns"]):
                if record["status"] == "producer_retired":
                    record["status"] = "unknown"
                return None
            if record["producer_gate_state"] == "closed":
                record["status"] = "unknown"
                record["uncertainty"] = "producer_retired_without_start_authorization"
                return None
            recovery_id = uuid.uuid4().hex
            record["recovery_id"] = recovery_id
            record["status"] = "recovery_pending"
            return {
                "operation_id": operation_id,
                "target_generation": target_generation,
                "recovery_id": recovery_id,
                "deadline_ns": record["cleanup_deadline_ns"],
                "obligations": list(record["obligations"]),
            }

    def recovery_completed(self, operation_id, target_generation, recovery_id,
                           *, release_accepted, readback):
        with self._lock:
            record = self._matching(operation_id, target_generation)
            if (record["status"] != "recovery_pending"
                    or recovery_id != record["recovery_id"]):
                return False
            valid_readback = (
                type(readback) is dict
                and readback.get("operation_id") == operation_id
                and readback.get("target_generation") == target_generation
                and readback.get("recovery_id") == recovery_id
                and readback.get("neutral") is True
            )
            confirmed = (
                release_accepted is True
                and valid_readback
                and self._clock_ns() < record["cleanup_deadline_ns"]
            )
            record["status"] = "recovered" if confirmed else "unknown"
            record["release_confirmed"] = bool(confirmed)
            if not confirmed:
                record["uncertainty"] = "recovery_or_neutral_readback_unconfirmed"
            return bool(confirmed)

    def result(self, operation_id):
        with self._lock:
            record = self._records.get(operation_id)
            if record is None:
                raise OwnerRefused("unknown operation ID")
            if (record["cleanup_deadline_ns"] is not None
                    and type(record["cleanup_deadline_ns"]) is int
                    and self._clock_ns() >= record["cleanup_deadline_ns"]
                    and record["status"] in ("cancel_pending", "producer_retired",
                                              "recovery_pending")):
                record["status"] = "unknown"
                record["uncertainty"] = "cleanup_deadline_expired"
            return self._public(record)

    def _matching(self, operation_id, target_generation):
        record = self._records.get(operation_id)
        if record is None or record["target_generation"] != target_generation:
            raise OwnerRefused("stale operation ID or target generation")
        return record

    @staticmethod
    def _validate_operation(operation_id, target_generation):
        if type(operation_id) is not str or not operation_id:
            raise OwnerRefused("nonempty operation ID required")
        if (type(target_generation) is not str
                or _GENERATION.fullmatch(target_generation) is None):
            raise OwnerRefused("SHA-256 target-generation digest required")

    @staticmethod
    def _process_identity(identity):
        if (type(identity) is not dict or set(identity) !=
                {"pid", "creation_time_100ns"}
                or type(identity["pid"]) is not int or identity["pid"] <= 0
                or type(identity["creation_time_100ns"]) is not int
                or identity["creation_time_100ns"] <= 0):
            raise OwnerRefused("exact producer PID and creation time required")
        return {"pid": identity["pid"],
                "creation_time_100ns": identity["creation_time_100ns"]}

    @staticmethod
    def _public(record):
        value = copy.deepcopy(record)
        value["obligations"] = list(value["obligations"])
        value["phase"] = value["status"]
        if value["status"] in ("cancel_pending", "producer_retired",
                                "recovery_pending"):
            value["status"] = "pending"
        return value
