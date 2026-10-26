"""Narrow caller journal tests for the opt-in Win32 operation owner."""
import copy
import asyncio
import hashlib
import json
import time
import unittest
from unittest.mock import Mock

from runtime.guarded_win32_v1.operation_owner import OperationOwner, OwnerRefused
from runtime.cli_v1.owned_win32_session import OwnedWin32SessionOwner
from runtime.cli_v1.mcp_guarded import register_guarded_tools
from runtime.backends.win32_v1.backend import Win32Backend


GEN_A = "a" * 64
GEN_B = "b" * 64
CALL_ID = "1" * 32
ACTION_ID = "2" * 32


def orphan_custody_record():
    return {"classification": "UNKNOWN_RELEASE_UNCONFIRMED_STOPPED",
        "operation_id": ACTION_ID, "target_generation": GEN_A,
        "obligations": ["key:map01:W"], "do_not_replay": True,
        "dispatch": {"input_dispatched": None, "release_confirmed": False,
            "task_success": None, "replay_allowed": False}}


class FakeProcess:
    def __init__(self, pid):
        self.pid = pid
        self.exitcode = None
        self.alive = True

    def is_alive(self):
        return self.alive


class StartableFakeProcess(FakeProcess):
    def __init__(self, pid):
        super().__init__(None)
        self.requested_pid = pid

    def start(self):
        self.pid = self.requested_pid


class FakeCancellationSupervisor:
    def __init__(self, owner):
        self.owner = owner
        self.calls = []
        self.closed = False

    def producer_started(self, operation_id, generation, process, *, process_identity):
        return self.owner.producer_started(operation_id, generation, process,
                                           process_identity=process_identity)

    def cancel(self, operation_id, generation, *, cleanup_deadline_ns):
        self.calls.append((operation_id, generation, cleanup_deadline_ns))
        self.owner.request_cancel(operation_id, generation,
                                  cleanup_deadline_ns=cleanup_deadline_ns)
        return self.owner.result(operation_id)

    def close(self):
        self.closed = True


class FakeToolServer:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def register(function):
            self.tools[function.__name__] = function
            return function
        return register


