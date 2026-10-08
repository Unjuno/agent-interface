"""Regression for step UP racing a verified cancellation-owner release."""
import importlib
import sys
import threading
import types
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIVE = HERE.parent / "live_control"


class Lease:
    intent_token = "lease-1"
    deadline = 999999999999999

    def __init__(self):
        self.cancel = threading.Event()


class Owner:
    owner_id = "owner-1"

    def __init__(self, _display):
        self.records = []
        self.held = set()
        self.active = None
        self.up_batch_calls = 0

    def close(self):
        pass

    def call(self, op, lease=None, key=None):
        if op == "down":
            self.active = lease
            self.held.add(key)
            row = {"event": "input_admission", "operation": "down", "key": key,
                   "owner_id": self.owner_id, "intent_token": lease.intent_token,
                   "valid_until_ns": lease.deadline, "admitted_ns": 1,
                   "input_ack_ns": 2}
            self.records.append(row)
            return row
        if op == "up_batch":
            self.up_batch_calls += 1
            if self.active is not lease or lease is None:
                raise ValueError("up_batch requires the active input lease")
            self.held.difference_update(key)
            return [{"event": "input_release_transition", "operation": "up",
                     "key": item, "owner_id": self.owner_id,
                     "intent_token": lease.intent_token,
                     "valid_until_ns": lease.deadline,
                     "release_call_started_ns": 7,
                     "release_call_returned_ns": 11,
                     "ordinary_release_candidate": True}
                    for item in key]
        if op == "cancel":
            lease.cancel.set()
            return self._release(lease, "cancelled")
        if op == "release":
            return self._release(
                lease, "cancelled" if lease.cancel.is_set() else "release")
        if op == "input_state":
            return {"owner_id": self.owner_id, "sample_started_ns": 12,
                    "sample_finished_ns": 13, "owned_keycodes": []}
        raise AssertionError(op)

    def _release(self, lease, reason):
        self.held.clear()
        row = {"event": "owner_release", "reason": reason, "verified": True,
               "keys_down": [], "buttons_down": [], "keys_unknown": [],
               "key_state_errors": [], "verified_ns": 14,
               "valid_until_ns": lease.deadline}
        self.records.append(row)
        self.active = None
        return row


class TransitionOwner:
    """Test owner boundary: ordinary RPCs delegate; stale batch is rejected."""

    def __init__(self, display, _owner_cls=Owner):
        self._inner = _owner_cls(display)

    @property
    def owner_id(self):
        return self._inner.owner_id

    @property
    def records(self):
        return list(self._inner.records)

    def close(self):
        self._inner.close()

    def call(self, op, lease=None, key=None):
        return self._inner.call(op, lease, key)


class PreviousBackend:
    def __init__(self, session, out, emit, signal_readers, *, cancel_before_up):
        self.owner = Owner(session.name)
        self.held = set()
        self.lease = None
        self._input_event_context = None
        self.emit = emit
        self.cancel_before_up = cancel_before_up

    def execute(self, _step, _cancel, identifier, index):
        self._input_event_context = (identifier, index)
        self.raw("Down", True)
        if self.cancel_before_up:
            self.owner.call("cancel", self.lease)
        self.raw("Down", False)

    def release_all(self):
        return self.owner.call("release", self.lease)


class CancelledLeaseReleaseTests(unittest.TestCase):
    def _run(self, *, cancelled):
        emitted = []
        base = types.ModuleType("doom_typed_release_backend_v2")

        class BackendBase(PreviousBackend):
            def __init__(self, session, out, emit, readers):
                super().__init__(session, out, emit, readers,
                                 cancel_before_up=cancelled)

        base.Backend = BackendBase
        base.suite = object()
        low_level = types.ModuleType("input_owner_v12")
        low_level.InputOwner = Owner
        transition = types.ModuleType("input_transition_owner_v3")
        transition.InputOwner = TransitionOwner
        names = ("input_owner_v12", "input_transition_owner_v3",
                 "input_transition_owner_v4", "doom_typed_release_backend_v2",
                 "doom_owner_thread_release_batch_backend_v1")
        prior = {name: sys.modules.get(name) for name in names}
        old_path = list(sys.path)
        for path in (str(LIVE), str(HERE)):
            if path not in sys.path:
                sys.path.insert(0, path)
        sys.modules["input_owner_v12"] = low_level
        sys.modules["input_transition_owner_v3"] = transition
        sys.modules["doom_typed_release_backend_v2"] = base
        try:
            owner_v4 = importlib.import_module("input_transition_owner_v4")
            backend_module = importlib.import_module(
                "doom_owner_thread_release_batch_backend_v1")
            self.assertIs(backend_module.InputOwner, owner_v4.InputOwner)
            backend = backend_module.Backend(types.SimpleNamespace(name="display"), None,
                                             emitted.append, {})
            backend.lease = Lease()
            backend.execute({}, backend.lease.cancel, "program-1", 0)
            release = backend.release_all()
            return backend, emitted, release
        finally:
            sys.path[:] = old_path
            for name, value in prior.items():
                if value is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = value

    def test_cancelled_pending_up_is_not_sent_to_revoked_lease(self):
        backend, emitted, release = self._run(cancelled=True)
        self.assertTrue(release["verified"])
        self.assertEqual(backend.owner._inner.up_batch_calls, 0)
        self.assertEqual(backend.owner.records[-1]["reason"], "cancelled")
        self.assertEqual(release["cancelled_pending_ups"], [{
            "key": "Down", "identifier": "program-1", "step": 0,
            "backend_owned_before_release": True,
            "disposition": "not_attempted_owner_cancel_release",
        }])
        self.assertFalse(any(row.get("event") == "input_release_transition"
                             for row in emitted))

    def test_ordinary_pending_up_still_uses_up_batch(self):
        backend, emitted, release = self._run(cancelled=False)
        self.assertTrue(release["verified"])
        self.assertEqual(backend.owner._inner.up_batch_calls, 1)
        transitions = [row for row in emitted
                       if row.get("event") == "input_release_transition"]
        self.assertEqual(len(transitions), 1)
        self.assertEqual(transitions[0]["key"], "Down")
        self.assertNotIn("cancelled_pending_ups", release)


if __name__ == "__main__":
    unittest.main()
