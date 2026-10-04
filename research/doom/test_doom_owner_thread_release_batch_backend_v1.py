"""Fault-injection tests for release-batch sink publication uncertainty."""
import importlib.util
import sys
import threading
import types
import unittest
from pathlib import Path
from types import SimpleNamespace


class Previous:
    def execute(self, step, cancel, identifier, index):
        return self._publish_release_batch(self._release_batch.context)


def load_backend():
    previous_name = "doom_typed_release_backend_v2"
    owner_name = "input_transition_owner_v4"
    saved = {name: sys.modules.get(name) for name in (previous_name, owner_name)}
    previous = types.ModuleType(previous_name)
    previous.Backend = Previous
    previous.suite = object()
    owner = types.ModuleType(owner_name)
    owner.InputOwner = object
    sys.modules[previous_name] = previous
    sys.modules[owner_name] = owner
    try:
        name = "_test_doom_owner_thread_release_batch_backend_v1"
        spec = importlib.util.spec_from_file_location(
            name, Path(__file__).with_name("doom_owner_thread_release_batch_backend_v1.py")
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.modules.pop("_test_doom_owner_thread_release_batch_backend_v1", None)
        for name, original in saved.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


BACKEND_MODULE = load_backend()


class Owner:
    records = []

    def call(self, operation, *args):
        if operation == "input_state":
            return {
                "owner_id": "owner-test",
                "owned_keycodes": [],
                "sample_started_ns": 30,
                "sample_finished_ns": 31,
            }
        raise AssertionError(operation)


class ReleaseBatchPublicationTests(unittest.TestCase):
    def make_backend(self, *, accept_then_raise):
        backend = object.__new__(BACKEND_MODULE.Backend)
        backend.owner = Owner()
        backend.lease = SimpleNamespace(intent_token="token-test")
        backend._release_batch = threading.local()
        context = {"identifier": "program-test", "step": 0, "rows": []}
        for index in range(3):
            context["rows"].append({
                "owner_id": "owner-test",
                "intent_token": "token-test",
                "release_call_started_ns": index + 1,
                "release_call_returned_ns": index + 10,
                "backend_owned_before_release": True,
                "ordinary_release_candidate": True,
                "owner_thread_keyup_verified": True,
                "owner_thread_keyup_receipt": None,
                "owner_cleanup_record_count_before_release": 0,
            })
        backend._release_batch.context = context
        backend.attempted = []
        backend.delivered = []

        def emit(row):
            position = row["release_batch_position"]
            backend.attempted.append(position)
            if position == 1:
                if accept_then_raise:
                    backend.delivered.append(dict(row))
                raise OSError("injected sink failure")
            backend.delivered.append(dict(row))

        backend.emit = emit
        return backend

    def test_failed_sink_attempt_is_bound_as_delivery_unknown(self):
        backend = self.make_backend(accept_then_raise=False)
        with self.assertRaises(OSError) as raised:
            backend.execute({}, object(), "program-test", 0)

        error = raised.exception
        self.assertEqual(getattr(error, "delivery_status", None), "unknown")
        self.assertEqual(getattr(error, "batch_identifier", None), "program-test")
        self.assertEqual(getattr(error, "batch_position", None), 1)
        self.assertEqual(getattr(error, "batch_size", None), 3)
        self.assertEqual(getattr(error, "published_positions", None), (0,))
        self.assertEqual(getattr(error, "sink_error_type", None), "OSError")
        self.assertIsInstance(error.__cause__, OSError)
        self.assertIn("position=1", repr(error))
        self.assertEqual(backend.attempted, [0, 1, 2])
        self.assertEqual(
            [(row["release_batch_position"], row["release_batch_complete"])
             for row in backend.delivered],
            [(0, True), (2, False)],
        )

    def test_accept_then_raise_is_not_retried_and_remains_ambiguous(self):
        backend = self.make_backend(accept_then_raise=True)
        with self.assertRaises(OSError) as raised:
            backend.execute({}, object(), "program-test", 0)

        error = raised.exception
        self.assertEqual(getattr(error, "delivery_status", None), "unknown")
        self.assertEqual(getattr(error, "batch_position", None), 1)
        self.assertEqual(getattr(error, "published_positions", None), (0,))
        self.assertIsInstance(error.__cause__, OSError)
        self.assertEqual(backend.attempted, [0, 1, 2])
        self.assertEqual(
            [row["release_batch_position"] for row in backend.delivered],
            [0, 1, 2],
        )

    def test_base_exception_type_is_preserved_with_failure_coordinates(self):
        backend = self.make_backend(accept_then_raise=False)

        def emit(row):
            position = row["release_batch_position"]
            backend.attempted.append(position)
            if position == 1:
                raise KeyboardInterrupt()
            backend.delivered.append(dict(row))

        backend.emit = emit
        with self.assertRaises(KeyboardInterrupt) as raised:
            backend.execute({}, object(), "program-test", 0)

        self.assertTrue(any("position=1" in note for note in raised.exception.__notes__))
        self.assertEqual(backend.attempted, [0, 1, 2])


if __name__ == "__main__":
    unittest.main()
