"""Fail-closed non-staggering explicit-release telemetry over InputOwner v10.

Per explicit release this wrapper does no owner/X11 state sample and publishes
nothing. It only snapshots cheap local lease state, brackets the unchanged v10
call with monotonic caller timestamps, and returns a receipt to the backend.
"""
import threading
import time

from input_owner_v12_candidate import InputOwner as Previous


class InputOwner:
    def __init__(self, display_name, _owner_cls=Previous):
        self._inner = _owner_cls(display_name)
        self._admission_records = {}
        self._admission_records_lock = threading.Lock()

    @property
    def owner_id(self):
        return self._inner.owner_id

    @property
    def records(self):
        return list(self._inner.records)

    def close(self):
        try:
            return self._inner.close()
        finally:
            with self._admission_records_lock:
                self._admission_records.clear()

    @staticmethod
    def _intent_token(lease):
        return getattr(lease, "intent_token", None) if lease is not None else None

    @staticmethod
    def _lease_state_at(lease, now_ns):
        if lease is None:
            return {
                "lease_time_valid_at_request": False,
                "cancel_requested_at_request": None,
                "focus_invalid_at_request": None,
                "ordinary_release_candidate": False,
            }
        deadline = getattr(lease, "deadline", None)
        cancel = getattr(lease, "cancel", None)
        cancel_requested = cancel.is_set() if hasattr(cancel, "is_set") else None
        focus_invalid = bool(getattr(lease, "focus_invalid", False))
        time_valid = type(deadline) is int and now_ns < deadline
        return {
            "lease_time_valid_at_request": time_valid,
            "cancel_requested_at_request": cancel_requested,
            "focus_invalid_at_request": focus_invalid,
            "ordinary_release_candidate": (
                time_valid and cancel_requested is False and not focus_invalid
            ),
        }

    def _decorate(self, result, lease):
        if not isinstance(result, dict):
            return result
        decorated = dict(result)
        token = self._intent_token(lease)
        if token is not None:
            decorated.setdefault("intent_token", token)
        return decorated

    def _records_snapshot(self):
        try:
            records = self._inner.records
        except Exception:
            return None
        return list(records) if isinstance(records, (list, tuple)) else None

    def _prune_completed_admissions(self, records):
        """Forget markers once owner history proves their hold was released."""
        if records is None:
            return
        completed = []
        for index, record in enumerate(records):
            if (isinstance(record, dict)
                    and record.get("event") == "owner_release"
                    and record.get("verified") is True
                    and record.get("keys_down") == []
                    and record.get("buttons_down") == []
                    and type(record.get("valid_until_ns")) is int
                    and type(record.get("verified_ns")) is int):
                completed.append((index, record["valid_until_ns"],
                                  record["verified_ns"]))
        if not completed:
            return
        with self._admission_records_lock:
            self._admission_records = {
                admission_key: marker
                for admission_key, marker in self._admission_records.items()
                if not any(
                    isinstance(marker, tuple) and len(marker) == 3
                    and type(marker[0]) is int and type(marker[1]) is int
                    and type(marker[2]) is int
                    and marker[0] <= index and marker[1] == deadline
                    and release_ns >= marker[2]
                    for index, deadline, release_ns in completed
                )
            }

    def _admission_key(self, lease, key):
        try:
            hash(key)
        except TypeError:
            return None
        return id(lease), key

    def call(self, operation, lease=None, key=None):
        if operation not in ("up", "button_up"):
            records_before = (
                self._records_snapshot()
                if operation in ("down", "button_down", "release") else None
            )
            self._prune_completed_admissions(records_before)
            started_ns = time.perf_counter_ns() if operation in ("release", "close") else None
            result = self._inner.call(operation, lease, key)
            returned_ns = time.perf_counter_ns() if started_ns is not None else None
            result = self._decorate(result, lease)
            if operation == "release":
                self._prune_completed_admissions(self._records_snapshot())
            admitted = (
                operation == "down" and isinstance(result, dict)
                and result.get("event") == "input_admission"
            ) or (
                operation == "button_down" and isinstance(result, dict)
                and result.get("event") == "pointer_admission"
            )
            if admitted:
                admission_key = self._admission_key(lease, key)
                if admission_key is not None and records_before is not None:
                    deadline = getattr(lease, "deadline", None) if lease is not None else None
                    admitted_ns = result.get("admitted_ns")
                    if type(deadline) is int and type(admitted_ns) is int:
                        with self._admission_records_lock:
                            self._admission_records[admission_key] = (
                                len(records_before), deadline, admitted_ns)
            if isinstance(result, dict) and result.get("event") == "owner_release":
                result.setdefault("release_call_started_ns", started_ns)
                result.setdefault("release_call_returned_ns", returned_ns)
            return result

        # No input_state/keymap query and no event publication occurs here.
        release_call_started_ns = time.perf_counter_ns()
        lease_state = self._lease_state_at(lease, release_call_started_ns)
        admission_key = self._admission_key(lease, key)
        admission_marker = None
        if admission_key is not None:
            with self._admission_records_lock:
                admission_marker = self._admission_records.pop(admission_key, None)
        owner_records_before = self._records_snapshot()
        result = self._inner.call(operation, lease, key)
        release_call_returned_ns = time.perf_counter_ns()
        if result is not None:
            raise AssertionError("InputOwner v10 explicit release unexpectedly returned payload")
        if release_call_returned_ns < release_call_started_ns:
            raise AssertionError("monotonic release clock moved backwards")

        records_after = self._records_snapshot()
        owner_release_history_complete = (
            admission_marker is not None and records_after is not None
        )
        owner_cleanup_intervened = False
        if owner_release_history_complete:
            record_index, admitted_deadline, admitted_ns = admission_marker
            if (type(record_index) is not int or record_index < 0
                    or record_index > len(records_after)
                    or type(admitted_deadline) is not int
                    or type(admitted_ns) is not int):
                owner_release_history_complete = False
            else:
                for record in records_after[record_index:]:
                    if not isinstance(record, dict):
                        owner_release_history_complete = False
                        break
                    if record.get("event") == "owner_release":
                        cleanup_deadline = record.get("valid_until_ns")
                        cleanup_ns = record.get("verified_ns")
                        if (type(cleanup_deadline) is not int
                                or type(cleanup_ns) is not int):
                            owner_release_history_complete = False
                            break
                        if (cleanup_deadline == admitted_deadline
                                and cleanup_ns >= admitted_ns):
                            owner_cleanup_intervened = True

        ordinary_release_candidate = (
            lease_state["ordinary_release_candidate"]
            and owner_release_history_complete
            and not owner_cleanup_intervened
        )

        receipt = {
            "event": "input_release_transition",
            "transition_schema": "input-release-transition-v3",
            "operation": operation,
            "key" if operation == "up" else "button": key,
            "owner_id": self._inner.owner_id,
            "intent_token": self._intent_token(lease),
            "valid_until_ns": getattr(lease, "deadline", None) if lease is not None else None,
            "release_call_started_ns": release_call_started_ns,
            "release_call_returned_ns": release_call_returned_ns,
            "release_call_bracket_ns": release_call_returned_ns - release_call_started_ns,
            "owner_transition_verified": None,
            "grants_input_authority": False,
            **lease_state,
            "owner_release_history_complete": owner_release_history_complete,
            "owner_cleanup_intervened": owner_cleanup_intervened,
            "ordinary_release_candidate": ordinary_release_candidate,
            "measurement_contract": (
                "caller brackets unchanged InputOwner v10 explicit release; the release "
                "history since admission must contain no same-lease owner cleanup; no "
                "owner/X11 state sample or telemetry publication occurs inside this call"
            ),
        }
        if operation == "up":
            records_after = self._records_snapshot()
            suffix = None
            if (isinstance(owner_records_before, list)
                    and isinstance(records_after, list)
                    and len(records_after) >= len(owner_records_before)):
                suffix = records_after[len(owner_records_before):]
            matches = [row for row in (suffix or [])
                       if isinstance(row, dict)
                       and row.get("event") == "owner_keyup"
                       and row.get("reason") == "explicit_up"
                       and row.get("owner_id") == self._inner.owner_id
                       and row.get("intent_token") == self._intent_token(lease)
                       and row.get("key") == key]
            exact = len(matches) == 1
            receipt["owner_keyup_join"] = (
                "MATCHED_EXPLICIT_KEYUP" if exact else
                "MISSING_OR_AMBIGUOUS_OWNER_RECEIPT"
            )
            receipt["owner_keyup_receipt"] = matches[0] if exact else None
            receipt["admission_id"] = matches[0].get("admission_id") if exact else None
            receipt["owner_keyup_interval_ordered"] = bool(
                exact and type(matches[0].get("owner_keyup_started_ns")) is int
                and type(matches[0].get("owner_sync_returned_ns")) is int
                and matches[0]["owner_keyup_started_ns"]
                    <= matches[0]["owner_sync_returned_ns"]
            ) if exact else False
        return receipt

