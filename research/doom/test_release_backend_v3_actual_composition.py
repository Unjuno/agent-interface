"""Construction check across the real v4 owner wrapper and release backend."""
import importlib
import sys
import types
import unittest
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
LIVE = HERE.parent / "live_control"


class ActualReleaseCompositionTests(unittest.TestCase):
    def _run(self, *, wrong_key=False, step_exception=False, cleanup_exception=False,
             emit_accept_then_raise=False, cancel_after_sync=False,
             capture_publication_error=False, sink_accept_before_raise=True,
             failure_position=0, capture_step_exception=False,
             fail_incomplete_publication=False,
             incomplete_publication_rows=False,
             release_all_publication_failure=False,
             return_backend=False, mutate_release_row_before_raise=False):
        emitted = []
        attempts = []
        fail_emit = [emit_accept_then_raise or release_all_publication_failure]

        def emit(row):
            attempts.append(dict(row))
            if (fail_incomplete_publication
                    and row.get("event") == "input_release_transition"
                    and row.get("release_batch_complete") is False
                    and row.get("release_batch_position") == failure_position):
                fail_emit[0] = False
                if sink_accept_before_raise:
                    emitted.append(dict(row))
                if mutate_release_row_before_raise:
                    row["release_batch_position"] = 99
                raise OSError("incomplete receipt sink failed")
            if (fail_emit[0] and row.get("event") == "input_release_transition"
                    and row.get("release_batch_position") == failure_position):
                fail_emit[0] = False
                if sink_accept_before_raise:
                    emitted.append(dict(row))
                if mutate_release_row_before_raise:
                    row["release_batch_position"] = 99
                raise RuntimeError("sink failed after accepting release row")
            emitted.append(dict(row))
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
                if emit_accept_then_raise:
                    self.raw("c", True)
                self.raw("a", False)
                if emit_accept_then_raise:
                    self.raw("b", False)
                    self.raw("c", False)
                    return
                if incomplete_publication_rows:
                    self._release_batch.context["rows"] = [
                        {"event": "input_release_transition", "key": key,
                         "release_batch_step": 0}
                        for key in ("a", "b", "c")
                    ]
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
                try:
                    candidate.execute({}, None, "program-1", 0)
                except RuntimeError as exc:
                    if capture_step_exception:
                        return exc, attempts, emitted, candidate.release_all()
                    self.assertEqual(str(exc), "later step failed")
            elif cleanup_exception:
                for key in ("a", "b"):
                    candidate.raw(key, True)
                candidate.raw("a", False)
                with self.assertRaisesRegex(RuntimeError, "cleanup failed after partial release"):
                    candidate.release_all()
            elif emit_accept_then_raise:
                try:
                    candidate.execute({}, None, "program-1", 0)
                except RuntimeError as exc:
                    if capture_publication_error:
                        return exc, attempts, emitted
                    self.assertEqual(str(exc), "sink failed after accepting release row")
            elif release_all_publication_failure:
                for key in ("a", "b"):
                    candidate.raw(key, True)
                candidate.raw("a", False)
                try:
                    candidate.release_all()
                except RuntimeError as exc:
                    return exc, attempts, emitted
            else:
                for key in ("a", "b"):
                    candidate.raw(key, True)
                for key in ("a", "b"):
                    candidate.raw(key, False)
            releases = [row for row in emitted if row.get("event") == "input_release_transition"]
            admissions = [row for row in emitted if row.get("event") == "input_admission"]
            if return_backend:
                return admissions, releases, candidate
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

    def test_release_all_without_current_batch_does_not_return_prior_program_ledger(self):
        _, releases, backend = self._run(
            emit_accept_then_raise=True, failure_position=None, return_backend=True)
        self.assertEqual([row["release_batch_position"] for row in releases], [0, 1, 2])
        self.assertIsNone(getattr(backend._release_batch, "context", None))
        self.assertEqual(backend._last_release_batch_delivery["identifier"], "program-1")

        release = backend.release_all()
        self.assertTrue(release["verified"])
        self.assertNotIn("release_batch_delivery", release)

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
        for failure_position in range(3):
            for accepted in (False, True):
                with self.subTest(failure_position=failure_position,
                                  sink_accept_before_raise=accepted):
                    error, attempts, emitted = self._run(
                        emit_accept_then_raise=True, capture_publication_error=True,
                        sink_accept_before_raise=accepted,
                        failure_position=failure_position)
                    release_attempts = [row for row in attempts
                                        if row.get("event") == "input_release_transition"]
                    self.assertEqual([row["release_batch_position"]
                                      for row in release_attempts], [0, 1, 2])
                    release_emitted = [row for row in emitted
                                       if row.get("event") == "input_release_transition"]
                    expected_emitted = (
                        list(range(failure_position))
                        + ([failure_position] if accepted else [])
                        + list(range(failure_position + 1, 3))
                    )
                    self.assertEqual([row["release_batch_position"]
                                      for row in release_emitted], expected_emitted)
                    self.assertEqual(sum(row["release_batch_position"] == failure_position
                                         for row in release_emitted), int(accepted))
                    self.assertTrue(all(row.get("release_batch_complete") is False
                                        for row in release_emitted
                                        if row["release_batch_position"] > failure_position))
                    self.assertEqual(str(error), "sink failed after accepting release row")
                    expected_states = [
                        "confirmed" if position < failure_position else
                        "unknown" if position == failure_position else
                        "confirmed_incomplete"
                        for position in range(3)
                    ]
                    ledger = getattr(error, "release_batch_publication", None)
                    self.assertEqual(ledger, {
                        "schema": "release-batch-delivery-v1",
                        "identifier": "program-1", "step": 0, "size": 3,
                        "positions": [
                            {"position": position, "step": 0,
                             "key": ("a", "b", "c")[position],
                             "state": expected_states[position]}
                            for position in range(3)
                        ],
                    })

    def test_executor_terminal_retains_actual_backend_delivery_positions(self):
        error, _, _ = self._run(
            emit_accept_then_raise=True, capture_publication_error=True,
            sink_accept_before_raise=False, failure_position=1)
        previous = sys.modules.get("executor_v13")
        sys.path.insert(0, str(LIVE))
        try:
            executor_module = importlib.import_module("executor_v13")

            class FailedPublicationBackend:
                sequence = 1

                def validate(self, steps):
                    pass

                def execute(self, step, cancel, identifier, index):
                    raise error

                def release_all(self):
                    return {"verified": True}

            events = []
            executor = executor_module.Executor(FailedPublicationBackend(), events.append)
            executor.submit("program-1", [{"op": "probe"}], 1,
                            time.perf_counter_ns() + 1_000_000_000)
            deadline = time.monotonic() + 1
            while not any(row.get("event") == "terminal" for row in events) and time.monotonic() < deadline:
                time.sleep(.002)
            executor.close()
            terminal = next(row for row in events if row.get("event") == "terminal")
            self.assertEqual(terminal["status"], "failed")
            self.assertEqual(terminal["release"]["release_batch_delivery"],
                             error.release_batch_publication)
        finally:
            sys.path.remove(str(LIVE))
            if previous is None:
                sys.modules.pop("executor_v13", None)
            else:
                sys.modules["executor_v13"] = previous

    def test_incomplete_publication_failure_keeps_row_status_on_original_exception(self):
        error, attempts, emitted, release = self._run(
            step_exception=True, capture_step_exception=True,
            fail_incomplete_publication=True, sink_accept_before_raise=False)
        self.assertEqual(str(error), "later step failed")
        self.assertEqual([row["release_batch_position"] for row in attempts
                          if row.get("event") == "input_release_transition"], [0])
        self.assertEqual([row["release_batch_position"] for row in emitted
                          if row.get("event") == "input_release_transition"], [])
        self.assertEqual(error.release_batch_publication, {
            "schema": "release-batch-delivery-v1", "identifier": "program-1",
            "step": 0, "size": 1,
            "positions": [{"position": 0, "step": 0, "key": "a", "state": "unknown"}],
        })
        self.assertNotIn("release_batch_delivery", release)

    def test_incomplete_publication_middle_failure_preserves_positions_on_original_exception(self):
        for accepted in (False, True):
            with self.subTest(sink_accept_before_raise=accepted):
                error, attempts, emitted, release = self._run(
                    step_exception=True, capture_step_exception=True,
                    fail_incomplete_publication=True,
                    incomplete_publication_rows=True,
                    sink_accept_before_raise=accepted, failure_position=1)
                attempted = [row["release_batch_position"] for row in attempts
                             if row.get("release_batch_complete") is False]
                self.assertEqual(attempted, [0, 1])
                self.assertEqual(
                    [row["release_batch_position"] for row in emitted
                     if row.get("release_batch_complete") is False],
                    [0, 1] if accepted else [0],
                )
                self.assertEqual(str(error), "later step failed")
                self.assertEqual(error.release_batch_publication, {
                    "schema": "release-batch-delivery-v1",
                    "identifier": "program-1", "step": 0, "size": 3,
                    "positions": [
                        {"position": 0, "step": 0, "key": "a",
                         "state": "confirmed_incomplete"},
                        {"position": 1, "step": 0, "key": "b", "state": "unknown"},
                        {"position": 2, "step": 0, "key": "c",
                         "state": "not_attempted"},
                    ],
                })
                self.assertNotIn("release_batch_delivery", release)

    def test_release_all_publication_failure_retains_delivery_ledger(self):
        error, attempts, emitted = self._run(
            release_all_publication_failure=True, failure_position=0,
            sink_accept_before_raise=False)
        self.assertEqual(str(error), "sink failed after accepting release row")
        self.assertEqual([row["release_batch_position"] for row in attempts
                          if row.get("event") == "input_release_transition"], [0])
        self.assertEqual([row for row in emitted
                          if row.get("event") == "input_release_transition"], [])
        self.assertEqual(error.release_batch_publication, {
            "schema": "release-batch-delivery-v1", "identifier": "program-1",
            "step": 0, "size": 1,
            "positions": [{"position": 0, "step": 0, "key": "a", "state": "unknown"}],
        })

    def test_sink_mutation_cannot_erase_failed_position_from_delivery_ledger(self):
        for position in range(3):
            for accepted in (False, True):
                with self.subTest(position=position, accepted=accepted):
                    error, _, _ = self._run(
                        emit_accept_then_raise=True, capture_publication_error=True,
                        sink_accept_before_raise=accepted, failure_position=position,
                        mutate_release_row_before_raise=True)
                    states = ["confirmed"] * position + ["unknown"] + [
                        "confirmed_incomplete"] * (2 - position)
                    self.assertEqual(
                        error.release_batch_publication["positions"],
                        [
                            {"position": i, "step": 0, "key": "abc"[i], "state": state}
                            for i, state in enumerate(states)
                        ],
                    )

    def test_incomplete_sink_mutation_cannot_erase_failed_position_from_delivery_ledger(self):
        for position in range(3):
            for accepted in (False, True):
                with self.subTest(position=position, accepted=accepted):
                    error, _, _, release = self._run(
                        step_exception=True, capture_step_exception=True,
                        fail_incomplete_publication=True,
                        incomplete_publication_rows=True,
                        sink_accept_before_raise=accepted, failure_position=position,
                        mutate_release_row_before_raise=True)
                    self.assertEqual(str(error), "later step failed")
                    self.assertNotIn("release_batch_delivery", release)
                    states = ["confirmed_incomplete"] * position + ["unknown"] + [
                        "not_attempted"] * (2 - position)
                    self.assertEqual(
                        error.release_batch_publication["positions"],
                        [
                            {"position": i, "step": 0, "key": "abc"[i], "state": state}
                            for i, state in enumerate(states)
                        ],
                    )


if __name__ == "__main__":
    unittest.main()