class OwnedWin32SessionTests(unittest.TestCase):
    def setUp(self):
        self.clock = time.monotonic_ns
        self.process = FakeProcess(4101)
        self.identity = {"pid": self.process.pid, "creation_time_100ns": 9001}
        self.owner = OperationOwner(clock_ns=self.clock,
            process_identity_reader=lambda handle: self.identity
            if handle is self.process else None)
        self.supervisor = FakeCancellationSupervisor(self.owner)
        self.session = OwnedWin32SessionOwner(self.owner, self.supervisor)

    def start_action(self):
        self.session.admit_action(CALL_ID, ACTION_ID, GEN_A,
            operation_deadline_ns=self.clock() + 5_000_000_000,
            obligations=["key:a"], action_metadata={"operation":"guarded_input"})
        self.assertTrue(self.session.producer_started(CALL_ID, self.process,
                                                      process_identity=self.identity))
        self.assertTrue(self.owner.authorize_producer_start(
            ACTION_ID, GEN_A, self.process, lambda: None))

    def test_backend_target_generation_rejects_same_process_new_hwnd_at_public_admission(self):
        backend = object.__new__(Win32Backend)
        backend.targets = {'fixture': 42}
        backend.user32 = Mock()
        backend.user32.IsWindow.return_value = True
        backend.user32.GetPropW.return_value = 98765
        backend._window_owner_identity_for_hwnd = Mock(return_value={
            'pid': 51, 'creation_time_100ns': 7001,
            'window_thread_id': 701})
        self.session.bind_target_generation_reader(
            lambda: backend.target_generation('fixture'))

        binding = self.session.bind_target_generation()
        backend.targets['fixture'] = 43
        with self.assertRaisesRegex(RuntimeError, 'TARGET_GENERATION_CHANGED'):
            self.session.admit_action_from_binding(CALL_ID, ACTION_ID,
                binding['target_binding_id'],
                operation_deadline_ns=self.clock() + 5_000_000_000,
                obligations=['key:a'])
        self.assertEqual(self.owner._records, {})

    def test_duplicate_cancel_keeps_action_and_cancellation_receipts_separate(self):
        self.start_action()
        action_before = self.session.interface_result(CALL_ID)["action"]
        deadline = self.clock() + 3_000_000_000
        first = self.session.cancel_guarded(CALL_ID,
            cancellation_operation_id="3" * 32,
            cleanup_deadline_ns=deadline)
        second = self.session.cancel_guarded(CALL_ID,
            cancellation_operation_id="4" * 32,
            cleanup_deadline_ns=deadline + 1_000_000_000)
        self.assertEqual(first["status"], "pending")
        self.assertEqual(first["operation_id"], "3" * 32)
        self.assertEqual(second["operation_id"], first["operation_id"])
        self.assertEqual(len(self.supervisor.calls), 1)
        self.assertEqual(self.session.interface_result(CALL_ID)["action"], action_before)
        self.assertFalse(first["release_confirmed"])
        self.assertIsNone(first["task_success"])
        self.assertFalse(first["replay_allowed"])

        self.owner.mark_unknown(ACTION_ID, GEN_A, "synthetic_test_uncertainty")
        pending = self.session.interface_result(CALL_ID)
        self.assertEqual(pending["action"], action_before)
        self.assertEqual(pending["cancellation"]["status"], "unknown")
        self.assertEqual(pending["cancellation"]["operation_id"], "3" * 32)
        self.assertFalse(pending["cancellation"]["release_confirmed"])
        self.assertIsNone(pending["cancellation"]["task_success"])
        self.assertFalse(pending["cancellation"]["replay_allowed"])

        terminal_action = {"status":"runtime_interrupted", "task_success":None,
                           "replay_allowed":False, "effect_status":"unknown"}
        self.session.record_action_result(CALL_ID, terminal_action)
        final = self.session.interface_result(CALL_ID)
        self.assertEqual(final["action"]["result"], terminal_action)
        self.assertEqual(final["cancellation"], pending["cancellation"])

    def test_unknown_operation_cannot_be_replaced_by_new_action_in_same_session(self):
        self.start_action()
        self.session.cancel_guarded(CALL_ID, cancellation_operation_id="3" * 32,
            cleanup_deadline_ns=self.clock() + 3_000_000_000)
        self.owner.mark_unknown(ACTION_ID, GEN_A, "cleanup_unconfirmed")
        prior = self.session.interface_result(CALL_ID)
        with self.assertRaises(OwnerRefused):
            self.session.admit_action("5" * 32, "6" * 32, GEN_B,
                operation_deadline_ns=self.clock() + 5_000_000_000,
                obligations=["key:b"], action_metadata={"operation":"guarded_input"})
        self.assertEqual(self.session.interface_result(CALL_ID), prior)

    def test_fresh_session_does_not_mutate_old_unknown_receipt(self):
        self.start_action()
        self.session.cancel_guarded(CALL_ID, cancellation_operation_id="3" * 32,
            cleanup_deadline_ns=self.clock() + 3_000_000_000)
        self.owner.mark_unknown(ACTION_ID, GEN_A, "cleanup_unconfirmed")
        old = copy.deepcopy(self.session.interface_result(CALL_ID))

        new_process = FakeProcess(4102)
        new_identity = {"pid": new_process.pid, "creation_time_100ns": 9002}
        new_owner = OperationOwner(clock_ns=self.clock,
            process_identity_reader=lambda handle: new_identity
            if handle is new_process else None)
        new_session = OwnedWin32SessionOwner(new_owner, FakeCancellationSupervisor(new_owner))
        new_session.admit_action("7" * 32, "8" * 32, GEN_B,
            operation_deadline_ns=self.clock() + 5_000_000_000,
            obligations=["key:b"], action_metadata={"operation":"guarded_input"})
        self.assertEqual(self.session.interface_result(CALL_ID), old)
        self.assertEqual(new_session.interface_result("7" * 32)["action"]["status"],
                         "admitted")

    def test_close_keeps_custody_open_while_action_is_unresolved(self):
        self.start_action()
        result = self.session.close()
        self.assertEqual(result["status"], "busy")
        self.assertEqual(self.session.state, "open")
        self.assertFalse(self.supervisor.closed)

    def test_standard_action_completion_keeps_action_and_release_receipt_separate(self):
        self.start_action()
        self.process.alive = False
        self.process.exitcode = 0
        result = {"status": "completed", "task_success": None,
                  "replay_allowed": False, "effect_status": "unknown"}
        release = {"verified": True, "keys_down": [], "buttons_down": [],
                   "keys_unknown": [], "buttons_unknown": []}

        complete = getattr(self.session, "complete_action", None)
        self.assertTrue(callable(complete), "standard action completion is not retained")
        row = complete(CALL_ID, self.process, result, release_receipt=release,
            readback={"operation_id": ACTION_ID, "target_generation": GEN_A,
                "producer_exit_confirmed_ns": 1,
                "observed_monotonic_ns": self.clock(), "neutral": True})

        self.assertEqual(row["action"]["status"], "completed")
        self.assertEqual(row["action"]["result"], result)
        self.assertTrue(row["action"]["release_confirmed"])
        self.assertIsNone(row["action"]["task_success"])
        self.assertFalse(row["action"]["replay_allowed"])
        self.assertIsNone(row["cancellation"])
        self.assertEqual(self.session.close()["status"], "closed")
        self.assertTrue(self.supervisor.closed)

    def test_exited_action_collects_backend_release_and_independent_readback_once(self):
        self.start_action()
        self.process.alive = False
        self.process.exitcode = 0
        reads = []
        backend_result = {"status": "completed", "effect_status": "unknown"}
        release = {"verified": True, "keys_down": [], "buttons_down": [],
                   "keys_unknown": [], "buttons_unknown": []}

        def read_result(process):
            self.assertIs(process, self.process)
            self.assertFalse(process.is_alive())
            reads.append("result")
            return {"result": backend_result, "release_receipt": release,
                "producer_timing": {"clock": "time.monotonic_ns",
                    "child_ready_monotonic_ns": self.clock()}}

        def readback(request):
            reads.append("readback")
            return {"operation_id": request["operation_id"],
                "target_generation": request["target_generation"],
                "producer_exit_confirmed_ns": request["producer_exit_confirmed_ns"],
                "observed_monotonic_ns": self.clock(), "neutral": True}

        complete = getattr(self.session, "complete_exited_action", None)
        self.assertTrue(callable(complete), "exited producer result collection is missing")
        row = complete(CALL_ID, result_reader=read_result,
                       readback_reader=readback)

        self.assertEqual(reads, ["result", "readback"])
        self.assertEqual(row["action"]["result"], backend_result)
        self.assertIn("child_ready_monotonic_ns",
                      row["action"]["producer_timing"])
        self.assertTrue(row["action"]["release_confirmed"])
        self.assertIsNone(row["action"]["task_success"])
        self.assertFalse(row["action"]["replay_allowed"])

        repeated = complete(CALL_ID,
            result_reader=lambda _process: self.fail("completed result reread"),
            readback_reader=lambda _request: self.fail("completed readback repeated"))
        self.assertEqual(repeated, row)

    def test_live_action_is_not_read_as_completed(self):
        self.start_action()
        reads = []

        row = self.session.complete_exited_action(CALL_ID,
            result_reader=lambda _process: reads.append("result"),
            readback_reader=lambda _request: reads.append("readback"))

        self.assertEqual(row["action"]["status"], "running")
        self.assertEqual(reads, [])

    def test_invalid_exited_result_keeps_release_and_task_effect_unknown(self):
        self.start_action()
        self.process.alive = False
        self.process.exitcode = 1

        row = self.session.complete_exited_action(CALL_ID,
            result_reader=lambda _process: {"result": {"status": "failed"}},
            readback_reader=lambda _request: self.fail("invalid producer packet must stop"))

        self.assertEqual(row["action"]["status"], "unknown")
        self.assertFalse(row["action"].get("release_confirmed", False))
        self.assertIsNone(row["action"]["task_success"])
        self.assertFalse(row["action"]["replay_allowed"])

    def test_standard_program_admission_freezes_target_and_full_input_obligations(self):
        self.session.bind_target_generation_reader(lambda: GEN_A)
        binding = self.session.bind_target_generation()
        program = {"schema": "agent-interface/program-v1",
            "program_id": "standard-caller-save",
            "source": {"observation_seq": 1, "binding_revision": 1,
                "target_generations": {"fixture": GEN_A}},
            "authority": {"lease_id": "standard-save",
                "expires_at_ns": self.clock() + 4_000_000_000},
            "terminal": {"release_all_required": True},
            "ops": [
                {"op": "focus", "target": "fixture"},
                {"op": "key_chord", "keys": ["CTRL", "S"]},
                {"op": "text", "text": "A😀"},
                {"op": "release_all"},
            ]}

        admit = getattr(self.session, "admit_standard_action", None)
        self.assertTrue(callable(admit), "standard program admission is not connected")
        row = admit(CALL_ID, ACTION_ID, binding["target_binding_id"], program,
            operation_deadline_ns=self.clock() + 5_000_000_000,
            current_observation_seq=1, current_binding_revision=1)

        self.assertEqual(row["action"]["target_generation"], GEN_A)
        self.assertEqual(self.session._calls[CALL_ID]["standard_program"], program)
        self.assertEqual(self.owner.result(ACTION_ID)["obligations"], [
            "key:fixture:CTRL", "key:fixture:S", "unicode:0041",
            "unicode:D83D", "unicode:DE00",
        ])
        self.assertEqual(row["action"]["metadata"]["source"], "interface_dispatch")

    def test_standard_program_is_forwarded_to_the_supervised_producer(self):
        self.session.bind_target_generation_reader(lambda: GEN_A)
        binding = self.session.bind_target_generation()
        program = {"schema": "agent-interface/program-v1",
            "program_id": "standard-caller-save",
            "source": {"observation_seq": 1, "binding_revision": 1,
                "target_generations": {"fixture": GEN_A}},
            "authority": {"lease_id": "standard-save",
                "expires_at_ns": self.clock() + 4_000_000_000},
            "terminal": {"release_all_required": True},
            "ops": [{"op": "focus", "target": "fixture"},
                {"op": "key_chord", "keys": ["CTRL", "S"]},
                {"op": "release_all"}]}
        self.session.admit_standard_action(CALL_ID, ACTION_ID,
            binding["target_binding_id"], program,
            operation_deadline_ns=self.clock() + 5_000_000_000,
            current_observation_seq=1, current_binding_revision=1)

        process = StartableFakeProcess(4102)
        identity = {"pid": 4102, "creation_time_100ns": 9002}
        self.process = process
        self.identity = identity
        received = []
        result = self.session.start_producer(CALL_ID, lambda action: (
            received.append(action) or process,
            lambda: identity,
            lambda: None))

        self.assertEqual(result["action"]["status"], "running")
        self.assertEqual(received[0]["program"], program)
        self.assertEqual(received[0]["operation_id"], ACTION_ID)
        timing = result["action"]["producer_timing"]
        self.assertEqual(timing["clock"], "time.monotonic_ns")
        stages = ("factory_requested_monotonic_ns",
                  "factory_returned_monotonic_ns",
                  "process_start_called_monotonic_ns",
                  "process_start_returned_monotonic_ns",
                  "identity_verified_monotonic_ns",
                  "start_gate_authorized_monotonic_ns")
        self.assertTrue(all(type(timing.get(stage)) is int for stage in stages), timing)
        self.assertEqual(sorted(timing[stage] for stage in stages),
                         [timing[stage] for stage in stages])

    def test_standard_program_authority_lease_cannot_be_reused_for_replay(self):
        self.session.bind_target_generation_reader(lambda: GEN_A)
        program = {"schema": "agent-interface/program-v1",
            "program_id": "standard-caller-save",
            "source": {"observation_seq": 1, "binding_revision": 1,
                "target_generations": {"fixture": GEN_A}},
            "authority": {"lease_id": "one-use-save-lease",
                "expires_at_ns": self.clock() + 4_000_000_000},
            "terminal": {"release_all_required": True},
            "ops": [{"op": "focus", "target": "fixture"},
                {"op": "key_chord", "keys": ["CTRL", "S"]},
                {"op": "release_all"}]}
        first_binding = self.session.bind_target_generation()
        self.session.admit_standard_action(CALL_ID, ACTION_ID,
            first_binding["target_binding_id"], program,
            operation_deadline_ns=self.clock() + 5_000_000_000,
            current_observation_seq=1, current_binding_revision=1)
        self.assertTrue(self.session.producer_started(CALL_ID, self.process,
            process_identity=self.identity))
        self.assertTrue(self.owner.authorize_producer_start(ACTION_ID, GEN_A,
            self.process, lambda: None))
        self.process.alive = False
        self.process.exitcode = 0
        self.session.complete_action(CALL_ID, self.process,
            {"status": "completed"},
            release_receipt={"verified": True, "keys_down": [],
                "buttons_down": [], "keys_unknown": [], "buttons_unknown": []},
            readback={"operation_id": ACTION_ID,
                "target_generation": GEN_A,
                "producer_exit_confirmed_ns": 1,
                "observed_monotonic_ns": self.clock(), "neutral": True})

        second_binding = self.session.bind_target_generation()
        with self.assertRaisesRegex(ValueError, "lease ID already used"):
            self.session.admit_standard_action("3" * 32, "4" * 32,
                second_binding["target_binding_id"], program,
                operation_deadline_ns=self.clock() + 5_000_000_000,
                current_observation_seq=1, current_binding_revision=1)

        self.assertEqual(set(self.owner._records), {ACTION_ID})

    def test_invalid_standard_program_is_rejected_before_custody_admission(self):
        self.session.bind_target_generation_reader(lambda: GEN_A)
        binding = self.session.bind_target_generation()

        admit = getattr(self.session, "admit_standard_action", None)
        self.assertTrue(callable(admit), "standard program admission is not connected")
        with self.assertRaises(ValueError):
            admit(CALL_ID, ACTION_ID, binding["target_binding_id"],
                {"program_id": "invalid", "ops": [
                    {"op": "focus", "target": "fixture"},
                    {"op": "key_chord", "keys": ["CTRL"]},
                ]}, operation_deadline_ns=self.clock() + 5_000_000_000,
                current_observation_seq=1, current_binding_revision=1)
        self.assertEqual(self.owner._records, {})

    def test_standard_program_stale_generation_is_rejected_before_admission(self):
        self.session.bind_target_generation_reader(lambda: GEN_A)
        binding = self.session.bind_target_generation()
        program = {"schema": "agent-interface/program-v1",
            "program_id": "stale-generation",
            "source": {"observation_seq": 1, "binding_revision": 1,
                "target_generations": {"fixture": GEN_B}},
            "authority": {"lease_id": "stale-generation",
                "expires_at_ns": self.clock() + 4_000_000_000},
            "terminal": {"release_all_required": True},
            "ops": [{"op": "focus", "target": "fixture"},
                {"op": "key_chord", "keys": ["CTRL"]},
                {"op": "release_all"}]}

        with self.assertRaisesRegex(ValueError, "TARGET_GENERATION_CHANGED"):
            self.session.admit_standard_action(CALL_ID, ACTION_ID,
                binding["target_binding_id"], program,
                operation_deadline_ns=self.clock() + 5_000_000_000,
                current_observation_seq=1, current_binding_revision=1)
        self.assertEqual(self.owner._records, {})

    def test_standard_program_source_sequence_or_binding_mismatch_is_rejected(self):
        self.session.bind_target_generation_reader(lambda: GEN_A)
        binding = self.session.bind_target_generation()
        program = {"schema": "agent-interface/program-v1",
            "program_id": "source-mismatch",
            "source": {"observation_seq": 7, "binding_revision": 3,
                "target_generations": {"fixture": GEN_A}},
            "authority": {"lease_id": "source-mismatch",
                "expires_at_ns": self.clock() + 4_000_000_000},
            "terminal": {"release_all_required": True},
            "ops": [{"op": "focus", "target": "fixture"},
                {"op": "key_chord", "keys": ["CTRL"]},
                {"op": "release_all"}]}

        for observation_seq, binding_revision in ((6, 3), (7, 2)):
            with self.subTest(observation_seq=observation_seq,
                              binding_revision=binding_revision):
                with self.assertRaisesRegex(ValueError,
                        "STANDARD_SOURCE_BINDING_MISMATCH"):
                    self.session.admit_standard_action(CALL_ID, ACTION_ID,
                        binding["target_binding_id"], program,
                        operation_deadline_ns=self.clock() + 5_000_000_000,
                        current_observation_seq=observation_seq,
                        current_binding_revision=binding_revision)
        self.assertEqual(self.owner._records, {})

    def test_cancel_during_producer_factory_never_opens_the_child_start_gate(self):
        import threading
        self.session.bind_target_generation_reader(lambda: GEN_A)
        self.session.admit_action(CALL_ID, ACTION_ID, GEN_A,
            operation_deadline_ns=self.clock() + 5_000_000_000,
            obligations=["key:a"])
        factory_entered, factory_release = threading.Event(), threading.Event()
        start_gate = threading.Event()

        class GatedProcess(FakeProcess):
            def start(self):
                self.alive = True

        process = GatedProcess(4201)
        identity = {"pid": process.pid, "creation_time_100ns": 9201}
        self.owner._process_identity_reader = lambda handle: identity if handle is process else None
        failures = []
        def factory(_action):
            factory_entered.set()
            self.assertTrue(factory_release.wait(2))
            return process, identity, start_gate.set

        def start():
            try:
                self.session.start_producer(CALL_ID, factory)
            except BaseException as error:
                failures.append(error)
        worker = threading.Thread(target=start, daemon=True)
        worker.start()
        self.assertTrue(factory_entered.wait(1))
        canceled = self.session.cancel_guarded(CALL_ID,
            cancellation_operation_id="3" * 32,
            cleanup_deadline_ns=self.clock() + 2_000_000_000)
        self.assertEqual(canceled["status"], "pending")
        factory_release.set()
        worker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertEqual(failures, [])
        self.assertFalse(start_gate.is_set())
        self.assertEqual(self.owner.result(ACTION_ID)["phase"], "cancel_pending")

    def test_cancel_during_generation_recheck_keeps_child_gated_without_waiting_for_reader(self):
        import threading
        from runtime.cli_v1.test_mcp_win32_composition import GatedSyntheticProcess

        entered, release, authorized = threading.Event(), threading.Event(), threading.Event()
        reads = []

        def generation():
            reads.append(1)
            if len(reads) == 2:
                entered.set()
                if not release.wait(2):
                    raise TimeoutError("test generation read deadline")
            return GEN_A

        self.session.bind_target_generation_reader(generation)
        self.session.admit_action(CALL_ID, ACTION_ID, GEN_A,
            operation_deadline_ns=self.clock() + 5_000_000_000, obligations=["key:a"])
        process = GatedSyntheticProcess(4201)
        identity = {"pid": 4201, "creation_time_100ns": 9201}
        self.owner._process_identity_reader = lambda handle: identity if handle is process else None
        failures = []

        def start():
            try:
                self.session.start_producer(CALL_ID, lambda _action:
                    (process, identity, authorized.set))
            except BaseException as error:
                failures.append(error)

        worker = threading.Thread(target=start, daemon=True)
        worker.start()
        try:
            self.assertTrue(entered.wait(1))
            before = time.monotonic()
            canceled = self.session.cancel_guarded(CALL_ID,
                cleanup_deadline_ns=self.clock() + 3_000_000_000)
            self.assertLess(time.monotonic() - before, 0.5)
            self.assertEqual(canceled["status"], "pending")
        finally:
            release.set()
            worker.join(3)
            process.terminate()
        self.assertFalse(worker.is_alive())
        self.assertEqual(failures, [])
        self.assertFalse(authorized.is_set())
        self.assertEqual(self.owner.result(ACTION_ID)["phase"], "cancel_pending")

    def test_independent_task_effect_receipt_stays_separate_from_cancel_result(self):
        self.start_action()
        self.assertTrue(self.session.begin_task_effect_verification(CALL_ID))
        receipt = {
            "call_id": CALL_ID,
            "operation_id": ACTION_ID,
            "target_generation": GEN_A,
            "oracle_id": "4" * 32,
            "outcome": "success",
            "observed_monotonic_ns": self.clock(),
            "evidence_ref": "synthetic-task-state:completed",
        }
        row = self.session.record_task_effect(CALL_ID, receipt)
        self.assertEqual(row["task_effect"]["task_success"], True)
        self.assertEqual(row["action"]["status"], "running")
        cancellation = self.session.cancel_guarded(CALL_ID,
            cancellation_operation_id="5" * 32,
            cleanup_deadline_ns=self.clock() + 3_000_000_000)
        self.assertIsNone(cancellation["task_success"])
        retained = self.session.interface_result(CALL_ID)
        self.assertTrue(retained["task_effect"]["task_success"])
        self.assertIsNone(retained["cancellation"]["task_success"])
        changed = dict(receipt, outcome="failure")
        with self.assertRaisesRegex(ValueError, "immutable"):
            self.session.record_task_effect(CALL_ID, changed)

    def _check_oracle_timing_endpoint(self, observed):
        from unittest.mock import patch
        self.start_action()
        receipt = {"call_id": CALL_ID, "operation_id": ACTION_ID,
                   "target_generation": GEN_A, "oracle_id": "9" * 32,
                   "outcome": "success", "observed_monotonic_ns": observed,
                   "evidence_ref": "synthetic-same-clock-state"}
        with patch("runtime.cli_v1.owned_win32_session.time.monotonic_ns",
                   side_effect=[100, 200]):
            self.assertTrue(self.session.begin_task_effect_verification(CALL_ID))
            row = self.session.record_task_effect(CALL_ID, receipt)
        self.assertTrue(row["task_effect"]["task_success"])
        self.assertEqual(row["task_effect"]["requested_monotonic_ns"], 100)
        self.assertEqual(row["task_effect"]["receipt_received_monotonic_ns"], 200)
        self.assertEqual(self.session.record_task_effect(CALL_ID, receipt), row)

    def test_oracle_observation_at_request_endpoint_is_valid(self):
        self._check_oracle_timing_endpoint(100)

    def test_oracle_observation_at_receive_endpoint_is_valid(self):
        self._check_oracle_timing_endpoint(200)

    def test_task_oracle_timeout_cannot_be_promoted_by_late_receipt(self):
        self.start_action()
        self.assertTrue(self.session.begin_task_effect_verification(CALL_ID))
        timed_out = self.session.fail_task_effect_verification(
            CALL_ID, "independent_task_oracle_response_timeout")
        receipt = {
            "call_id": CALL_ID,
            "operation_id": ACTION_ID,
            "target_generation": GEN_A,
            "oracle_id": "6" * 32,
            "outcome": "success",
            "observed_monotonic_ns": self.clock(),
            "evidence_ref": "synthetic-application-state:completed",
        }
        with self.assertRaisesRegex(ValueError, "immutable"):
            self.session.record_task_effect(CALL_ID, receipt)
        retained = self.session.interface_result(CALL_ID)
        self.assertEqual(timed_out["task_effect"]["status"], "unknown")
        self.assertEqual(retained["task_effect"]["status"], "unknown")
        self.assertIsNone(retained["task_effect"]["task_success"])

    def test_registered_public_cancel_callback_uses_the_same_retained_operation(self):
        self.start_action()
        server = FakeToolServer()
        register_guarded_tools(server, submit=lambda *args, **kwargs: None,
                               cancel=self.session.cancel_guarded)
        cancel_tool = server.tools["interface_guarded_cancel"]
        first = asyncio.run(cancel_tool(CALL_ID))
        second = asyncio.run(cancel_tool(CALL_ID))
        first_row = first
        second_row = second
        self.assertEqual(first_row["status"], "pending")
        self.assertEqual(first_row["operation_id"], second_row["operation_id"])
        self.assertEqual(first_row["cancellation"]["action_operation_id"], ACTION_ID)
        self.assertEqual(len(self.supervisor.calls), 1)

    def test_confirmed_neutrality_does_not_promote_the_action_or_task_success(self):
        self.start_action()
        self.session.cancel_guarded(CALL_ID, cancellation_operation_id="3" * 32,
            cleanup_deadline_ns=self.clock() + 3_000_000_000)
        self.process.alive = False
        self.process.exitcode = 0
        self.assertTrue(self.owner.producer_retired(ACTION_ID, GEN_A, self.process))
        recovery = self.owner.claim_recovery(ACTION_ID, GEN_A)
        self.assertTrue(self.owner.recovery_completed(ACTION_ID, GEN_A,
            recovery["recovery_id"], release_accepted=True,
            readback={"operation_id":ACTION_ID, "target_generation":GEN_A,
                      "recovery_id":recovery["recovery_id"], "neutral":True}))
        result = self.session.interface_result(CALL_ID)
        self.assertEqual(result["action"]["status"], "running")
        self.assertIsNone(result["action"]["result"])
        self.assertEqual(result["cancellation"]["status"], "recovered")
        self.assertTrue(result["cancellation"]["release_confirmed"])
        self.assertIsNone(result["cancellation"]["task_success"])
        self.assertFalse(result["cancellation"]["replay_allowed"])

    def test_orphan_recovery_is_generation_bound_and_keeps_source_action_unknown(self):
        recovery_receipt = {"status": "recovered", "release_confirmed": True,
            "operation_id": ACTION_ID, "target_generation": GEN_A,
            "recovery_id": "3" * 32, "readback": {"neutral": True}}
        supervisor = FakeCancellationSupervisor(self.owner)
        def recover_orphaned_input(operation_id, generation, recovery_id,
                                   deadline_ns, obligations):
            return {**recovery_receipt, "operation_id": operation_id,
                    "target_generation": generation,
                    "recovery_id": recovery_id}
        supervisor.recover_orphaned_input = Mock(
            side_effect=recover_orphaned_input)
        session = OwnedWin32SessionOwner(self.owner, supervisor,
                                         synthetic_only=False)
        session.bind_target_generation_reader(lambda: GEN_A)

        result = session.recover_orphaned_input(
            source_operation_id=ACTION_ID,
            source_target_generation=GEN_A,
            obligations=["key:map01:W"],
            source_custody_record=orphan_custody_record())

        self.assertEqual(result["recovery_status"], "recovered")
        self.assertEqual(result["source_action_status"], "unknown")
        self.assertIsNone(result["task_success"])
        self.assertFalse(result["replay_allowed"])
        self.assertTrue(result["next_action_requires_fresh_generation"])
        canonical = json.dumps(orphan_custody_record(), sort_keys=True,
            separators=(",", ":"), ensure_ascii=False,
            allow_nan=False).encode("utf-8")
        self.assertEqual(result["source_custody_canonical_sha256"],
                         hashlib.sha256(canonical).hexdigest())
        supervisor.recover_orphaned_input.assert_called_once()
        duplicate = session.recover_orphaned_input(
            source_operation_id=ACTION_ID,
            source_target_generation=GEN_A,
            obligations=["key:map01:W"],
            source_custody_record=orphan_custody_record())
        self.assertEqual(duplicate["reason"], "source_recovery_already_attempted")
        supervisor.recover_orphaned_input.assert_called_once()

    def test_orphan_recovery_accepts_known_dispatch_but_rejects_known_no_dispatch(self):
        for dispatched, expected in ((True, "recovered"), (False, "refused")):
            with self.subTest(input_dispatched=dispatched):
                supervisor = FakeCancellationSupervisor(self.owner)
                def recover_orphaned_input(operation_id, generation,
                                           recovery_id, deadline_ns, obligations):
                    return {"status": "recovered", "release_confirmed": True,
                        "operation_id": operation_id,
                        "target_generation": generation,
                        "recovery_id": recovery_id,
                        "readback": {"neutral": True}}
                supervisor.recover_orphaned_input = Mock(
                    side_effect=recover_orphaned_input)
                session = OwnedWin32SessionOwner(self.owner, supervisor,
                                                 synthetic_only=False)
                session.bind_target_generation_reader(lambda: GEN_A)
                record = orphan_custody_record()
                record["dispatch"]["input_dispatched"] = dispatched

                result = session.recover_orphaned_input(
                    source_operation_id=ACTION_ID,
                    source_target_generation=GEN_A,
                    obligations=["key:map01:W"],
                    source_custody_record=record)

                self.assertEqual(result["recovery_status"], expected)
                self.assertEqual(supervisor.recover_orphaned_input.called,
                                 dispatched)
                if dispatched:
                    self.assertEqual(result["source_action_status"], "unknown")
                    self.assertIsNone(result["task_success"])
                    self.assertFalse(result["replay_allowed"])

    def test_orphan_recovery_generation_mismatch_sends_no_release(self):
        supervisor = FakeCancellationSupervisor(self.owner)
        supervisor.recover_orphaned_input = Mock()
        session = OwnedWin32SessionOwner(self.owner, supervisor,
                                         synthetic_only=False)
        session.bind_target_generation_reader(lambda: GEN_B)

        result = session.recover_orphaned_input(
            source_operation_id=ACTION_ID,
            source_target_generation=GEN_A,
            obligations=["key:map01:W"],
            source_custody_record=orphan_custody_record())

        self.assertEqual(result["recovery_status"], "refused")
        self.assertEqual(result["reason"], "target_generation_mismatch")
        supervisor.recover_orphaned_input.assert_not_called()

    def test_inconsistent_orphan_record_refuses_before_release(self):
        supervisor = FakeCancellationSupervisor(self.owner)
        supervisor.recover_orphaned_input = Mock()
        session = OwnedWin32SessionOwner(self.owner, supervisor,
                                         synthetic_only=False)
        session.bind_target_generation_reader(lambda: GEN_A)
        record = orphan_custody_record()
        record["dispatch"]["release_confirmed"] = True

        result = session.recover_orphaned_input(
            source_operation_id=ACTION_ID,
            source_target_generation=GEN_A,
            obligations=["key:map01:W"],
            source_custody_record=record)

        self.assertEqual(result["reason"], "custody_record_mismatch")
        supervisor.recover_orphaned_input.assert_not_called()


if __name__ == "__main__":
    unittest.main()
