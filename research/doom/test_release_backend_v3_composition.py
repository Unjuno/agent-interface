import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent


class ReleaseBackendCompositionTests(unittest.TestCase):
    def _load_candidate(self, module, previous_base):
        previous_owner = sys.modules.get("input_transition_owner_v4")
        sys.modules["input_transition_owner_v4"] = module
        base = types.ModuleType("doom_typed_release_backend_v2")
        base.Backend = previous_base
        base.suite = object()
        old_base = sys.modules.get("doom_typed_release_backend_v2")
        sys.modules["doom_typed_release_backend_v2"] = base
        sys.path.insert(0, str(HERE))
        import doom_owner_thread_release_batch_backend_v1 as candidate
        return candidate, previous_owner, old_base

    def test_release_batch_preserves_backend_v2_program_step_provenance(self):
        """Owner-thread receipts stay joinable to the v2 input-admission stream."""
        emitted = []
        module = types.ModuleType("input_transition_owner_v4")

        class Owner:
            owner_id = "owner-1"
            records = []

            def __init__(self, display_name):
                self.display_name = display_name
                self.records = []

            def close(self):
                pass

            def call(self, operation, lease=None, key=None):
                if operation == "down":
                    return {"event": "input_admission", "operation": operation, "key": key,
                            "owner_id": self.owner_id, "intent_token": "lease-1"}
                if operation == "up":
                    count = len(self.records)
                    receipt = {
                        "event": "owner_explicit_keyup", "operation": "up", "key": key,
                        "keycode": 25, "owner_id": self.owner_id,
                        "intent_token": "lease-1", "valid_until_ns": None,
                        "owner_keyrelease_started_ns": 12,
                        "owner_sync_returned_ns": 13,
                        "server_sync_completed": True,
                        "physical_verification_authoritative": False,
                    }
                    self.records.append(receipt)
                    return {
                        "event": "input_release_transition",
                        "operation": operation,
                        "key": key,
                        "owner_id": self.owner_id,
                        "release_call_started_ns": 10,
                        "release_call_returned_ns": 20,
                        "owner_cleanup_record_count_before_release": count,
                        "owner_thread_keyup_verified": True,
                        "owner_thread_keyup_receipt": receipt,
                        "ordinary_release_candidate": True,
                        "intent_token": "lease-1",
                    }
                if operation == "input_state":
                    return {
                        "owner_id": self.owner_id,
                        "sample_started_ns": 31,
                        "sample_finished_ns": 32,
                        "owned_keycodes": [],
                    }
                raise AssertionError(operation)

        module.InputOwner = Owner
        class Previous:
            def __init__(self, session, out, emit, signal_readers):
                self.owner = Owner(session.name)
                self._input_event_context = None
                self.held = set()
                self.emit = emit
                self._release_batch = types.SimpleNamespace()

            def execute(self, step, cancel, identifier, index):
                if self._input_event_context is not None:
                    raise RuntimeError("nested input telemetry context")
                self._input_event_context = (identifier, index)
                previous = getattr(self._release_batch, "context", None)
                if previous is not None and previous.get("identifier") == identifier:
                    context = previous
                else:
                    context = {"rows": [], "identifier": identifier}
                context["step"] = index
                self._release_batch.context = context
                try:
                    result = self.raw(step["key"], step["down"])
                finally:
                    self._input_event_context = None
                if context["rows"]:
                    self._release_batch.context = context
                else:
                    try:
                        del self._release_batch.context
                    except AttributeError:
                        pass
                return result
        candidate, previous_owner, previous_base = self._load_candidate(module, Previous)
        try:
            with patch.object(candidate, "InputOwner", Owner):
                backend = candidate.Backend(types.SimpleNamespace(name="display"), None,
                                             emitted.append, {"health": 1, "ammo": 1},
                                             run_id="scorer-run-7")
            backend.lease = types.SimpleNamespace(intent_token="lease-1")
            backend.execute({"key": "w", "down": True}, None, "program-7", 3)
            admission = emitted.pop()
            self.assertEqual((admission["id"], admission["step"]), ("program-7", 3))
            self.assertEqual(admission["run_id"], "scorer-run-7")
            self.assertEqual(admission["session_id"], "scorer-run-7")
            backend.execute({"key": "w", "down": False}, None, "program-7", 3)

            release = emitted.pop()
            self.assertEqual(release["event"], "input_release_transition")
            self.assertEqual(release["run_id"], "scorer-run-7")
            self.assertEqual(release["session_id"], "scorer-run-7")
            self.assertEqual(
                (release["release_batch_identifier"], release["release_batch_step"]),
                ("program-7", 3),
            )
            self.assertTrue(release["owner_thread_keyup_verified_after_batch"])
            self.assertTrue(release["owner_transition_verified"])
            self.assertEqual((release["id"], release["step"]), ("program-7", 3))
        finally:
            sys.path.remove(str(HERE))
            sys.modules.pop("doom_owner_thread_release_batch_backend_v1", None)
            if previous_base is None:
                sys.modules.pop("doom_typed_release_backend_v2", None)
            else:
                sys.modules["doom_typed_release_backend_v2"] = previous_base
            if previous_owner is None:
                sys.modules.pop("input_transition_owner_v4", None)
            else:
                sys.modules["input_transition_owner_v4"] = previous_owner

    def test_partial_release_batch_is_discarded_on_step_exception(self):
        emitted = []
        module = types.ModuleType("input_transition_owner_v4")

        class Owner:
            owner_id = "owner-1"

            def __init__(self, display_name):
                self.records = []

            def close(self):
                pass

            def call(self, operation, lease=None, key=None):
                if operation == "up":
                    return {
                        "event": "input_release_transition", "key": key,
                        "owner_id": self.owner_id, "intent_token": "lease-1",
                        "release_call_started_ns": 1, "release_call_returned_ns": 2,
                        "owner_thread_keyup_verified": True,
                        "owner_thread_keyup_receipt": {"event": "owner_explicit_keyup"},
                        "ordinary_release_candidate": True,
                    }
                raise AssertionError(operation)

        module.InputOwner = Owner

        class Previous:
            def __init__(self, session, out, emit, signal_readers):
                self.owner = Owner(session.name)
                self._input_event_context = None
                self.held = {"a", "b"}
                self.emit = emit
                self._release_batch = types.SimpleNamespace()

            def execute(self, step, cancel, identifier, index):
                self._input_event_context = (identifier, index)
                old = getattr(self._release_batch, "context", None)
                context = old if old and old.get("identifier") == identifier else {
                    "rows": [], "identifier": identifier
                }
                context["step"] = index
                self._release_batch.context = context
                try:
                    self.raw(step["key"], False)
                    if step.get("raise"):
                        raise RuntimeError("step failed after release")
                finally:
                    self._input_event_context = None
                if context["rows"]:
                    self._release_batch.context = context
                else:
                    del self._release_batch.context

        candidate, previous_owner, previous_base = self._load_candidate(module, Previous)
        try:
            with patch.object(candidate, "InputOwner", Owner):
                backend = candidate.Backend(types.SimpleNamespace(name="display"), None,
                                             emitted.append, {"health": 1, "ammo": 1})
            backend.lease = types.SimpleNamespace(intent_token="lease-1")
            with self.assertRaisesRegex(RuntimeError, "step failed after release"):
                backend.execute({"key": "a", "raise": True}, None, "program-8", 0)
            self.assertFalse(hasattr(backend._release_batch, "context"))
            self.assertEqual(len(emitted), 1)
            release = emitted[0]
            self.assertEqual(release["event"], "input_release_transition")
            self.assertEqual((release["id"], release["step"]), ("program-8", 0))
            self.assertTrue(release["owner_thread_keyup_verified"])
            self.assertFalse(release["owner_transition_verified"])
            self.assertFalse(release["release_batch_complete"])
            self.assertEqual(release["release_batch_disposition"], "step_exception")
        finally:
            sys.path.remove(str(HERE))
            sys.modules.pop("doom_owner_thread_release_batch_backend_v1", None)
            if previous_base is None:
                sys.modules.pop("doom_typed_release_backend_v2", None)
            else:
                sys.modules["doom_typed_release_backend_v2"] = previous_base
            if previous_owner is None:
                sys.modules.pop("input_transition_owner_v4", None)
            else:
                sys.modules["input_transition_owner_v4"] = previous_owner


if __name__ == "__main__":
    unittest.main()
