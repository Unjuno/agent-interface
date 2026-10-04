"""Construction check across the real v4 owner wrapper and release backend."""
import importlib
import sys
import types
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
LIVE = HERE.parent / "live_control"


class ActualReleaseCompositionTests(unittest.TestCase):
    def _run(self, *, wrong_key=False, step_exception=False, cleanup_exception=False,
             emit_accept_then_raise=False, cancel_after_sync=False):
        emitted = []
        fail_emit = [emit_accept_then_raise]

        def emit(row):
            emitted.append(dict(row))
            if fail_emit[0] and row.get("event") == "input_release_transition":
                fail_emit[0] = False
                raise RuntimeError("sink failed after accepting release row")
        low_level = types.ModuleType("input_owner_v12")
        transition = types.ModuleType("input_transition_owner_v3")
        backend_base = types.ModuleType("doom_typed_release_backend_v2")

        class Owner:
            owner_id = "owner-1"

            def __init__(self, display_name):
                self.records = []
                self.held = set()

            def close(self):
                pass

            def call(self, operation, lease=None, key=None):
                if operation == "down":
                    self.held.add(key)
                    return {"event": "input_admission", "operation": "down", "key": key,
                            "admitted_ns": 10, "input_ack_ns": 11,
                            "owner_id": self.owner_id,
                            "intent_token": lease.intent_token,
                            "valid_until_ns": lease.deadline}
                if operation == "up":
                    self.held.discard(key)
                    self.records.append({
                        "event": "owner_explicit_keyup", "operation": "up",
                        "key": "wrong" if wrong_key and key == "a" else key,
                        "owner_id": self.owner_id, "intent_token": lease.intent_token,
                        "valid_until_ns": lease.deadline,
                        "owner_keyrelease_started_ns": 20,
                        "owner_sync_returned_ns": 21,
                        "cancel_requested_after_sync": cancel_after_sync,
                        "server_sync_completed": True,
                        "physical_verification_authoritative": False,
                    })
                    return None
                if operation == "input_state":
                    return {"owner_id": self.owner_id, "sample_started_ns": 31,
                            "sample_finished_ns": 32, "owned_keycodes": sorted(self.held)}
                raise AssertionError(operation)

        class TransitionOwner:
            def __init__(self, display_name, _owner_cls=Owner):
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
                return getattr(lease, "intent_token", None)

            def call(self, operation, lease=None, key=None):
                if operation == "up":
                    self._inner.call(operation, lease, key)
                    return {
                        "event": "input_release_transition", "operation": operation,
                        "key": key, "owner_id": self.owner_id,
                        "intent_token": lease.intent_token, "valid_until_ns": lease.deadline,
                        "release_call_started_ns": 19,
                        "release_call_returned_ns": 22,
                        "ordinary_release_candidate": True,
                    }
                return self._inner.call(operation, lease, key)

        class PreviousBackend:
            def __init__(self, session, out, emit, signal_readers):
                self.owner = Owner(session.name)
                self.held = set()
                self.lease = None
                self._input_event_context = None
                self.emit = emit

            def execute(self, step, cancel, identifier, index):
                self._input_event_context = (identifier, index)
                self.raw("a", True)
                self.raw("b", True)
                self.raw("a", False)
                if emit_accept_then_raise:
                    self.raw("b", False)
                    return
                raise RuntimeError("later step failed")

            def release_all(self):
                if cleanup_exception:
                    raise RuntimeError("cleanup failed after partial release")
                return {"verified": True}

        low_level.InputOwner = Owner
        transition.InputOwner = TransitionOwner
        backend_base.Backend = PreviousBackend
        backend_base.suite = object()
        prior = {name: sys.modules.get(name) for name in (
            "input_owner_v12", "input_transition_owner_v3", "input_transition_owner_v4",
            "doom_typed_release_backend_v2", "doom_owner_thread_release_batch_backend_v1",
        )}
        for path in (str(LIVE), str(HERE)):
            sys.path.insert(0, path)
        sys.modules["input_owner_v12"] = low_level
        sys.modules["input_transition_owner_v3"] = transition
        sys.modules["doom_typed_release_backend_v2"] = backend_base
        try:
            owner_v4 = importlib.import_module("input_transition_owner_v4")
            backend = importlib.import_module("doom_owner_thread_release_batch_backend_v1")
            # Ensure the backend imports the real wrapper implementation under test.
            self.assertIs(backend.InputOwner, owner_v4.InputOwner)
            candidate = backend.Backend(types.SimpleNamespace(name="display"), None,
                                        emit, {})
            candidate.lease = types.SimpleNamespace(intent_token="lease-1", deadline=99)
            candidate._input_event_context = ("program-1", 0)
            candidate._release_batch.context = {"rows": [], "identifier": "program-1",
                                                "step": 0}
            if step_exception:
                with self.assertRaisesRegex(RuntimeError, "later step failed"):
                    candidate.execute({}, None, "program-1", 0)
            elif cleanup_exception:
                for key in ("a", "b"):
                    candidate.raw(key, True)
                candidate.raw("a", False)
                with self.assertRaisesRegex(RuntimeError, "cleanup failed after partial release"):
                    candidate.release_all()
            elif emit_accept_then_raise:
                with self.assertRaisesRegex(RuntimeError, "sink failed after accepting release row"):
                    candidate.execute({}, None, "program-1", 0)
            else:
                for key in ("a", "b"):
                    candidate.raw(key, True)
                for key in ("a", "b"):
                    candidate.raw(key, False)
            releases = [row for row in emitted if row.get("event") == "input_release_transition"]
            admissions = [row for row in emitted if row.get("event") == "input_admission"]
            return admissions, releases
        finally:
            for path in (str(LIVE), str(HERE)):
                if path in sys.path:
                    sys.path.remove(path)
            for name, value in prior.items():
                if value is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = value

    def test_current_v4_wrapper_joins_each_key_admission_to_its_release(self):
        admissions, releases = self._run()
        self.assertEqual([row["key"] for row in admissions], ["a", "b"])
        self.assertTrue(all(row["event"] == "input_admission"
                            and row["operation"] == "down"
                            and row["intent_token"] == "lease-1"
                            and (row["id"], row["step"]) == ("program-1", 0)
                            and row["admitted_ns"] <= row["input_ack_ns"]
                            for row in admissions))
        self.assertEqual([row["key"] for row in releases], ["a", "b"])
        self.assertTrue(all(row["operation"] == "up"
                            and row["intent_token"] == "lease-1"
                            and (row["id"], row["step"]) == ("program-1", 0)
                            for row in releases))
        self.assertEqual([row["owner_thread_keyup_receipt"]["key"] for row in releases],
                         ["a", "b"])
        self.assertTrue(all(
            row["owner_thread_keyup_receipt"]["owner_id"] == "owner-1"
            and row["owner_thread_keyup_receipt"]["intent_token"] == "lease-1"
            and row["owner_thread_keyup_receipt"]["valid_until_ns"] == 99
            and row["owner_thread_keyup_receipt"]["owner_keyrelease_started_ns"]
                <= row["owner_thread_keyup_receipt"]["owner_sync_returned_ns"]
            for row in releases
        ))
        self.assertTrue(all(row["owner_transition_verified"] for row in releases))
        self.assertEqual([row["release_batch_position"] for row in releases], [0, 1])
        self.assertEqual([row["release_batch_size"] for row in releases], [2, 2])

    def test_wrong_key_receipt_fails_closed_through_batch_composition(self):
        _, releases = self._run(wrong_key=True)
        self.assertEqual([row["key"] for row in releases], ["a", "b"])
        self.assertFalse(any(row["owner_transition_verified"] for row in releases))
        self.assertFalse(any(row["owner_thread_keyup_verified_after_batch"] for row in releases))

    def test_cancel_during_keyup_sync_fails_closed_through_batch_composition(self):
        _, releases = self._run(cancel_after_sync=True)
        self.assertEqual([row["key"] for row in releases], ["a", "b"])
        self.assertTrue(all(row["cancel_requested_after_sync"] for row in releases))
        self.assertTrue(all(row["owner_thread_keyup_verified"] for row in releases))
        self.assertFalse(any(row["ordinary_release_candidate"] for row in releases))
        self.assertFalse(any(row["owner_transition_verified"] for row in releases))

    def test_current_v4_wrapper_retains_partial_receipt_on_later_step_exception(self):
        _, releases = self._run(step_exception=True)
        self.assertEqual([row["key"] for row in releases], ["a"])
        self.assertEqual(releases[0]["owner_thread_keyup_receipt"]["key"], "a")
        self.assertTrue(releases[0]["owner_thread_keyup_verified"])
        self.assertFalse(releases[0]["owner_transition_verified"])
        self.assertFalse(releases[0]["release_batch_complete"])
        self.assertEqual(releases[0]["release_batch_disposition"], "step_exception")

    def test_cleanup_exception_publishes_partial_receipt_before_propagating(self):
        _, releases = self._run(cleanup_exception=True)
        self.assertEqual([row["key"] for row in releases], ["a"])
        self.assertTrue(releases[0]["owner_thread_keyup_verified"])
        self.assertFalse(releases[0]["owner_transition_verified"])
        self.assertFalse(releases[0]["release_batch_complete"])
        self.assertEqual(releases[0]["release_batch_disposition"], "release_all_exception")

    def test_accept_then_raise_does_not_duplicate_release_batch_rows(self):
        _, releases = self._run(emit_accept_then_raise=True)
        self.assertEqual(len(releases), 2)
        self.assertEqual([row["owner_thread_keyup_receipt"]["key"] for row in releases],
                         ["a", "b"])
        self.assertEqual([row["release_batch_position"] for row in releases], [0, 1])
        self.assertEqual([row["release_batch_size"] for row in releases], [2, 2])
        self.assertEqual([row["release_batch_complete"] for row in releases], [True, False])
        self.assertEqual(releases[1]["release_batch_disposition"], "publication_exception")


if __name__ == "__main__":
    unittest.main()
