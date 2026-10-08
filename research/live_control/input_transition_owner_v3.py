"""Fail-closed non-staggering explicit-release telemetry over InputOwner v10.

Per explicit release this wrapper does no owner/X11 state sample and publishes
nothing. It snapshots cheap local lease state, brackets the unchanged v10 call
with monotonic caller timestamps, and returns the exact stored input-admission
receipt with the matching per-key release transition.
"""
import threading
import time

from input_owner_v10 import InputOwner as Previous


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
                    isinstance(marker, tuple) and len(marker) == 5
                    and type(marker[1]) is int and type(marker[2]) is int
                    and type(marker[3]) is int
                    and marker[1] <= index and marker[2] == deadline
                    and release_ns >= marker[3]
                    for index, deadline, release_ns in completed
                )
            }

    def _admission_key(self, lease, key):
        try:
            hash(key)
        except TypeError:
            return None
        return id(lease), key

    def _clear_admissions_for_lease(self, lease):
        with self._admission_records_lock:
            for admission_key, marker in list(self._admission_records.items()):
                if marker[0] is lease:
                    del self._admission_records[admission_key]

    def _admission_receipt_for_release(self, marker, lease, operation, key, release_started_ns):
        receipt = (dict(marker[4]) if isinstance(marker, tuple) and len(marker) == 5
                   and type(marker[4]) is dict else None)
        expected_event = "input_admission" if operation == "down" else "pointer_admission"
        identity_field = "key" if operation == "down" else "payload"
        valid = (
            receipt is not None
            and receipt.get("event") == expected_event
            and receipt.get("operation") == operation
            and receipt.get(identity_field) == key
            and receipt.get("owner_id") == self._inner.owner_id
            and receipt.get("intent_token") == self._intent_token(lease)
            and receipt.get("valid_until_ns") == getattr(lease, "deadline", None)
            and type(receipt.get("admitted_ns")) is int
            and type(receipt.get("input_ack_ns")) is int
            and receipt["admitted_ns"] <= receipt["input_ack_ns"] < release_started_ns
        )
        return receipt, valid

    def _call_up_batch(self, lease, keys):
        if type(keys) is not list or not keys or len(set(keys)) != len(keys):
            raise ValueError("unique key list required for up_batch")
        started_ns = time.perf_counter_ns()
        lease_state = self._lease_state_at(lease, started_ns)
        markers = {}
        with self._admission_records_lock:
            for key in keys:
                markers[key] = self._admission_records.pop(
                    self._admission_key(lease, key), None)
        receipts = self._inner.call("up_batch", lease, keys)
        returned_ns = time.perf_counter_ns()
        records_after = self._records_snapshot()
        if type(receipts) is not list or len(receipts) != len(keys):
            raise RuntimeError("owner returned malformed up_batch receipts")
        transitions = []
        for key, receipt in zip(keys, receipts):
            marker = markers[key]
            history_complete = marker is not None and records_after is not None
            cleanup_intervened = False
            if history_complete:
                admitted_lease, record_index, admitted_deadline, admitted_ns, _ = marker
                if (admitted_lease is not lease
                        or type(record_index) is not int or record_index < 0
                        or record_index > len(records_after)
                        or type(admitted_deadline) is not int
                        or type(admitted_ns) is not int):
                    history_complete = False
                else:
                    for record in records_after[record_index:]:
                        if not isinstance(record, dict):
                            history_complete = False
                            break
                        if record.get("event") == "owner_release":
                            cleanup_deadline = record.get("valid_until_ns")
                            cleanup_ns = record.get("verified_ns")
                            if type(cleanup_deadline) is not int or type(cleanup_ns) is not int:
                                history_complete = False
                                break
                            if cleanup_deadline == admitted_deadline and cleanup_ns >= admitted_ns:
                                cleanup_intervened = True
            receipt_valid = (
                type(receipt) is dict
                and receipt.get("event") == "owner_explicit_keyup"
                and receipt.get("key") == key
                and receipt.get("operation") == "up"
                and receipt.get("owner_id") == self._inner.owner_id
                and receipt.get("server_keyup_verified") is True
            )
            ordinary = (
                lease_state["ordinary_release_candidate"] and history_complete
                and not cleanup_intervened and receipt_valid
            )
            admission_receipt, admission_receipt_valid = self._admission_receipt_for_release(
                marker, lease, "down", key, started_ns)
            transitions.append({
                "event": "input_release_transition",
                "transition_schema": "input-release-transition-v3",
                "operation": "up", "key": key,
                "owner_id": self._inner.owner_id,
                "intent_token": self._intent_token(lease),
                "valid_until_ns": getattr(lease, "deadline", None),
                "release_call_started_ns": started_ns,
                "release_call_returned_ns": returned_ns,
                "release_call_bracket_ns": returned_ns - started_ns,
                "owner_transition_verified": receipt_valid,
                "admission_receipt": admission_receipt,
                "admission_receipt_valid": admission_receipt_valid,
                "owner_explicit_keyup_failure": (
                    dict(receipt) if not receipt_valid and type(receipt) is dict else None
                ),
                "grants_input_authority": False,
                **lease_state,
                "owner_release_history_complete": history_complete,
                "owner_cleanup_intervened": cleanup_intervened,
                "ordinary_release_candidate": ordinary,
                "measurement_contract": (
                    "one serialized owner-thread batch brackets ordered explicit UPs; "
                    "per-key keymap samples occur after the original UP batch; each "
                    "transition carries its matching input-admission receipt when valid"
                ),
            })
        return transitions

    def call(self, operation, lease=None, key=None):
        if operation == "up_batch":
            return self._call_up_batch(lease, key)
        if operation not in ("up", "button_up"):
            records_before = (
                self._records_snapshot()
                if operation in ("down", "button_down", "release") else None
            )
            self._prune_completed_admissions(records_before)
            started_ns = time.perf_counter_ns() if operation in ("release", "close") else None
            try:
                result = self._inner.call(operation, lease, key)
            except RuntimeError as error:
                failed_release = getattr(error, "owner_release_record", None)
                if (operation != "release" or type(failed_release) is not dict or
                        failed_release.get("event") != "owner_release" or
                        failed_release.get("verified") is not False):
                    raise
                # Surface the bounded failed receipt to the executor so its
                # terminal can retain the stuck-key state and all attempts.
                result = failed_release
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
                            identity_field = "key" if operation == "down" else "payload"
                            admission_receipt = {
                                "event": result.get("event"),
                                "operation": operation,
                                identity_field: result.get(identity_field),
                                "owner_id": self._inner.owner_id,
                                "intent_token": result.get("intent_token"),
                                "valid_until_ns": result.get("valid_until_ns"),
                                "admitted_ns": result.get("admitted_ns"),
                                "input_ack_ns": result.get("input_ack_ns"),
                            }
                            self._admission_records[admission_key] = (
                                lease, len(records_before), deadline, admitted_ns,
                                admission_receipt)
            if isinstance(result, dict) and result.get("event") == "owner_release":
                result.setdefault("release_call_started_ns", started_ns)
                result.setdefault("release_call_returned_ns", returned_ns)
                self._clear_admissions_for_lease(lease)
            return result

        # No input_state/keymap query and no event publication occurs here.
        release_call_started_ns = time.perf_counter_ns()
        lease_state = self._lease_state_at(lease, release_call_started_ns)
        admission_key = self._admission_key(lease, key)
        admission_marker = None
        if admission_key is not None:
            with self._admission_records_lock:
                admission_marker = self._admission_records.pop(admission_key, None)
        explicit_keyup_failure = None
        try:
            result = self._inner.call(operation, lease, key)
        except RuntimeError as error:
            failed_receipt = getattr(error, "owner_explicit_keyup_record", None)
            if (operation != "up" or type(failed_receipt) is not dict or
                    failed_receipt.get("event") != "owner_explicit_keyup" or
                    failed_receipt.get("operation") != "up" or
                    failed_receipt.get("key") != key or
                    failed_receipt.get("server_keyup_verified") is not False or
                    failed_receipt.get("key_state_source") != "x11_query_keymap"):
                raise
            explicit_keyup_failure = failed_receipt
            result = None
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
            admitted_lease, record_index, admitted_deadline, admitted_ns, _ = admission_marker
            if (admitted_lease is not lease
                    or type(record_index) is not int or record_index < 0
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

        admission_operation = "down" if operation == "up" else "button_down"
        admission_receipt, admission_receipt_valid = self._admission_receipt_for_release(
            admission_marker, lease, admission_operation, key, release_call_started_ns)
        return {
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
            "owner_transition_verified": (False if explicit_keyup_failure is not None else None),
            "admission_receipt": admission_receipt,
            "admission_receipt_valid": admission_receipt_valid,
            "owner_explicit_keyup_failure": (
                dict(explicit_keyup_failure) if explicit_keyup_failure is not None else None
            ),
            "grants_input_authority": False,
            **lease_state,
            "owner_release_history_complete": owner_release_history_complete,
            "owner_cleanup_intervened": owner_cleanup_intervened,
            "ordinary_release_candidate": (
                ordinary_release_candidate and explicit_keyup_failure is None
            ),
            "measurement_contract": (
                "caller brackets unchanged InputOwner v10 explicit release; the release "
                "history since admission must contain no same-lease owner cleanup; no "
                "owner/X11 state sample or telemetry publication occurs inside this call; "
                "the returned transition includes its matching admission receipt"
            ),
        }
