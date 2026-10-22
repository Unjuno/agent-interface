"""Narrow caller journal tests for the opt-in Win32 operation owner."""
import copy
import asyncio
import time
import unittest

from runtime.guarded_win32_v1.operation_owner import OperationOwner, OwnerRefused
from runtime.cli_v1.owned_win32_session import OwnedWin32SessionOwner
from runtime.cli_v1.mcp_guarded import register_guarded_tools


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

    def producer_started(self, operation_id, generation, process, *, process_identity):
        return self.owner.producer_started(operation_id, generation, process,
                                           process_identity=process_identity)

    def cancel(self, operation_id, generation, *, cleanup_deadline_ns):
        self.calls.append((operation_id, generation, cleanup_deadline_ns))
        self.owner.request_cancel(operation_id, generation,
                                  cleanup_deadline_ns=cleanup_deadline_ns)
        return self.owner.result(operation_id)


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
