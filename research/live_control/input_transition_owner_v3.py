"""Fail-closed non-staggering explicit-release telemetry over InputOwner v10.

Per explicit release this wrapper does no owner/X11 state sample and publishes
nothing. It only snapshots cheap local lease state, brackets the unchanged v10
call with monotonic caller timestamps, and returns a receipt to the backend.
"""
import time

from input_owner_v10 import InputOwner as Previous


class InputOwner:
    def __init__(self, display_name, _owner_cls=Previous):
        self._inner = _owner_cls(display_name)

    @property
    def owner_id(self):
        return self._inner.owner_id

    @property
    def records(self):
        return list(self._inner.records)

    def close(self):
        return self._inner.close()

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

    def call(self, operation, lease=None, key=None):
        if operation not in ("up", "button_up"):
            started_ns = time.perf_counter_ns() if operation in ("release", "close") else None
            result = self._inner.call(operation, lease, key)
            returned_ns = time.perf_counter_ns() if started_ns is not None else None
            result = self._decorate(result, lease)
            if isinstance(result, dict) and result.get("event") == "owner_release":
                result.setdefault("release_call_started_ns", started_ns)
                result.setdefault("release_call_returned_ns", returned_ns)
            return result

        # No input_state/keymap query and no event publication occurs here.
        release_call_started_ns = time.perf_counter_ns()
        lease_state = self._lease_state_at(lease, release_call_started_ns)
        result = self._inner.call(operation, lease, key)
        release_call_returned_ns = time.perf_counter_ns()
        if result is not None:
            raise AssertionError("InputOwner v10 explicit release unexpectedly returned payload")
        if release_call_returned_ns < release_call_started_ns:
            raise AssertionError("monotonic release clock moved backwards")

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
            "owner_transition_verified": None,
            "grants_input_authority": False,
            **lease_state,
            "measurement_contract": (
                "caller brackets unchanged InputOwner v10 explicit release; no owner/X11 "
                "state sample or telemetry publication occurs inside this per-input call"
            ),
        }
