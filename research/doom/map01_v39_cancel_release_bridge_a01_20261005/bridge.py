"""V39 adapter that forwards owner-verified cancellation up outcomes.

This opt-in research successor preserves the V39 input seam while adding a
barrier after each program step. It emits a cleanup up outcome only when an
InputOwner v13 per-key row joins to the exact admission identity and context.
"""
from __future__ import annotations

import copy
import time

from doom_typed_release_backend_v1 import Backend as Previous, suite
from .input_owner_v13 import InputOwner


def _text(value):
    return type(value) is str and bool(value.strip())


def _interval(value):
    return (type(value) is list and len(value) == 2
            and all(type(item) is int and item >= 0 for item in value)
            and value[0] <= value[1])


class Backend(Previous):
    def __init__(self, session, out, emit, signal_readers):
        super().__init__(session, out, emit, signal_readers)
        self.owner.close()
        self.owner = InputOwner(session.name)
        self._input_event_context = None
        self._active_admissions = {}

    def execute(self, step, cancel, identifier, index):
        if self._input_event_context is not None:
            raise RuntimeError("nested input telemetry context")
        self._input_event_context = (identifier, index)
        record_start = len(self.owner.records)
        primary_failed = False
        try:
            return super().execute(step, cancel, identifier, index)
        except BaseException:
            primary_failed = True
            raise
        finally:
            try:
                self._forward_verified_cleanup(
                    record_start,
                    wait_for_cancel=(self._cancel_requested(cancel)
                                     or self._cancel_requested(
                                         getattr(self.lease, "cancel", None))))
            except BaseException:
                # Preserve the action's original exception. A failed barrier
                # cannot reconcile held state or manufacture a release event.
                if not primary_failed:
                    raise
            finally:
                self._input_event_context = None

    @staticmethod
    def _cancel_requested(cancel):
        for candidate in (cancel, getattr(cancel, "cancel", None)):
            is_set = getattr(candidate, "is_set", None)
            if callable(is_set) and is_set():
                return True
        return False

    def _forward_verified_cleanup(self, record_start, wait_for_cancel=False):
        """Serialize with the owner, then publish only exact per-admission rows."""
        if wait_for_cancel:
            deadline = time.monotonic() + 0.5
            while (len(self.owner.records) <= record_start
                   and time.monotonic() < deadline):
                time.sleep(0.002)
            if len(self.owner.records) <= record_start:
                return
        state = self.owner.call("input_state")
        owner_id = getattr(self.owner, "owner_id", None)
        if (not isinstance(state, dict) or not _text(owner_id)
                or state.get("owner_id") != owner_id
                or state.get("owned_keycodes") != []
                or state.get("owned_buttons") != []):
            return

        records = list(self.owner.records[record_start:])
        for release in records:
            if (not isinstance(release, dict)
                    or release.get("event") != "owner_release"
                    or release.get("verified") is not True
                    or release.get("keys_down") != []
                    or release.get("buttons_down") != []):
                continue
            measurements = release.get("per_key_release_measurements")
            if type(measurements) is not list:
                continue

            by_key = {}
            for measured in measurements:
                key = measured.get("key") if isinstance(measured, dict) else None
                if type(key) is str:
                    by_key.setdefault(key, []).append(measured)
            emitted_keys = set()
            for key, candidates in by_key.items():
                if len(candidates) != 1:
                    continue
                measured = candidates[0]
                if measured.get("edge") != "up":
                    continue
                admission = self._active_admissions.get(key) if type(key) is str else None
                bracket = measured.get("bracket")
                if (not isinstance(admission, dict)
                        or admission.get("key") != key
                        or admission.get("owner_id") != owner_id
                        or not isinstance(bracket, dict)
                        or bracket.get("owner_id") != owner_id
                        or bracket.get("key") != key
                        or bracket.get("intent_token") != admission.get("intent_token")
                        or measured.get("actuation_id") != admission.get("actuation_id")
                        or measured.get("classification") != bracket.get("status")):
                    continue

                physical = copy.deepcopy(measured)
                interval = bracket.get("physical_up_interval")
                classification = measured.get("classification")
                if classification == "CONFIRMED_PHYSICAL_UP" and not _interval(interval):
                    continue
                adapter_edge = None
                if classification == "CONFIRMED_PHYSICAL_UP" and _interval(interval):
                    adapter_edge = dict(
                        edge="up", status=classification,
                        actuation_id=admission["actuation_id"], owner_id=owner_id,
                        intent_token=admission["intent_token"], key=key,
                        interval=list(interval), grants_input_authority=False)
                physical["adapter_edge"] = adapter_edge
                physical["grants_input_authority"] = False
                physical["application_consumption_observed"] = False
                row = dict(
                    event="input_release_measurement", key=key,
                    id=admission["id"], step=admission["step"],
                    owner_id=owner_id,
                    intent_token=admission["intent_token"],
                    cleanup_reason=release.get("reason"),
                    physical_key_measurement=physical,
                    owner_release={
                        "event": "owner_release",
                        "reason": release.get("reason"),
                        "verified": True,
                        "keys_down": [],
                        "buttons_down": [],
                        "verified_ns": release.get("verified_ns"),
                        "per_key_release_measurements": [copy.deepcopy(measured)],
                    },
                    grants_input_authority=False,
                    application_consumption_observed=False,
                )
                self.emit(row)
                emitted_keys.add(key)

            # Aggregate neutral state can clear the bridge's key membership
            # only where the owner supplied a unique matching admission row.
            for key in set(self.held):
                candidates = by_key.get(key, [])
                admission = self._active_admissions.get(key)
                if len(candidates) != 1:
                    continue
                measured = candidates[0]
                bracket = measured.get("bracket")
                if (not isinstance(admission, dict)
                        or not isinstance(bracket, dict)
                        or measured.get("edge") != "up"
                        or measured.get("release_attempted") is not True
                        or measured.get("classification") != bracket.get("status")
                        or admission.get("owner_id") != owner_id
                        or measured.get("actuation_id") != admission.get("actuation_id")
                        or bracket.get("owner_id") != owner_id
                        or bracket.get("key") != key
                        or bracket.get("intent_token") != admission.get("intent_token")):
                    continue
                self.held.discard(key)
                self._active_admissions.pop(key, None)
            for key in emitted_keys:
                self._active_admissions.pop(key, None)

    def raw(self, key, down):
        context = self._input_event_context
        if context is None:
            raise RuntimeError("keyboard input outside program/step telemetry context")

        operation = "down" if down else "up"
        record = self.owner.call(operation, self.lease, key)
        if down:
            self.held.add(key)
        else:
            self.held.discard(key)
        if record is None:
            return

        row = dict(record)
        row["id"], row["step"] = context
        owner_id = getattr(self.owner, "owner_id", None)
        intent_token = getattr(self.lease, "intent_token", None)
        row.setdefault("owner_id", owner_id)
        row.setdefault("intent_token", intent_token)

        measurement = row.get("physical_key_measurement")
        actuation_id = (measurement.get("actuation_id")
                        if isinstance(measurement, dict) else None)
        if (down and record.get("event") == "input_admission"
                and type(key) is str and _text(owner_id) and _text(intent_token)
                and _text(actuation_id) and type(context[0]) is str
                and bool(context[0]) and type(context[1]) is int
                and context[1] >= 0):
            existing = self._active_admissions.get(key)
            if not (isinstance(existing, dict)
                    and existing.get("actuation_id") == actuation_id
                    and existing.get("owner_id") == owner_id):
                self._active_admissions[key] = dict(
                    key=key, owner_id=owner_id, intent_token=intent_token,
                    actuation_id=actuation_id, id=context[0], step=context[1])

        if (not down and isinstance(measurement, dict)
                and measurement.get("classification") == "CONFIRMED_PHYSICAL_UP"
                and type(key) is str):
            admission = self._active_admissions.get(key)
            if (isinstance(admission, dict)
                    and measurement.get("actuation_id") == admission.get("actuation_id")):
                self._active_admissions.pop(key, None)
        self.emit(row)
