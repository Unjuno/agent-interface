"""Observation wrapper for InputOwner v10 physical-release transition windows.

The wrapped owner remains authoritative for all X11 work.  This layer only brackets
explicit key/button releases from the caller thread and preserves the existing
owner thread's no-callback/no-logging property.
"""
import time

from input_owner_v10 import InputOwner as Previous


class InputOwner:
    def __init__(self, display_name, _owner_cls=Previous):
        self._inner = _owner_cls(display_name)
        self.transition_records = []

    @property
    def owner_id(self):
        return self._inner.owner_id

    @property
    def records(self):
        # owner records contain independent expiry/cancel releases; transition
        # records contain explicit caller-observed release windows.
        return list(self._inner.records) + list(self.transition_records)

    def close(self):
        return self._inner.close()

    @staticmethod
    def _intent_token(lease):
        return getattr(lease, "intent_token", None) if lease is not None else None

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

        # Do not sample before release: that would extend the physical hold merely
        # to observe it.  The timestamp is taken immediately before enqueueing
        # the existing v10 up/button_up call; v10 returns only after d.sync when
        # it actually owns the input.  A post-release owner sample is safe.
        release_call_started_ns = time.perf_counter_ns()
        result = self._inner.call(operation, lease, key)
        release_call_returned_ns = time.perf_counter_ns()
        after = self._inner.call("input_state")
        if result is not None:
            raise AssertionError("InputOwner v10 explicit release unexpectedly returned payload")

        field = "owned_keycodes" if operation == "up" else "owned_buttons"
        after_owned = list(after[field])
        record = {
            "event": "input_release_transition",
            "operation": operation,
            "key" if operation == "up" else "button": key,
            "owner_id": after["owner_id"],
            "intent_token": self._intent_token(lease),
            "valid_until_ns": getattr(lease, "deadline", None) if lease is not None else None,
            "release_call_started_ns": release_call_started_ns,
            "release_call_returned_ns": release_call_returned_ns,
            "owner_sample_after_started_ns": after["sample_started_ns"],
            "owned_count_after": len(after_owned),
            "owner_transition_verified": None,
            "measurement_contract": (
                "release is bracketed by the caller around InputOwner v10 up/button_up; "
                "v10 returns after X11 d.sync when it owns the input; owner state is "
                "sampled only after release so instrumentation does not extend the hold"
            ),
        }
        self.transition_records.append(record)
        return record
