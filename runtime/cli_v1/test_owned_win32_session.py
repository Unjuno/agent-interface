"""Narrow caller journal tests for the opt-in Win32 operation owner."""
import copy
import asyncio
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


class FakeProcess:
    def __init__(self, pid):
        self.pid = pid
        self.exitcode = None
        self.alive = True

    def is_alive(self):
        return self.alive


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
        backend.process_identity = Mock(return_value={
            'pid': 51, 'creation_time_100ns': 7001})
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


if __name__ == "__main__":
    unittest.main()
