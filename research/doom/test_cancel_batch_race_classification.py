"""A verified owner cancellation superseding a delayed release batch is cancellation."""
import importlib.util
import sys
import threading
import types
import unittest
from pathlib import Path


class Cancelled(Exception):
    pass


def load_backend():
    previous_names = (
        "doom_typed_release_backend_v2",
        "input_transition_owner_v4",
        "doom_owner_thread_release_batch_backend_v1",
    )
    saved = {name: sys.modules.get(name) for name in previous_names}
    previous = types.ModuleType("doom_typed_release_backend_v2")

    class BaseBackend:
        def execute(self, step, cancel, identifier, index):
            self.raw("space", False)

    previous.Backend = BaseBackend
    previous.suite = object()
    owner = types.ModuleType("input_transition_owner_v4")
    owner.InputOwner = object
    sys.modules["doom_typed_release_backend_v2"] = previous
    sys.modules["input_transition_owner_v4"] = owner
    try:
        path = Path(__file__).with_name("doom_owner_thread_release_batch_backend_v1.py")
        spec = importlib.util.spec_from_file_location(
            "doom_owner_thread_release_batch_backend_v1_cancel_race_test", path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.Backend
    finally:
        for name, old_module in saved.items():
            if old_module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old_module


Backend = load_backend()


class FakeOwner:
    owner_id = "synthetic-owner"

    def __init__(self, verified_cancel):
        self.calls = []
        self.records = (
            [{"event": "owner_release", "reason": "cancelled", "verified": True,
              "keys_down": [], "buttons_down": []}]
            if verified_cancel else []
        )

    def call(self, operation, lease=None, key=None):
        self.calls.append((operation, lease, key))
        if operation == "up_batch":
            raise ValueError("up_batch requires the active input lease")
        raise AssertionError(operation)


class FakeLease:
    intent_token = "synthetic-intent"

    def __init__(self, owner, verified_cancel):
        self.owner = owner
        self.verified_cancel = verified_cancel
        self.check_calls = 0

    def check(self):
        self.check_calls += 1
        verified_empty_cancel = any(
            row.get("event") == "owner_release"
            and row.get("reason") == "cancelled"
            and row.get("verified") is True
            and row.get("keys_down") == []
            and row.get("buttons_down") == []
            for row in self.owner.records
        )
        if self.verified_cancel and verified_empty_cancel:
            raise Cancelled()


class CancelBatchClassificationTests(unittest.TestCase):
    @staticmethod
    def backend(verified_cancel):
        backend = object.__new__(Backend)
        backend._release_batch = threading.local()
        backend._last_release_batch_delivery = None
        backend._input_event_context = ("synthetic-program", 7)
        backend.owner = FakeOwner(verified_cancel)
        backend.lease = FakeLease(backend.owner, verified_cancel)
        backend.held = {"space"}
        backend.emit = lambda row: None
        backend._finish_incomplete_release_batch = (
            lambda context, error, disposition: None
        )
        return backend

    def test_verified_empty_owner_cancel_maps_race_to_cancelled_and_keeps_unknown_receipt(self):
        backend = self.backend(True)
        try:
            backend.execute({"op": "synthetic"}, object(), "synthetic-program", 7)
        except Exception as exc:
            outcome = type(exc)
        else:
            outcome = None
        self.assertIs(outcome, Cancelled)

        context = backend._release_batch.context
        self.assertEqual(len(backend.owner.calls), 1)
        self.assertEqual(context["pending_ups"], [])
        self.assertEqual(len(context["rows"]), 1)
        self.assertEqual(
            context["rows"][0]["release_batch_call_outcome"], "unknown_no_retry"
        )
        self.assertEqual(backend.lease.check_calls, 1)

    def test_cancelled_pending_disposition_survives_later_step_failure(self):
        backend = self.backend(True)
        # Exercise the real production incomplete-publication cleanup rather
        # than the no-op fixture hook used by the two smaller tests above.
        del backend._finish_incomplete_release_batch
        backend.lease.cancel = threading.Event()
        backend.lease.cancel.set()
        backend_type = type(backend)
        base_type = backend_type.__mro__[1]
        original_execute = base_type.execute

        def fail_after_release_classification(self, step, cancel, identifier, index):
            self.raw("space", False)
            raise RuntimeError("subsequent operation failed")

        base_type.execute = fail_after_release_classification
        try:
            with self.assertRaisesRegex(RuntimeError, "subsequent operation failed") as caught:
                backend.execute({}, object(), "synthetic-program", 7)
        finally:
            base_type.execute = original_execute

        self.assertEqual(
            getattr(caught.exception, "cancelled_pending_ups", None),
            [{"key": "space", "identifier": "synthetic-program", "step": 7,
              "backend_owned_before_release": True,
              "disposition": "not_attempted_owner_cancel_release"}],
        )
        self.assertFalse(hasattr(backend._release_batch, "context"))
        self.assertEqual(backend.owner.calls, [])

    def test_without_verified_cancel_preserves_original_failure(self):
        backend = self.backend(False)
        try:
            backend.execute({"op": "synthetic"}, object(), "synthetic-program", 7)
        except Exception as exc:
            outcome = (type(exc), str(exc))
        else:
            outcome = None
        self.assertEqual(
            outcome, (ValueError, "up_batch requires the active input lease")
        )

        context = backend._release_batch.context
        self.assertEqual(len(backend.owner.calls), 1)
        self.assertEqual(len(context["rows"]), 1)
        self.assertEqual(
            context["rows"][0]["release_batch_call_outcome"], "unknown_no_retry"
        )


if __name__ == "__main__":
    unittest.main()
