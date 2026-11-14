import json
import time
import unittest
import asyncio
import threading
import sys
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import Mock, patch

from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.owned_win32_session import OwnedWin32SessionOwner
from runtime.cli_v1.supervised_win32_compiled import run_public_compiled
from runtime.guarded_win32_v1.operation_owner import OperationOwner
from runtime.guarded_win32_v1.process_cancellation import (
    OperationCancellationSupervisor,
)


GENERATION = "a" * 64


class FakeProcess:
    def __init__(self):
        self.pid = None
        self.exitcode = None
        self.alive = False

    def start(self):
        self.pid = 7101
        self.alive = True

    def is_alive(self):
        return self.alive

    def close(self):
        return None


class FakeSupervisor:
    def __init__(self, operation_owner):
        self.operation_owner = operation_owner
        self.closed = False

    def producer_started(self, operation_id, generation, process, *, process_identity):
        return self.operation_owner.producer_started(operation_id, generation,
            process, process_identity=process_identity)

    def cancel(self, operation_id, generation, *, cleanup_deadline_ns):
        self.operation_owner.request_cancel(operation_id, generation,
            cleanup_deadline_ns=cleanup_deadline_ns)
        return self.operation_owner.result(operation_id)

    def observe_completed(self, operation_id, generation, *,
                          producer_exit_confirmed_ns, deadline_ns):
        observed = time.monotonic_ns()
        return {"operation_id": operation_id,
            "target_generation": generation,
            "producer_exit_confirmed_ns": producer_exit_confirmed_ns,
            "observed_monotonic_ns": observed,
            "neutral": True}

    def close(self):
        self.closed = True


class FakeProducerFactory:
    def __init__(self, process, identity):
        self.process = process
        self.identity = identity
        self.started = 0

    def __call__(self, _action):
        self.started += 1
        def open_gate():
            self.process.alive = False
            self.process.exitcode = 0
        return self.process, lambda: self.identity, open_gate

    def read_result(self, process):
        if process is not self.process or process.is_alive():
            raise RuntimeError("producer has not exited")
        return {"result": {"status": "completed",
                "execution": {"emissions": 1}},
            "release_receipt": {"verified": True, "keys_down": [],
                "buttons_down": [], "keys_unknown": [], "buttons_unknown": []}}


class ExceptionReceiptProducerFactory(FakeProducerFactory):
    def read_result(self, process):
        if process is not self.process or process.is_alive():
            raise RuntimeError("producer has not exited")
        return {"result": {"status": "runtime_failed",
                "error_type": "RuntimeError",
                "detail": "controlled producer dispatch exception"},
            "release_receipt": {"verified": False, "keys_down": [],
                "buttons_down": [], "keys_unknown": ["producer_exception"],
                "buttons_unknown": []}}


class DelayedExceptionReceiptProducerFactory(ExceptionReceiptProducerFactory):
    def __init__(self, process, identity, delay_s):
        super().__init__(process, identity)
        self.delay_s = delay_s

    def read_result(self, process):
        time.sleep(self.delay_s)
        return super().read_result(process)


class AbruptExitProducerFactory(FakeProducerFactory):
    def __call__(self, _action):
        self.started += 1
        def exit_without_receipt():
            self.process.alive = False
            self.process.exitcode = 86
        return self.process, lambda: self.identity, exit_without_receipt

    def read_result(self, process):
        if process is not self.process or process.is_alive():
            raise RuntimeError("producer has not exited")
        raise EOFError("producer exited without a completion packet")


class HeldProducerFactory:
    def __init__(self, process, identity):
        self.process = process
        self.identity = identity
        self.started = threading.Event()
        self.program_actions_lower_bound = 0

    def __call__(self, _action):
        return self.process, lambda: self.identity, self.started.set

    def read_result(self, process):
        if process is not self.process or process.is_alive():
            raise RuntimeError("producer has not exited")
        raise AssertionError("a cancelled producer has no normal completion receipt")

    def read_program_actions_lower_bound(self, process):
        if process is not self.process:
            raise ValueError("unknown producer process")
        return self.program_actions_lower_bound


class RecoveringFakeSupervisor(FakeSupervisor):
    def __init__(self, operation_owner, process):
        super().__init__(operation_owner)
        self.process = process

    def cancel(self, operation_id, generation, *, cleanup_deadline_ns):
        self.operation_owner.request_cancel(operation_id, generation,
            cleanup_deadline_ns=cleanup_deadline_ns)
        if self.process.alive:
            self.process.alive = False
            self.process.exitcode = -15
        if not self.operation_owner.producer_retired(
                operation_id, generation, self.process):
            raise AssertionError("fake producer retirement was not accepted")
        recovery = self.operation_owner.claim_recovery(operation_id, generation)
        if recovery is None:
            raise AssertionError("fake recovery was not admitted")
        readback = {"operation_id": operation_id,
            "target_generation": generation,
            "recovery_id": recovery["recovery_id"], "neutral": True,
            "observed_monotonic_ns": time.monotonic_ns(),
            "key_button_states": [False], "unicode_event_units": 0}
        self.operation_owner.recovery_release_attempted(operation_id,
            generation, recovery["recovery_id"], [{
                "virtual_key": 0x57, "encoding": "scan_code",
                "status": "returned"}])
        if not self.operation_owner.recovery_completed(operation_id, generation,
                recovery["recovery_id"], release_accepted=True,
                readback=readback):
            raise AssertionError("fake recovery was not confirmed")
        return self.operation_owner.result(operation_id)


class DelayedRecoveringFakeSupervisor(RecoveringFakeSupervisor):
    """Model lease expiry returning before the recovery receipt is published."""
    def __init__(self, operation_owner, process, delay_s=0.05):
        super().__init__(operation_owner, process)
        self.delay_s = delay_s
        self.recovery_thread = None

    def cancel(self, operation_id, generation, *, cleanup_deadline_ns):
        self.operation_owner.request_cancel(operation_id, generation,
            cleanup_deadline_ns=cleanup_deadline_ns)
        self.process.alive = False
        self.process.exitcode = -15
        if not self.operation_owner.producer_retired(
                operation_id, generation, self.process):
            raise AssertionError("fake producer retirement was not accepted")
        recovery = self.operation_owner.claim_recovery(operation_id, generation)
        if recovery is None:
            raise AssertionError("fake recovery was not admitted")
        readback = {"operation_id": operation_id,
            "target_generation": generation,
            "recovery_id": recovery["recovery_id"], "neutral": True,
            "observed_monotonic_ns": time.monotonic_ns(),
            "key_button_states": [False], "unicode_event_units": 0}

        def finish_recovery():
            time.sleep(self.delay_s)
            if not self.operation_owner.recovery_completed(operation_id,
                    generation, recovery["recovery_id"],
                    release_accepted=True, readback=readback):
                raise AssertionError("delayed fake recovery was not confirmed")

        self.recovery_thread = threading.Thread(target=finish_recovery, daemon=True)
        self.recovery_thread.start()
        return self.operation_owner.result(operation_id)


class UnknownAfterCancelSupervisor(FakeSupervisor):
    def cancel(self, operation_id, generation, *, cleanup_deadline_ns):
        self.operation_owner.request_cancel(operation_id, generation,
            cleanup_deadline_ns=cleanup_deadline_ns)
        return self.operation_owner.mark_unknown(operation_id, generation,
            "test_cleanup_deadline_expired")


class MissingAttemptReceiptSupervisor(FakeSupervisor):
    def __init__(self, operation_owner, process):
        super().__init__(operation_owner)
        self.process = process

    def cancel(self, operation_id, generation, *, cleanup_deadline_ns):
        self.operation_owner.request_cancel(operation_id, generation,
            cleanup_deadline_ns=cleanup_deadline_ns)
        self.process.alive = False
        self.process.exitcode = -15
        if not self.operation_owner.producer_retired(
                operation_id, generation, self.process):
            raise AssertionError("fake producer retirement was not accepted")
        recovery = self.operation_owner.claim_recovery(operation_id, generation)
        if recovery is None:
            raise AssertionError("fake recovery was not admitted")

        supervisor = object.__new__(OperationCancellationSupervisor)
        supervisor._owner = self.operation_owner
        supervisor._clock_ns = time.monotonic_ns
        supervisor._invalidate_helper = lambda *_args: None
        supervisor._exchange_helper = lambda *_args: {
            "operation_id": operation_id,
            "target_generation": generation,
            "recovery_id": recovery["recovery_id"],
            "release_accepted": True}
        supervisor._run_recovery(operation_id, generation, recovery)
        return self.operation_owner.result(operation_id)


class SupervisedWin32MCPTests(unittest.IsolatedAsyncioTestCase):
    def make_components(self, generation=GENERATION):
        process = FakeProcess()
        identity = {"pid": 7101, "creation_time_100ns": 90101}
        op_owner = OperationOwner(clock_ns=time.monotonic_ns,
            process_identity_reader=lambda handle: identity if handle is process else None)
        supervisor = FakeSupervisor(op_owner)
        owner = OwnedWin32SessionOwner(op_owner, supervisor, synthetic_only=False)
        owner.bind_target_generation_reader(lambda: generation)
        producer = FakeProducerFactory(process, identity)
        return owner, producer, supervisor

    def make_server(self, root, owner, producer):
        return create_server({"fixture": 123}, root,
            session_mode="supervised-win32",
            _supervised_win32_owner_factory=lambda *_args: owner,
            _supervised_win32_producer_factory=lambda *_args: producer)

    def valid_program(self):
        return {"schema": "agent-interface/program-v1",
            "program_id": "public-standard-save",
            "source": {"observation_seq": 1, "binding_revision": 1,
                "target_generations": {"fixture": GENERATION}},
            "authority": {"lease_id": "public-standard-save-lease",
                "expires_at_ns": time.monotonic_ns() + 5_000_000_000},
            "terminal": {"release_all_required": True},
            "ops": [{"op": "focus", "target": "fixture"},
                {"op": "key_chord", "keys": ["CTRL", "S"]},
                {"op": "release_all"}]}

    async def test_public_orphan_recovery_tool_is_bounded_and_keeps_source_unknown(self):
        recovery_generation = "b" * 64
        owner, producer, supervisor = self.make_components(recovery_generation)
        requests = []
        def recover(operation_id, generation, recovery_id, deadline_ns,
                    obligations, *, recovery_target_generation=None):
            requests.append((operation_id, generation, recovery_id,
                             deadline_ns, obligations,
                             recovery_target_generation))
            return {"status": "recovered", "release_confirmed": True,
                "operation_id": operation_id, "target_generation": (recovery_target_generation
                    or generation),
                "source_target_generation": generation,
                "recovery_target_generation": (recovery_target_generation
                    or generation),
                "recovery_id": recovery_id,
                "readback": {"neutral": True}}
        supervisor.recover_orphaned_input = recover
        with TemporaryDirectory() as root:
            server = self.make_server(root, owner, producer)
            async with server.settings.lifespan(server):
                tools = await server.list_tools()
                self.assertIn("interface_recover_orphaned_input",
                              {tool.name for tool in tools})
                reply = await server.call_tool(
                    "interface_recover_orphaned_input", {
                        "source_operation_id": "2" * 32,
                        "source_target_generation": GENERATION,
                        "recovery_target_generation": recovery_generation,
                        "obligations": ["key:fixture:W"],
                        "source_custody_record": {
                            "classification": "UNKNOWN_RELEASE_UNCONFIRMED_STOPPED",
                            "operation_id": "2" * 32,
                            "target_generation": GENERATION,
                            "obligations": ["key:fixture:W"],
                            "do_not_replay": True,
                            "observed_producer_live": False,
                            "late_server_request_possible": False,
                            "dispatch": {"input_dispatched": None,
                                "release_confirmed": False,
                                "task_success": None,
                                "replay_allowed": False}}})
                public_report = json.loads(reply.content[0].text)
                row = public_report
                self.assertNotIn("image_status", row)
                self.assertNotIn("image_error", row)
                self.assertEqual(row.get("status"), "recovered", row)
                self.assertEqual(row.get("recovery_status"), "recovered", row)
                self.assertEqual(row["source_action_status"], "unknown")
                self.assertTrue(row["release_confirmed"])
                self.assertIsNone(row["task_success"])
                self.assertFalse(row["replay_allowed"])
                self.assertEqual(len(requests), 1)
                self.assertEqual(requests[0][0], "2" * 32)
                self.assertEqual(requests[0][4], ["key:fixture:W"])
                self.assertEqual(requests[0][1], GENERATION)
                self.assertEqual(requests[0][5], recovery_generation)
                self.assertLessEqual(requests[0][3] - time.monotonic_ns(),
                                     5_000_000_000)
                refused = self.row(await server.call_tool(
                    "interface_dispatch", {
                        "program": self.valid_program(),
                        "current_observation_seq": 1,
                        "current_binding_revision": 1,
                        "wait_for_result_ms": 5000}))
                self.assertEqual(refused.get("status"), "invalid_request",
                                 refused)
                self.assertEqual(refused.get("error"),
                                 "TARGET_GENERATION_CHANGED")
                self.assertFalse(refused.get("operation_invoked"))
                self.assertFalse(refused.get("input_dispatched"))
                self.assertEqual(producer.started, 0)

    async def test_public_orphan_recovery_refusal_is_an_mcp_error(self):
        owner, producer, _supervisor = self.make_components()
        with TemporaryDirectory() as root:
            server = self.make_server(root, owner, producer)
            async with server.settings.lifespan(server):
                reply = await server.call_tool(
                    "interface_recover_orphaned_input", {
                        "source_operation_id": "2" * 32,
                        "source_target_generation": GENERATION,
                        "recovery_target_generation": GENERATION,
                        "obligations": ["key:fixture:W"],
                        "source_custody_record": {}})
                refusal = json.loads(reply.content[0].text)
                self.assertEqual(refusal.get("status"), "refused", refusal)
                self.assertFalse(refusal.get("release_confirmed"), refusal)
                self.assertIsNone(refusal.get("task_success"), refusal)
                self.assertFalse(refusal.get("replay_allowed"), refusal)
                self.assertTrue(reply.isError)
                self.assertEqual(producer.started, 0)

    async def test_public_orphan_recovery_unknown_is_an_mcp_error(self):
        owner, producer, supervisor = self.make_components()
        def unknown_receipt(operation_id, source_generation, recovery_id,
                            _deadline_ns, _obligations, *,
                            recovery_target_generation=None):
            recovery_generation = (recovery_target_generation
                or source_generation)
            return {"status": "unknown",
                "reason": "late_input_horizon_unconfirmed",
                "error_type": "OSError", "operation_id": operation_id,
                "target_generation": source_generation,
                "source_target_generation": source_generation,
                "recovery_target_generation": recovery_generation,
                "recovery_id": recovery_id, "release_confirmed": False,
                "release_receipt": {"release_accepted": True},
                "readback": {"neutral": True,
                    "observed_monotonic_ns": 123456789},
                "late_input_horizon_ns": 2_000_000_000,
                "late_input_observation_count": 1,
                "late_input_release_received_monotonic_ns": 123456700,
                "late_input_observation_start_monotonic_ns": 123456789,
                "late_input_observation_end_monotonic_ns": 123456789,
                "late_input_max_observed_gap_ns": 89,
                "late_input_max_sample_gap_ns": 100_000_000}
        supervisor.recover_orphaned_input = Mock(side_effect=unknown_receipt)
        with TemporaryDirectory() as root:
            server = self.make_server(root, owner, producer)
            async with server.settings.lifespan(server):
                reply = await server.call_tool(
                    "interface_recover_orphaned_input", {
                        "source_operation_id": "2" * 32,
                        "source_target_generation": GENERATION,
                        "recovery_target_generation": GENERATION,
                        "obligations": ["key:fixture:W"],
                        "source_custody_record": {
                            "classification": "UNKNOWN_RELEASE_UNCONFIRMED_STOPPED",
                            "operation_id": "2" * 32,
                            "target_generation": GENERATION,
                            "obligations": ["key:fixture:W"],
                            "do_not_replay": True,
                            "observed_producer_live": False,
                            "late_server_request_possible": False,
                            "dispatch": {"input_dispatched": None,
                                "release_confirmed": False,
                                "task_success": None,
                                "replay_allowed": False}}})
                result = json.loads(reply.content[0].text)
                self.assertEqual(result.get("status"), "unknown", result)
                self.assertFalse(result.get("release_confirmed"), result)
                self.assertIsNone(result.get("task_success"), result)
                self.assertFalse(result.get("replay_allowed"), result)
                nested = result.get("recovery_receipt")
                self.assertEqual(nested.get("reason"),
                    "late_input_horizon_unconfirmed")
                self.assertEqual(nested.get("error_type"), "OSError")
                self.assertEqual(nested.get("operation_id"), "2" * 32)
                self.assertEqual(nested.get("source_target_generation"), GENERATION)
                self.assertEqual(nested.get("recovery_target_generation"), GENERATION)
                self.assertEqual(nested.get("late_input_observation_count"), 1)
                self.assertEqual(nested.get("readback", {}).get(
                    "observed_monotonic_ns"), 123456789)
                self.assertTrue(reply.isError)
                self.assertEqual(supervisor.recover_orphaned_input.call_count, 1)
                self.assertEqual(producer.started, 0)

    @staticmethod
    def row(reply):
        row = json.loads(reply.content[0].text)
        receipt = row.get("receipt")
        if isinstance(receipt, dict):
            source = receipt.get("source")
            if isinstance(source, dict) and isinstance(source.get("raw_report"), dict):
                return source["raw_report"]
        return row

    async def test_standard_interface_dispatch_completes_with_separate_readback(self):
        owner, producer, supervisor = self.make_components()
        with TemporaryDirectory() as root:
            server = self.make_server(root, owner, producer)
            reply = await server.call_tool("interface_dispatch", {
                "program": self.valid_program(),
                "current_observation_seq": 1,
                "current_binding_revision": 1,
                "wait_for_result_ms": 5000})
            result = self.row(reply)
            self.assertEqual(result.get("status"), "returned", result)
            self.assertTrue(result["release_confirmed"])
            self.assertTrue(result["input_dispatched"])
            self.assertIsNone(result["task_success"])
            self.assertFalse(result["replay_allowed"])
            self.assertTrue(result["supervision"]["action"]["completion_custody"]["release_confirmed"])
            retrieved = self.row(await server.call_tool("interface_results", {
                "call_id": result["call_id"]}))
            self.assertEqual(retrieved["action"]["status"], "completed")
            self.assertTrue(retrieved["action"]["release_confirmed"])
            self.assertIsNone(retrieved["task_success"])
            close = self.row(await server.call_tool("interface_close", {}))
            self.assertEqual(close["status"], "closed")
            self.assertFalse(close["release_confirmed"])
            self.assertTrue(retrieved["action"]["release_confirmed"])
        self.assertTrue(supervisor.closed)

    async def test_abrupt_standard_producer_exit_automatically_recovers_without_rewriting_action(self):
        process = FakeProcess()
        identity = {"pid": 7101, "creation_time_100ns": 90101}
        operation_owner = OperationOwner(clock_ns=time.monotonic_ns,
            process_identity_reader=lambda handle: identity
            if handle is process else None)
        supervisor = RecoveringFakeSupervisor(operation_owner, process)
        owner = OwnedWin32SessionOwner(operation_owner, supervisor,
            synthetic_only=False)
        owner.bind_target_generation_reader(lambda: GENERATION)
        producer = AbruptExitProducerFactory(process, identity)
        with TemporaryDirectory() as root:
            server = self.make_server(root, owner, producer)
            result = self.row(await server.call_tool("interface_dispatch", {
                "program": self.valid_program(),
                "current_observation_seq": 1,
                "current_binding_revision": 1,
                "wait_for_result_ms": 5000}))
            self.assertEqual(result["status"], "returned", result)
            self.assertEqual(result["result"]["status"], "unknown")
            self.assertIsNone(result["input_dispatched"])
            self.assertTrue(result["release_confirmed"])
            self.assertIsNone(result["task_success"])
            self.assertFalse(result["replay_allowed"])
            action = result["supervision"]["action"]
            cancellation = result["supervision"]["cancellation"]
            self.assertEqual(action["status"], "unknown")
            self.assertFalse(action["release_confirmed"], result)
            self.assertIsNone(action["task_success"])
            self.assertFalse(action["replay_allowed"])
            self.assertTrue(cancellation["automatic_completion_recovery"])
            self.assertEqual(cancellation["status"], "recovered")
            self.assertTrue(cancellation["release_confirmed"])
            self.assertEqual(process.exitcode, 86)
            await server.call_tool("interface_close", {})

    async def test_public_dispatch_exception_auto_recovers_and_preserves_unknown_action(self):
        process = FakeProcess()
        identity = {"pid": 7101, "creation_time_100ns": 90101}
        operation_owner = OperationOwner(clock_ns=time.monotonic_ns,
            process_identity_reader=lambda handle: identity
            if handle is process else None)
        supervisor = RecoveringFakeSupervisor(operation_owner, process)
        owner = OwnedWin32SessionOwner(operation_owner, supervisor,
            synthetic_only=False)
        owner.bind_target_generation_reader(lambda: GENERATION)
        producer = ExceptionReceiptProducerFactory(process, identity)
        with TemporaryDirectory() as root:
            server = self.make_server(root, owner, producer)
            result = self.row(await server.call_tool("interface_dispatch", {
                "program": self.valid_program(),
                "current_observation_seq": 1,
                "current_binding_revision": 1,
                "wait_for_result_ms": 5000}))
            self.assertEqual(result["status"], "returned", result)
            self.assertEqual(result["result"]["status"], "unknown")
            self.assertIsNone(result["input_dispatched"])
            self.assertTrue(result["release_confirmed"])
            self.assertIsNone(result["task_success"])
            self.assertFalse(result["replay_allowed"])
            action = result["supervision"]["action"]
            cancellation = result["supervision"]["cancellation"]
            self.assertEqual(action["status"], "unknown")
            self.assertFalse(action["release_confirmed"])
            self.assertEqual(action["result"]["error"],
                             "COMPLETION_EVIDENCE_UNCONFIRMED")
            self.assertEqual(cancellation["status"], "recovered")
            self.assertTrue(cancellation["automatic_completion_recovery"])
            self.assertTrue(cancellation["release_confirmed"])
            self.assertIsNone(action["task_success"])
            self.assertFalse(action["replay_allowed"])
            await server.call_tool("interface_close", {})

    async def test_failed_automatic_exception_recovery_allows_fresh_generation_recovery(self):
        from runtime.guarded_win32_v1.input_obligations import derive_input_obligations

        process = FakeProcess()
        identity = {"pid": 7101, "creation_time_100ns": 90101}
        operation_owner = OperationOwner(clock_ns=time.monotonic_ns,
            process_identity_reader=lambda handle: identity
            if handle is process else None)
        supervisor = UnknownAfterCancelSupervisor(operation_owner)
        owner = OwnedWin32SessionOwner(operation_owner, supervisor,
            synthetic_only=False)
        owner.bind_target_generation_reader(lambda: GENERATION)
        producer = ExceptionReceiptProducerFactory(process, identity)
        recovery_generation = "b" * 64
        program = self.valid_program()
        obligations = derive_input_obligations(program)

        with TemporaryDirectory() as root, TemporaryDirectory() as fresh_root:
            server = self.make_server(root, owner, producer)
            result = self.row(await server.call_tool("interface_dispatch", {
                "program": program,
                "current_observation_seq": 1,
                "current_binding_revision": 1,
                "wait_for_result_ms": 5000}))
            self.assertEqual(result["result"]["status"], "unknown")
            self.assertFalse(result["release_confirmed"])
            self.assertIsNone(result["task_success"])
            self.assertFalse(result["replay_allowed"])
            action = result["supervision"]["action"]
            cancellation = result["supervision"]["cancellation"]
            self.assertEqual(action["status"], "unknown")
            self.assertEqual(cancellation["status"], "unknown")
            self.assertTrue(cancellation["automatic_completion_recovery"])
            self.assertFalse(cancellation["release_confirmed"])
            self.assertIsNone(action["task_success"])
            self.assertFalse(action["replay_allowed"])
            close = self.row(await server.call_tool("interface_close", {}))
            self.assertEqual(close["status"], "busy")

            fresh_owner, fresh_producer, fresh_supervisor = self.make_components(
                recovery_generation)
            recovery_calls = []
            def recover(operation_id, source_generation, recovery_id,
                        deadline_ns, input_obligations, *,
                        recovery_target_generation=None):
                recovery_calls.append((operation_id, source_generation,
                    recovery_id, deadline_ns, list(input_obligations),
                    recovery_target_generation))
                return {"status": "recovered", "release_confirmed": True,
                    "operation_id": operation_id,
                    "target_generation": recovery_target_generation,
                    "source_target_generation": source_generation,
                    "recovery_target_generation": recovery_target_generation,
                    "recovery_id": recovery_id,
                    "readback": {"neutral": True},
                    "late_input_horizon_verified": True,
                    "late_input_horizon_ns": 2_000_000_000,
                    "late_input_release_received_monotonic_ns": 100,
                    "late_input_observation_start_monotonic_ns": 100,
                    "late_input_observation_end_monotonic_ns": 2_000_000_100,
                    "late_input_observation_count": 3,
                    "late_input_max_observed_gap_ns": 1_000_000,
                    "late_input_max_sample_gap_ns": 100_000_000}
            fresh_supervisor.recover_orphaned_input = recover
            fresh_server = self.make_server(
                fresh_root, fresh_owner, fresh_producer)
            source_custody_record = {
                "classification": "UNKNOWN_RELEASE_UNCONFIRMED_STOPPED",
                "operation_id": action["operation_id"],
                "target_generation": action["target_generation"],
                "obligations": obligations,
                "do_not_replay": True,
                "observed_producer_live": False,
                "late_server_request_possible": True,
                "dispatch": {"input_dispatched": None,
                    "release_confirmed": False, "task_success": None,
                    "replay_allowed": False}}
            reply = await fresh_server.call_tool(
                "interface_recover_orphaned_input", {
                    "source_operation_id": action["operation_id"],
                    "source_target_generation": action["target_generation"],
                    "recovery_target_generation": recovery_generation,
                    "obligations": obligations,
                    "source_custody_record": source_custody_record})
            recovered = self.row(reply)
            self.assertEqual(recovered["status"], "recovered", recovered)
            self.assertEqual(recovered["source_action_status"], "unknown")
            self.assertTrue(recovered["release_confirmed"])
            self.assertTrue(recovered["recovery_receipt"][
                "late_input_horizon_verified"])
            self.assertEqual(recovered["recovery_receipt"][
                "late_input_horizon_ns"], 2_000_000_000)
            self.assertIsNone(recovered["task_success"])
            self.assertFalse(recovered["replay_allowed"])
            self.assertTrue(recovered["next_action_requires_fresh_generation"])
            self.assertEqual(len(recovery_calls), 1)
            self.assertEqual(recovery_calls[0][0], action["operation_id"])
            self.assertEqual(recovery_calls[0][1], action["target_generation"])
            self.assertEqual(recovery_calls[0][4], obligations)
            self.assertEqual(recovery_calls[0][5], recovery_generation)

            original = self.row(await server.call_tool("interface_results", {
                "call_id": result["call_id"]}))
            self.assertEqual(original["action"]["status"], "unknown")
            self.assertFalse(original["action"]["release_confirmed"])
            self.assertIsNone(original["task_success"])
            self.assertFalse(original["replay_allowed"])

    async def test_public_dispatch_keeps_child_release_unconfirmed_without_observer_readback(self):
        process = FakeProcess()
        identity = {"pid": 7101, "creation_time_100ns": 90101}
        operation_owner = OperationOwner(clock_ns=time.monotonic_ns,
            process_identity_reader=lambda handle: identity
            if handle is process else None)
        supervisor = RecoveringFakeSupervisor(operation_owner, process)
        owner = OwnedWin32SessionOwner(operation_owner, supervisor,
            synthetic_only=False)
        owner.bind_target_generation_reader(lambda: GENERATION)
        producer = FakeProducerFactory(process, identity)
        supervisor.observe_completed = lambda *_args, **_kwargs: None
        with TemporaryDirectory() as root:
            server = self.make_server(root, owner, producer)
            reply = await server.call_tool("interface_dispatch", {
                "program": self.valid_program(),
                "current_observation_seq": 1,
                "current_binding_revision": 1,
                "wait_for_result_ms": 5000})
            result = self.row(reply)
            self.assertEqual(result.get("status"), "returned", result)
            action = result["supervision"]["action"]
            self.assertEqual(action["status"], "unknown")
            self.assertEqual(action["result"]["status"], "unknown")
            self.assertTrue(result["release_confirmed"])
            self.assertFalse(action["release_confirmed"])
            self.assertEqual(result["supervision"]["cancellation"]["status"],
                             "recovered")
            self.assertTrue(result["supervision"]["cancellation"][
                "automatic_completion_recovery"])
            self.assertIsNone(result["task_success"])
            self.assertFalse(result["replay_allowed"])
            close = self.row(await server.call_tool("interface_close", {}))
            self.assertEqual(close["status"], "closed")
        self.assertTrue(supervisor.closed)

    async def test_completion_observer_unknown_still_enters_bounded_recovery(self):
        process = FakeProcess()
        identity = {"pid": 7101, "creation_time_100ns": 90101}
        operation_owner = OperationOwner(clock_ns=time.monotonic_ns,
            process_identity_reader=lambda handle: identity
            if handle is process else None)
        supervisor = RecoveringFakeSupervisor(operation_owner, process)
        owner = OwnedWin32SessionOwner(operation_owner, supervisor,
            synthetic_only=False)
        owner.bind_target_generation_reader(lambda: GENERATION)
        producer = FakeProducerFactory(process, identity)

        def observer_marks_unknown(operation_id, generation, **_kwargs):
            operation_owner.mark_unknown(operation_id, generation,
                "normal_completion_observer_unconfirmed: RuntimeError")
            return None

        supervisor.observe_completed = observer_marks_unknown
        with TemporaryDirectory() as root:
            server = self.make_server(root, owner, producer)
            result = self.row(await server.call_tool("interface_dispatch", {
                "program": self.valid_program(),
                "current_observation_seq": 1,
                "current_binding_revision": 1,
                "wait_for_result_ms": 5000}))
            action = result["supervision"]["action"]
            cancellation = result["supervision"]["cancellation"]
            self.assertEqual(action["status"], "unknown", result)
            self.assertFalse(action["release_confirmed"], result)
            self.assertIsNone(action["task_success"])
            self.assertFalse(action["replay_allowed"])
            self.assertTrue(cancellation["automatic_completion_recovery"])
            self.assertEqual(cancellation["status"], "recovered", result)
            self.assertTrue(cancellation["release_confirmed"], result)
            self.assertEqual(result["status"], "returned")
            await server.call_tool("interface_close", {})

    async def test_async_completion_recovery_does_not_upgrade_unknown_action_after_expiry(self):
        process = FakeProcess()
        identity = {"pid": 7101, "creation_time_100ns": 90101}
        operation_owner = OperationOwner(clock_ns=time.monotonic_ns,
            process_identity_reader=lambda handle: identity
            if handle is process else None)
        supervisor = DelayedRecoveringFakeSupervisor(operation_owner, process,
            delay_s=0.25)
        owner = OwnedWin32SessionOwner(operation_owner, supervisor,
            synthetic_only=False)
        owner.bind_target_generation_reader(lambda: GENERATION)
        producer = DelayedExceptionReceiptProducerFactory(process, identity,
            delay_s=0.7)
        with TemporaryDirectory() as root:
            server = self.make_server(root, owner, producer)
            program = self.valid_program()
            program["authority"]["expires_at_ns"] = time.monotonic_ns() + 500_000_000
            pending = self.row(await server.call_tool("interface_dispatch", {
                "program": program,
                "current_observation_seq": 1,
                "current_binding_revision": 1,
                "wait_for_result_ms": 0}))
            self.assertEqual(pending["status"], "pending", pending)
            deadline = time.monotonic() + 3
            retained = None
            while time.monotonic() < deadline:
                retained = self.row(await server.call_tool("interface_results", {
                    "call_id": pending["call_id"]}))
                cancellation = retained.get("cancellation")
                if (isinstance(cancellation, dict)
                        and cancellation.get("status") == "recovered"):
                    break
                await asyncio.sleep(0.01)
            self.assertIsNotNone(retained)
            self.assertIn("cancellation", retained, retained)
            self.assertEqual(retained["cancellation"]["status"], "recovered",
                retained)
            self.assertTrue(retained["cancellation"]["release_confirmed"])
            self.assertEqual(retained["action"]["status"], "unknown", retained)
            self.assertFalse(retained["action"]["release_confirmed"], retained)
            self.assertEqual(retained["action"]["result"]["status"], "unknown")
            self.assertIsNone(retained["action"]["task_success"])
            self.assertFalse(retained["replay_allowed"])
            await server.call_tool("interface_close", {})

    async def test_task_oracle_is_not_invoked_for_unknown_public_custody(self):
        process = FakeProcess()
        identity = {"pid": 7101, "creation_time_100ns": 90101}
        operation_owner = OperationOwner(clock_ns=time.monotonic_ns,
            process_identity_reader=lambda handle: identity
            if handle is process else None)
        supervisor = RecoveringFakeSupervisor(operation_owner, process)
        owner = OwnedWin32SessionOwner(operation_owner, supervisor,
            synthetic_only=False)
        owner.bind_target_generation_reader(lambda: GENERATION)
        producer = FakeProducerFactory(process, identity)

        def non_neutral_readback(operation_id, generation, *,
                                 producer_exit_confirmed_ns, deadline_ns):
            return {"operation_id": operation_id,
                "target_generation": generation,
                "producer_exit_confirmed_ns": producer_exit_confirmed_ns,
                "observed_monotonic_ns": time.monotonic_ns(),
                "neutral": False}

        supervisor.observe_completed = non_neutral_readback
        oracle_calls = []

        def oracle(action):
            oracle_calls.append(action["call_id"])
            return {
                "call_id": action["call_id"],
                "operation_id": action["operation_id"],
                "target_generation": action["target_generation"],
                "oracle_id": "c" * 32,
                "outcome": "success",
                "observed_monotonic_ns": time.monotonic_ns(),
                "evidence_ref": "fixture-oracle:must-not-run",
            }

        with TemporaryDirectory() as root:
            server = create_server({"fixture": 123}, root,
                session_mode="supervised-win32",
                _supervised_win32_owner_factory=lambda *_args: owner,
                _supervised_win32_producer_factory=lambda *_args: producer,
                supervised_win32_task_oracle=oracle)
            dispatched = self.row(await server.call_tool("interface_dispatch", {
                "program": self.valid_program(),
                "current_observation_seq": 1,
                "current_binding_revision": 1,
                "wait_for_result_ms": 5000}))
            verified = json.loads((await server.call_tool("interface_verify_task", {
                "call_id": dispatched["call_id"],
                "wait_for_result_ms": 1000})).content[0].text)
            self.assertEqual(verified["status"], "unknown", verified)
            action = dispatched["supervision"]["action"]
            self.assertEqual(action["status"], "unknown")
            self.assertFalse(action["release_confirmed"])
            self.assertEqual(dispatched["supervision"]["cancellation"]["status"],
                             "recovered")
            self.assertTrue(dispatched["release_confirmed"])
            self.assertIsNone(verified["task_success"])
            self.assertFalse(verified["replay_allowed"])
            self.assertEqual(oracle_calls, [])
            close = self.row(await server.call_tool("interface_close", {}))
            self.assertEqual(close["status"], "closed")
        self.assertTrue(supervisor.closed)

    async def test_supervised_task_oracle_certifies_exact_completed_action_once(self):
        owner, producer, _ = self.make_components()
        oracle_calls = []

        def oracle(action):
            oracle_calls.append(dict(action))
            return {
                "call_id": action["call_id"],
                "operation_id": action["operation_id"],
                "target_generation": action["target_generation"],
                "oracle_id": "b" * 32,
                "outcome": "success",
                "observed_monotonic_ns": time.monotonic_ns(),
                "evidence_ref": "fixture-oracle:save-receipt:sha256:" + "c" * 64,
            }

        with TemporaryDirectory() as root:
            server = create_server({"fixture": 123}, root,
                session_mode="supervised-win32",
                _supervised_win32_owner_factory=lambda *_args: owner,
                _supervised_win32_producer_factory=lambda *_args: producer,
                supervised_win32_task_oracle=oracle)
            dispatched = self.row(await server.call_tool("interface_dispatch", {
                "program": self.valid_program(),
                "current_observation_seq": 1,
                "current_binding_revision": 1,
                "wait_for_result_ms": 5000}))
            self.assertEqual(dispatched.get("status"), "returned", dispatched)
            verified = json.loads((await server.call_tool("interface_verify_task", {
                "call_id": dispatched["call_id"],
                "wait_for_result_ms": 1000})).content[0].text)
            self.assertEqual(verified["status"], "verified", verified)
            self.assertTrue(verified["task_success"])
            self.assertFalse(verified["operation_invoked"])
            self.assertFalse(verified["input_dispatched"])
            self.assertFalse(verified["replay_allowed"])
            retained = self.row(await server.call_tool("interface_results", {
                "call_id": dispatched["call_id"]}))
            self.assertTrue(retained["task_success"], retained)
            self.assertEqual(retained["task_effect"]["receipt"]["evidence_ref"],
                "fixture-oracle:save-receipt:sha256:" + "c" * 64)
            repeated = json.loads((await server.call_tool("interface_verify_task", {
                "call_id": dispatched["call_id"],
                "wait_for_result_ms": 1000})).content[0].text)
            self.assertEqual(repeated["status"], "verified", repeated)
            self.assertEqual(len(oracle_calls), 1)
            self.assertEqual(oracle_calls[0]["call_id"], dispatched["call_id"])
            self.assertEqual(oracle_calls[0]["target_generation"], GENERATION)
            await server.call_tool("interface_close", {})

    async def test_supervised_task_oracle_rejects_wrong_generation_without_retry(self):
        owner, producer, _ = self.make_components()
        oracle_calls = []

        def oracle(action):
            oracle_calls.append(action["call_id"])
            return {
                "call_id": action["call_id"],
                "operation_id": action["operation_id"],
                "target_generation": "d" * 64,
                "oracle_id": "e" * 32,
                "outcome": "success",
                "observed_monotonic_ns": time.monotonic_ns(),
                "evidence_ref": "fixture-oracle:wrong-generation",
            }

        with TemporaryDirectory() as root:
            server = create_server({"fixture": 123}, root,
                session_mode="supervised-win32",
                _supervised_win32_owner_factory=lambda *_args: owner,
                _supervised_win32_producer_factory=lambda *_args: producer,
                supervised_win32_task_oracle=oracle)
            dispatched = self.row(await server.call_tool("interface_dispatch", {
                "program": self.valid_program(),
                "current_observation_seq": 1,
                "current_binding_revision": 1,
                "wait_for_result_ms": 5000}))
            failed = json.loads((await server.call_tool("interface_verify_task", {
                "call_id": dispatched["call_id"],
                "wait_for_result_ms": 1000})).content[0].text)
            self.assertEqual(failed["status"], "unknown", failed)
            self.assertIsNone(failed["task_success"])
            self.assertFalse(failed["replay_allowed"])
            self.assertIn("different action generation",
                failed["task_effect"]["uncertainty"])
            repeated = json.loads((await server.call_tool("interface_verify_task", {
                "call_id": dispatched["call_id"],
                "wait_for_result_ms": 1000})).content[0].text)
            self.assertEqual(repeated["status"], "unknown", repeated)
            self.assertEqual(oracle_calls, [dispatched["call_id"]])
            await server.call_tool("interface_close", {})

    async def test_supervised_task_oracle_timeout_is_unknown_and_cannot_be_retried(self):
        owner, producer, _ = self.make_components()
        oracle_started = threading.Event()
        release_oracle = threading.Event()
        oracle_calls = []

        def oracle(action):
            oracle_calls.append(action["call_id"])
            oracle_started.set()
            release_oracle.wait(2)
            return {
                "call_id": action["call_id"],
                "operation_id": action["operation_id"],
                "target_generation": action["target_generation"],
                "oracle_id": "f" * 32,
                "outcome": "success",
                "observed_monotonic_ns": time.monotonic_ns(),
                "evidence_ref": "fixture-oracle:late-result",
            }

        with TemporaryDirectory() as root:
            server = create_server({"fixture": 123}, root,
                session_mode="supervised-win32",
                _supervised_win32_owner_factory=lambda *_args: owner,
                _supervised_win32_producer_factory=lambda *_args: producer,
                supervised_win32_task_oracle=oracle)
            dispatched = self.row(await server.call_tool("interface_dispatch", {
                "program": self.valid_program(),
                "current_observation_seq": 1,
                "current_binding_revision": 1,
                "wait_for_result_ms": 5000}))
            timed_out = json.loads((await server.call_tool("interface_verify_task", {
                "call_id": dispatched["call_id"],
                "wait_for_result_ms": 0})).content[0].text)
            self.assertTrue(oracle_started.wait(1))
            self.assertEqual(timed_out["status"], "unknown", timed_out)
            self.assertIsNone(timed_out["task_success"])
            self.assertFalse(timed_out["replay_allowed"])
            release_oracle.set()
            await asyncio.sleep(0.05)
            repeated = json.loads((await server.call_tool("interface_verify_task", {
                "call_id": dispatched["call_id"],
                "wait_for_result_ms": 1000})).content[0].text)
            self.assertEqual(repeated["status"], "unknown", repeated)
            self.assertIsNone(repeated["task_success"])
            self.assertEqual(oracle_calls, [dispatched["call_id"]])
            await server.call_tool("interface_close", {})

    async def test_concurrent_supervised_task_oracle_requests_reserve_one_attempt(self):
        owner, producer, _ = self.make_components()
        oracle_started = threading.Event()
        release_oracle = threading.Event()
        oracle_calls = []

        def oracle(action):
            oracle_calls.append(action["call_id"])
            oracle_started.set()
            release_oracle.wait(2)
            return {
                "call_id": action["call_id"],
                "operation_id": action["operation_id"],
                "target_generation": action["target_generation"],
                "oracle_id": "a" * 32,
                "outcome": "success",
                "observed_monotonic_ns": time.monotonic_ns(),
                "evidence_ref": "fixture-oracle:concurrent-receipt",
            }

        with TemporaryDirectory() as root:
            server = create_server({"fixture": 123}, root,
                session_mode="supervised-win32",
                _supervised_win32_owner_factory=lambda *_args: owner,
                _supervised_win32_producer_factory=lambda *_args: producer,
                supervised_win32_task_oracle=oracle)
            dispatched = self.row(await server.call_tool("interface_dispatch", {
                "program": self.valid_program(),
                "current_observation_seq": 1,
                "current_binding_revision": 1,
                "wait_for_result_ms": 5000}))
            first = asyncio.create_task(server.call_tool("interface_verify_task", {
                "call_id": dispatched["call_id"], "wait_for_result_ms": 1000}))
            try:
                self.assertTrue(await asyncio.to_thread(oracle_started.wait, 1))
                second = json.loads((await server.call_tool("interface_verify_task", {
                    "call_id": dispatched["call_id"],
                    "wait_for_result_ms": 1000})).content[0].text)
                self.assertEqual(second["status"], "pending", second)
                self.assertEqual(oracle_calls, [dispatched["call_id"]])
                release_oracle.set()
                first_result = json.loads((await first).content[0].text)
                self.assertEqual(first_result["status"], "verified", first_result)
                self.assertTrue(first_result["task_success"])
                self.assertEqual(oracle_calls, [dispatched["call_id"]])
            finally:
                release_oracle.set()
                if not first.done():
                    await first
                await server.call_tool("interface_close", {})

    async def test_native_producer_directory_is_disjoint_from_public_call_receipts(self):
        owner, producer, _ = self.make_components()
        producer_roots = []

        def producer_factory(_targets, output_directory, *_args):
            producer_roots.append(Path(output_directory))
            return producer

        with TemporaryDirectory() as root:
            server = create_server({"fixture": 123}, root,
                session_mode="supervised-win32",
                _supervised_win32_owner_factory=lambda *_args: owner,
                _supervised_win32_producer_factory=producer_factory)
            result = self.row(await server.call_tool("interface_dispatch", {
                "program": self.valid_program(),
                "current_observation_seq": 1,
                "current_binding_revision": 1,
                "wait_for_result_ms": 5000}))
            call_directory = Path(root) / result["call_id"]
            producer_directory = producer_roots[0] / result["call_id"]
            self.assertTrue((call_directory / "report.json").exists())
            self.assertNotEqual(producer_directory, call_directory)
            await server.call_tool("interface_close", {})

    async def test_transport_shutdown_closes_supervised_owner_and_helpers(self):
        owner, producer, supervisor = self.make_components()
        with TemporaryDirectory() as root:
            server = self.make_server(root, owner, producer)
            async with server.settings.lifespan(server):
                self.assertEqual(owner.state, "open")
            self.assertEqual(owner.state, "closed")
            self.assertTrue(supervisor.closed)
            close_report = json.loads((Path(root) /
                f"session-{owner.session_id}-close.json").read_text(encoding="utf-8"))
            self.assertEqual(close_report["status"], "closed")

    async def test_dispatch_releases_public_operation_lock_after_recovered_cancel(self):
        process = FakeProcess()
        identity = {"pid": 7101, "creation_time_100ns": 90101}
        op_owner = OperationOwner(clock_ns=time.monotonic_ns,
            process_identity_reader=lambda handle: identity if handle is process else None)
        supervisor = RecoveringFakeSupervisor(op_owner, process)
        owner = OwnedWin32SessionOwner(op_owner, supervisor, synthetic_only=False)
        owner.bind_target_generation_reader(lambda: GENERATION)
        producer = HeldProducerFactory(process, identity)
        with TemporaryDirectory() as root:
            server = self.make_server(root, owner, producer)
            program = self.valid_program()
            # Leave room for Windows event-loop and worker startup scheduling;
            # the test measures cancellation drain, not a subsecond lease race.
            program["authority"]["expires_at_ns"] = time.monotonic_ns() + 5_000_000_000
            pending = self.row(await server.call_tool("interface_dispatch", {
                "program": program,
                "current_observation_seq": 1,
                "current_binding_revision": 1,
                "wait_for_result_ms": 0}))
            self.assertEqual(pending["status"], "pending")
            for _ in range(20):
                self.row(await server.call_tool("interface_results", {
                    "call_id": pending["call_id"]}))
                if producer.started.is_set():
                    break
                await asyncio.sleep(0.01)
            self.assertTrue(await asyncio.wait_for(
                asyncio.to_thread(producer.started.wait, 1), 1))

            cancelled = self.row(await server.call_tool("interface_cancel", {
                "call_id": pending["call_id"]}))
            self.assertEqual(cancelled["status"], "recovered")
            deadline = time.monotonic() + 2
            while True:
                retained = self.row(await server.call_tool("interface_results", {
                    "call_id": pending["call_id"]}))
                if (retained["action"]["status"] != "running"
                        and "program_actions_lower_bound" in retained["action"]):
                    break
                self.assertLess(time.monotonic(), deadline, retained)
                await asyncio.sleep(0.01)
            self.assertEqual(retained["cancellation"]["status"], "recovered")
            self.assertEqual(
                retained["action"]["program_actions_lower_bound"], 0)
            self.assertIsNone(retained["action"].get("input_dispatched"))

            close_statuses = []
            # Recovered cancellation ends input custody; the public dispatch
            # still has to persist and present its terminal receipt before the
            # serialized close can enter. Bound that full drain separately.
            deadline = time.monotonic() + 2
            try:
                while time.monotonic() < deadline:
                    closed = self.row(await server.call_tool("interface_close", {}))
                    close_statuses.append(closed.get("status"))
                    if closed.get("status") == "closed":
                        break
                    await asyncio.sleep(0.05)
                self.assertEqual(close_statuses[-1], "closed", close_statuses)
            finally:
                if owner.state != "closed":
                    await asyncio.sleep(0.55)
                    self.row(await server.call_tool("interface_close", {}))

    async def test_standard_recovered_cancel_then_fresh_generation_task_success(self):
        old_generation = "a" * 64
        new_generation = "b" * 64
        old_process = FakeProcess()
        identity = {"pid": 7101, "creation_time_100ns": 90101}
        old_owner = OperationOwner(clock_ns=time.monotonic_ns,
            process_identity_reader=lambda handle: identity if handle is old_process else None)
        old_supervisor = RecoveringFakeSupervisor(old_owner, old_process)
        old_session = OwnedWin32SessionOwner(old_owner, old_supervisor,
            synthetic_only=False)
        old_session.bind_target_generation_reader(lambda: old_generation)
        old_producer = HeldProducerFactory(old_process, identity)

        new_session, new_producer, _ = self.make_components(new_generation)
        oracle_calls = []

        def oracle(action):
            oracle_calls.append(dict(action))
            return {
                "call_id": action["call_id"],
                "operation_id": action["operation_id"],
                "target_generation": action["target_generation"],
                "oracle_id": "e" * 32,
                "outcome": "success",
                "observed_monotonic_ns": time.monotonic_ns(),
                "evidence_ref": "fixture-oracle:fresh-generation-save",
            }

        with TemporaryDirectory() as old_root, TemporaryDirectory() as new_root:
            old_server = self.make_server(old_root, old_session, old_producer)
            new_server = create_server({"fixture": 123}, new_root,
                session_mode="supervised-win32",
                _supervised_win32_owner_factory=lambda *_args: new_session,
                _supervised_win32_producer_factory=lambda *_args: new_producer,
                supervised_win32_task_oracle=oracle)
            try:
                old_program = self.valid_program()
                old_program["authority"]["expires_at_ns"] = time.monotonic_ns() + 5_000_000_000
                old_pending = self.row(await old_server.call_tool("interface_dispatch", {
                    "program": old_program,
                    "current_observation_seq": 1,
                    "current_binding_revision": 1,
                    "wait_for_result_ms": 0}))
                self.assertEqual(old_pending["status"], "pending", old_pending)
                self.assertTrue(await asyncio.wait_for(
                    asyncio.to_thread(old_producer.started.wait, 1), 1))

                old_cancel = self.row(await old_server.call_tool("interface_cancel", {
                    "call_id": old_pending["call_id"]}))
                self.assertEqual(old_cancel["status"], "recovered", old_cancel)
                deadline = time.monotonic() + 2
                while True:
                    old_result = self.row(await old_server.call_tool("interface_results", {
                        "call_id": old_pending["call_id"]}))
                    if (old_result["action"]["status"] != "running"
                            and "program_actions_lower_bound"
                                in old_result["action"]):
                        break
                    self.assertLess(time.monotonic(), deadline, old_result)
                    await asyncio.sleep(0.01)
                self.assertEqual(old_result["action"]["target_generation"], old_generation)
                self.assertEqual(old_result["action"]["status"], "recovered")
                self.assertTrue(old_result["cancellation"]["release_confirmed"])
                self.assertIsNone(old_result["task_success"])
                frozen_old = json.loads(json.dumps(old_result, sort_keys=True))

                new_program = self.valid_program()
                new_program["program_id"] = "public-standard-save-fresh-generation"
                new_program["source"]["target_generations"] = {"fixture": new_generation}
                new = self.row(await new_server.call_tool("interface_dispatch", {
                    "program": new_program,
                    "current_observation_seq": 1,
                    "current_binding_revision": 1,
                    "wait_for_result_ms": 5000}))
                self.assertEqual(new["status"], "returned", new)
                self.assertNotEqual(new["call_id"], old_pending["call_id"])
                self.assertNotEqual(new["operation_id"], old_result["action"]["operation_id"])
                self.assertEqual(new["target_generation"], new_generation)

                verified = json.loads((await new_server.call_tool(
                    "interface_verify_task", {
                        "call_id": new["call_id"],
                        "wait_for_result_ms": 1000})).content[0].text)
                self.assertEqual(verified["status"], "verified", verified)
                self.assertTrue(verified["task_success"])
                receipt = verified["task_effect"]["receipt"]
                self.assertEqual(receipt["call_id"], new["call_id"])
                self.assertEqual(receipt["operation_id"], new["operation_id"])
                self.assertEqual(receipt["target_generation"], new_generation)
                self.assertEqual(receipt["oracle_id"], "e" * 32)
                self.assertEqual(len(oracle_calls), 1)
                self.assertEqual(oracle_calls[0]["call_id"], new["call_id"])

                old_after = self.row(await old_server.call_tool("interface_results", {
                    "call_id": old_pending["call_id"]}))
                self.assertEqual(old_after, frozen_old)
            finally:
                await new_server.call_tool("interface_close", {})
                if old_session.state != "closed":
                    await old_server.call_tool("interface_close", {})

    async def test_recovered_cancel_persists_terminal_action_receipt(self):
        process = FakeProcess()
        identity = {"pid": 7101, "creation_time_100ns": 90101}
        op_owner = OperationOwner(clock_ns=time.monotonic_ns,
            process_identity_reader=lambda handle: identity if handle is process else None)
        supervisor = RecoveringFakeSupervisor(op_owner, process)
        owner = OwnedWin32SessionOwner(op_owner, supervisor, synthetic_only=False)
        owner.bind_target_generation_reader(lambda: GENERATION)
        producer = HeldProducerFactory(process, identity)
        producer.program_actions_lower_bound = 2
        with TemporaryDirectory() as root:
            server = self.make_server(root, owner, producer)
            program = self.valid_program()
            program["authority"]["expires_at_ns"] = time.monotonic_ns() + 5_000_000_000
            pending = self.row(await server.call_tool("interface_dispatch", {
                "program": program,
                "current_observation_seq": 1,
                "current_binding_revision": 1,
                "wait_for_result_ms": 0}))
            self.assertEqual(pending["status"], "pending")
            for _ in range(20):
                self.row(await server.call_tool("interface_results", {
                    "call_id": pending["call_id"]}))
                if producer.started.is_set():
                    break
                await asyncio.sleep(0.01)
            self.assertTrue(await asyncio.wait_for(
                asyncio.to_thread(producer.started.wait, 1), 1))

            cancelled = self.row(await server.call_tool("interface_cancel", {
                "call_id": pending["call_id"]}))
            self.assertEqual(cancelled["status"], "recovered")
            deadline = time.monotonic() + 2
            while True:
                retained = self.row(await server.call_tool("interface_results", {
                    "call_id": pending["call_id"]}))
                if (retained["action"]["status"] != "running"
                        and "program_actions_lower_bound" in retained["action"]):
                    break
                self.assertLess(time.monotonic(), deadline, retained)
                await asyncio.sleep(0.01)
            self.assertEqual(retained["cancellation"]["status"], "recovered")
            self.assertTrue(retained["cancellation"]["release_confirmed"])
            self.assertEqual(retained["action"]["status"], "recovered", retained)
            self.assertEqual(retained["action"]["obligations"],
                             retained["cancellation"]["result"]["obligations"])
            action_result = retained["action"]["result"]
            self.assertEqual(action_result["status"], "recovered")
            self.assertEqual(retained["action"][
                "recovery_release_key_up_attempts"], [{
                    "virtual_key": 0x57, "encoding": "scan_code",
                    "status": "returned"}])
            self.assertEqual(action_result[
                "recovery_release_key_up_attempts"], [{
                    "virtual_key": 0x57, "encoding": "scan_code",
                    "status": "returned"}])
            cleanup = retained["cancellation"]["result"]
            readback = cleanup["readback"]
            self.assertEqual(readback["operation_id"],
                             retained["action"]["operation_id"])
            self.assertEqual(readback["target_generation"],
                             retained["action"]["target_generation"])
            self.assertEqual(readback["recovery_id"], cleanup["recovery_id"])
            self.assertIs(readback["neutral"], True)
            self.assertIsInstance(readback["observed_monotonic_ns"], int)
            self.assertGreater(readback["observed_monotonic_ns"], 0)
            self.assertEqual(readback["key_button_states"], [False])
            self.assertEqual(readback["unicode_event_units"], 0)
            self.assertIsInstance(cleanup["cleanup_requested_monotonic_ns"], int)
            self.assertIsInstance(cleanup["recovery_completed_monotonic_ns"], int)
            self.assertEqual(cleanup["cleanup_latency_ns"],
                             cleanup["recovery_completed_monotonic_ns"]
                             - cleanup["cleanup_requested_monotonic_ns"])
            self.assertIsInstance(
                cleanup["cleanup_requested_perf_counter_ns"], int)
            self.assertIsInstance(
                cleanup["recovery_completed_perf_counter_ns"], int)
            self.assertEqual(
                cleanup["cleanup_latency_perf_counter_ns"],
                cleanup["recovery_completed_perf_counter_ns"]
                - cleanup["cleanup_requested_perf_counter_ns"])
            self.assertLess(cleanup["recovery_completed_monotonic_ns"],
                            cleanup["cleanup_deadline_ns"])
            self.assertTrue(action_result["release_confirmed"])
            self.assertTrue(action_result["input_dispatched"])
            self.assertEqual(action_result["program_actions_lower_bound"], 2)
            self.assertTrue(retained["action"]["input_dispatched"])
            self.assertEqual(action_result["effect_status"], "unknown")
            self.assertIsNone(action_result["task_success"])
            self.assertFalse(action_result["replay_allowed"])
            self.assertIsNone(retained["task_success"])
            self.assertFalse(retained["replay_allowed"])
            call_directory = Path(root) / pending["call_id"]
            report_path = call_directory / "report.json"
            report_temp = call_directory / ".report.json.tmp"
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                if report_path.is_file() and not report_temp.exists():
                    break
                await asyncio.sleep(0.01)
            self.assertTrue(report_path.is_file())
            self.assertFalse(report_temp.exists())
            public_dispatch = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertIs(public_dispatch["input_dispatched"], True)
            self.assertEqual(
                public_dispatch["result"]["program_actions_lower_bound"], 2)
            deadline = time.monotonic() + 2
            while True:
                closed = self.row(await server.call_tool("interface_close", {}))
                if closed["status"] == "closed":
                    break
                self.assertLess(time.monotonic(), deadline, closed)
                await asyncio.sleep(0.02)

    async def test_recovered_progress_capture_failure_is_visible_in_public_receipt(self):
        process = FakeProcess()
        identity = {"pid": 7101, "creation_time_100ns": 90101}
        op_owner = OperationOwner(clock_ns=time.monotonic_ns,
            process_identity_reader=lambda handle: identity if handle is process else None)
        supervisor = RecoveringFakeSupervisor(op_owner, process)
        owner = OwnedWin32SessionOwner(op_owner, supervisor, synthetic_only=False)
        owner.bind_target_generation_reader(lambda: GENERATION)
        producer = HeldProducerFactory(process, identity)

        def fail_progress(_process):
            raise ValueError("unknown native producer process")

        producer.read_program_actions_lower_bound = fail_progress
        with TemporaryDirectory() as root:
            server = self.make_server(root, owner, producer)
            program = self.valid_program()
            program["authority"]["expires_at_ns"] = time.monotonic_ns() + 5_000_000_000
            pending = self.row(await server.call_tool("interface_dispatch", {
                "program": program,
                "current_observation_seq": 1,
                "current_binding_revision": 1,
                "wait_for_result_ms": 0}))
            self.assertEqual(pending["status"], "pending")
            for _ in range(20):
                self.row(await server.call_tool("interface_results", {
                    "call_id": pending["call_id"]}))
                if producer.started.is_set():
                    break
                await asyncio.sleep(0.01)
            self.assertTrue(await asyncio.wait_for(
                asyncio.to_thread(producer.started.wait, 1), 1))

            cancelled = self.row(await server.call_tool("interface_cancel", {
                "call_id": pending["call_id"]}))
            self.assertEqual(cancelled["status"], "recovered")
            deadline = time.monotonic() + 2
            while True:
                retained = self.row(await server.call_tool("interface_results", {
                    "call_id": pending["call_id"]}))
                if retained["action"]["status"] == "recovered" and \
                        retained["action"].get("program_actions_capture_status") == "unavailable":
                    break
                self.assertLess(time.monotonic(), deadline, retained)
                await asyncio.sleep(0.01)

            self.assertEqual(
                retained["action"]["program_actions_capture_error_code"],
                "producer_registry_miss")
            self.assertTrue(retained["cancellation"]["release_confirmed"])
            self.assertIsNone(retained["action"].get("program_actions_lower_bound"))
            self.assertFalse(retained["replay_allowed"])
            self.assertIsNone(retained["task_success"])
            deadline = time.monotonic() + 2
            while True:
                close = self.row(await server.call_tool("interface_close", {}))
                if close["status"] == "closed":
                    break
                self.assertLess(time.monotonic(), deadline, close)
                await asyncio.sleep(0.02)

    async def test_late_recovery_after_dispatch_return_promotes_action_receipt(self):
        process = FakeProcess()
        identity = {"pid": 7101, "creation_time_100ns": 90101}
        op_owner = OperationOwner(clock_ns=time.monotonic_ns,
            process_identity_reader=lambda handle: identity if handle is process else None)
        supervisor = DelayedRecoveringFakeSupervisor(op_owner, process,
            delay_s=0.25)
        owner = OwnedWin32SessionOwner(op_owner, supervisor, synthetic_only=False)
        owner.bind_target_generation_reader(lambda: GENERATION)
        producer = HeldProducerFactory(process, identity)
        producer.program_actions_lower_bound = 2
        fence_events = []
        custody_fence = Mock()
        custody_fence.update.side_effect = lambda *args, **kwargs: fence_events.append(
            ("update", kwargs))
        custody_fence.resolve.side_effect = lambda *args, **kwargs: fence_events.append(
            ("resolve", kwargs))
        owner._custody_fence = custody_fence
        oracle_calls = []

        def oracle(action):
            oracle_calls.append(dict(action))
            return {"call_id": action["call_id"],
                "operation_id": action["operation_id"],
                "target_generation": action["target_generation"],
                "oracle_id": "f" * 32, "outcome": "failure",
                "observed_monotonic_ns": time.monotonic_ns(),
                "evidence_ref": "fixture-oracle:late-recovered-action"}

        with TemporaryDirectory() as root:
            server = create_server({"fixture": 123}, root,
                session_mode="supervised-win32",
                _supervised_win32_owner_factory=lambda *_args: owner,
                _supervised_win32_producer_factory=lambda *_args: producer,
                supervised_win32_task_oracle=oracle)
            program = self.valid_program()
            program["authority"]["expires_at_ns"] = time.monotonic_ns() + 800_000_000
            pending = self.row(await server.call_tool("interface_dispatch", {
                "program": program,
                "current_observation_seq": 1,
                "current_binding_revision": 1,
                "wait_for_result_ms": 0}))
            self.assertEqual(pending["status"], "pending")
            for _ in range(20):
                self.row(await server.call_tool("interface_results", {
                    "call_id": pending["call_id"]}))
                if producer.started.is_set():
                    break
                await asyncio.sleep(0.01)
            self.assertTrue(await asyncio.wait_for(
                asyncio.to_thread(producer.started.wait, 1), 1))

            while time.monotonic_ns() < program["authority"]["expires_at_ns"]:
                await asyncio.sleep(0.01)
            deadline = time.monotonic() + 2
            retained = None
            while time.monotonic() < deadline:
                retained = self.row(await server.call_tool("interface_results", {
                    "call_id": pending["call_id"]}))
                cancellation = retained.get("cancellation")
                if (isinstance(cancellation, dict)
                        and cancellation.get("status") == "pending"):
                    break
                await asyncio.sleep(0.005)

            self.assertIsNotNone(retained)
            self.assertEqual(retained["cancellation"]["status"], "pending")
            self.assertFalse(retained["cancellation"]["release_confirmed"])
            self.assertEqual(retained["action"]["status"], "running", retained)
            self.assertIsNone(retained["task_success"])
            self.assertFalse(retained["replay_allowed"])
            # This result lookup sends no new input; action and cancellation
            # remain separate records with separate release state.
            self.assertFalse(retained["input_dispatched"])

            while time.monotonic() < deadline:
                retained = self.row(await server.call_tool("interface_results", {
                    "call_id": pending["call_id"]}))
                cancellation = retained.get("cancellation")
                if (isinstance(cancellation, dict)
                        and cancellation.get("status") == "recovered"
                        and ("program_actions_lower_bound"
                             in retained["action"]
                             or retained["action"].get(
                                 "program_actions_capture_status") == "unavailable")):
                    break
                await asyncio.sleep(0.01)

            self.assertIsNotNone(retained)
            self.assertEqual(retained["cancellation"]["status"], "recovered")
            self.assertTrue(retained["cancellation"]["release_confirmed"])
            self.assertEqual(retained["action"]["status"], "recovered", retained)
            self.assertEqual(
                retained["action"]["program_actions_lower_bound"], 2)
            self.assertEqual(
                retained["action"]["program_actions_capture_status"],
                "observed")
            input_update = next(index for index, (kind, fields)
                in enumerate(fence_events)
                if kind == "update" and fields.get("input_dispatched") is True)
            resolution = next(index for index, (kind, _fields)
                in enumerate(fence_events) if kind == "resolve")
            self.assertLess(input_update, resolution)
            self.assertEqual(retained["action"]["result"]["status"], "recovered")
            self.assertTrue(retained["action"]["result"]["release_confirmed"])
            self.assertIsNone(retained["action"]["result"]["task_success"])
            self.assertIsNone(retained["task_success"])
            verified = self.row(await server.call_tool("interface_verify_task", {
                "call_id": pending["call_id"], "wait_for_result_ms": 1000}))
            self.assertEqual(verified["status"], "verified", verified)
            self.assertFalse(verified["task_success"])
            self.assertEqual(len(oracle_calls), 1)
            self.assertEqual(oracle_calls[0]["operation_id"],
                             retained["action"]["operation_id"])
            close_statuses = []
            deadline = time.monotonic() + 2
            try:
                while time.monotonic() < deadline:
                    closed = self.row(await server.call_tool("interface_close", {}))
                    close_statuses.append(closed.get("status"))
                    if closed.get("status") == "closed":
                        break
                    await asyncio.sleep(0.02)
                self.assertEqual(close_statuses[-1], "closed", close_statuses)
            finally:
                if owner.state != "closed":
                    await asyncio.sleep(0.55)
                    self.row(await server.call_tool("interface_close", {}))

    async def test_terminal_unknown_dispatch_marks_action_unknown_but_keeps_custody_open(self):
        process = FakeProcess()
        identity = {"pid": 7101, "creation_time_100ns": 90101}
        op_owner = OperationOwner(clock_ns=time.monotonic_ns,
            process_identity_reader=lambda handle: identity if handle is process else None)
        supervisor = UnknownAfterCancelSupervisor(op_owner)
        owner = OwnedWin32SessionOwner(op_owner, supervisor, synthetic_only=False)
        owner.bind_target_generation_reader(lambda: GENERATION)
        producer = HeldProducerFactory(process, identity)
        with TemporaryDirectory() as root:
            server = self.make_server(root, owner, producer)
            async with server.settings.lifespan(server):
                pending = self.row(await server.call_tool("interface_dispatch", {
                    "program": self.valid_program(),
                    "current_observation_seq": 1,
                    "current_binding_revision": 1,
                    "wait_for_result_ms": 0}))
                self.assertEqual(pending["status"], "pending")
                self.assertTrue(await asyncio.wait_for(
                    asyncio.to_thread(producer.started.wait, 1), 1))

                cancelled = self.row(await server.call_tool("interface_cancel", {
                    "call_id": pending["call_id"]}))
                self.assertEqual(cancelled["status"], "unknown")
                deadline = time.monotonic() + 1
                retained = None
                while time.monotonic() < deadline:
                    retained = self.row(await server.call_tool("interface_results", {
                        "call_id": pending["call_id"]}))
                    if retained["action"]["status"] != "running":
                        break
                    await asyncio.sleep(0.01)

                self.assertEqual(retained["action"]["status"], "unknown")
                action_result = retained["action"]["result"]
                self.assertEqual(action_result["status"], "unknown")
                self.assertIsNone(action_result["task_success"])
                self.assertFalse(action_result["release_confirmed"])
                self.assertFalse(action_result["replay_allowed"])
                self.assertEqual(retained["cancellation"]["status"], "unknown")
                self.assertEqual(op_owner.result(retained["action"]["operation_id"])[
                    "phase"], "unknown")
                self.assertEqual(owner.close()["status"], "busy")
                self.assertEqual(owner.state, "open")

    async def test_missing_positive_attempt_receipt_stays_unknown_in_public_results(self):
        process = FakeProcess()
        identity = {"pid": 7101, "creation_time_100ns": 90101}
        op_owner = OperationOwner(clock_ns=time.monotonic_ns,
            process_identity_reader=lambda handle: identity if handle is process else None)
        supervisor = MissingAttemptReceiptSupervisor(op_owner, process)
        owner = OwnedWin32SessionOwner(op_owner, supervisor, synthetic_only=False)
        owner.bind_target_generation_reader(lambda: GENERATION)
        producer = HeldProducerFactory(process, identity)
        with TemporaryDirectory() as root:
            server = self.make_server(root, owner, producer)
            async with server.settings.lifespan(server):
                pending = self.row(await server.call_tool("interface_dispatch", {
                    "program": self.valid_program(),
                    "current_observation_seq": 1,
                    "current_binding_revision": 1,
                    "wait_for_result_ms": 0}))
                self.assertEqual(pending["status"], "pending")
                self.assertTrue(await asyncio.wait_for(
                    asyncio.to_thread(producer.started.wait, 1), 1))

                cancelled = self.row(await server.call_tool("interface_cancel", {
                    "call_id": pending["call_id"]}))
                self.assertEqual(cancelled["status"], "unknown", cancelled)
                retained = self.row(await server.call_tool("interface_results", {
                    "call_id": pending["call_id"]}))

                self.assertEqual(retained["action"]["status"], "unknown")
                self.assertFalse(retained["action"]["release_confirmed"])
                self.assertFalse(retained["action"]["result"]["release_confirmed"])
                self.assertEqual(retained["cancellation"]["status"], "unknown")
                self.assertEqual(retained["cancellation"]["result"]["uncertainty"],
                    "recovery_key_up_attempt_receipt_missing_or_invalid")
                self.assertFalse(retained["cancellation"]["release_confirmed"])
                self.assertIsNone(retained["task_success"])
                self.assertFalse(retained["replay_allowed"])
                self.assertEqual(op_owner.result(
                    retained["action"]["operation_id"])["phase"], "unknown")
                self.assertEqual(owner.close()["status"], "busy")

    async def test_stale_target_generation_is_refused_before_producer_start(self):
        owner, producer, _ = self.make_components(generation="b" * 64)
        with TemporaryDirectory() as root:
            server = self.make_server(root, owner, producer)
            reply = await server.call_tool("interface_dispatch", {
                "program": self.valid_program(),
                "current_observation_seq": 1,
                "current_binding_revision": 1})
            result = self.row(reply)
            self.assertEqual(result.get("status"), "invalid_request", result)
            self.assertFalse(result["operation_invoked"])
            self.assertEqual(owner.list_results(), [])
            await server.call_tool("interface_close", {})

    async def test_unavailable_target_generation_has_stable_public_refusal(self):
        owner, producer, _ = self.make_components()
        def unavailable_generation():
            raise RuntimeError("invalid HWND for target fixture")
        owner.bind_target_generation_reader(unavailable_generation)
        with TemporaryDirectory() as root:
            server = self.make_server(root, owner, producer)
            reply = await server.call_tool("interface_dispatch", {
                "program": self.valid_program(),
                "current_observation_seq": 1,
                "current_binding_revision": 1})
            result = self.row(reply)
            self.assertEqual(result.get("status"), "invalid_request", result)
            self.assertEqual(result.get("error"), "TARGET_GENERATION_UNAVAILABLE", result)
            self.assertFalse(result["operation_invoked"])
            self.assertFalse(result["input_dispatched"])
            self.assertIsNone(result["task_success"])
            self.assertFalse(result["replay_allowed"])
            self.assertEqual(owner.list_results(), [])
            self.assertEqual(producer.started, 0)
            await server.call_tool("interface_close", {})

    async def test_source_binding_mismatch_creates_no_operation(self):
        owner, producer, _ = self.make_components()
        program = self.valid_program()
        program["source"]["observation_seq"] = 2
        with TemporaryDirectory() as root:
            server = self.make_server(root, owner, producer)
            reply = await server.call_tool("interface_dispatch", {
                "program": program,
                "current_observation_seq": 1,
                "current_binding_revision": 1})
            result = self.row(reply)
            self.assertIn("STANDARD_SOURCE_BINDING_MISMATCH", result.get("error", ""), result)
            self.assertEqual(owner.list_results(), [])
            await server.call_tool("interface_close", {})

    async def test_cancel_before_admission_is_retained_and_prevents_producer_start(self):
        owner, producer, _ = self.make_components()
        entered = threading.Event()
        continue_binding = threading.Event()
        def delayed_generation():
            entered.set()
            if not continue_binding.wait(2):
                raise TimeoutError("test generation reader timed out")
            return GENERATION
        owner.bind_target_generation_reader(delayed_generation)
        with TemporaryDirectory() as root:
            server = self.make_server(root, owner, producer)
            dispatch_task = asyncio.create_task(server.call_tool("interface_dispatch", {
                "program": self.valid_program(),
                "current_observation_seq": 1,
                "current_binding_revision": 1,
                "wait_for_result_ms": 0}))
            pending = self.row(await dispatch_task)
            self.assertEqual(pending["status"], "pending")
            self.assertTrue(entered.wait(1))
            with patch.object(owner, "interface_result", return_value=None):
                during_admission = self.row(await server.call_tool("interface_results", {
                    "call_id": pending["call_id"]}))
            self.assertEqual(during_admission["status"], "pending", during_admission)
            self.assertEqual(during_admission["call"]["call_id"], pending["call_id"])
            cancelled = self.row(await server.call_tool("interface_cancel", {
                "call_id": pending["call_id"]}))
            self.assertEqual(cancelled["status"], "cancel_pending")
            continue_binding.set()
            for _ in range(100):
                action = owner.interface_result(pending["call_id"])
                if action is not None:
                    break
                await asyncio.sleep(0.01)
            await asyncio.sleep(0.05)
            self.assertEqual(producer.started, 0)
            row = owner.interface_result(pending["call_id"])
            self.assertIsNotNone(row["cancellation"])
            self.assertFalse(row["action"].get("release_confirmed", False))
            self.assertFalse(row["action"].get("replay_allowed", False))
            retrieved = self.row(await server.call_tool("interface_results", {
                "call_id": pending["call_id"]}))
            self.assertIsNotNone(retrieved["cancellation"])
            operation_id = row["action"]["operation_id"]
            owner._owner.mark_unknown(operation_id, GENERATION,
                "test_closed_gate_cancellation")
            # The supervised lookup exposes custody, not the MCP worker state.
            # Wait for its atomic report publication before removing the root.
            report_path = Path(root) / pending["call_id"] / "report.json"
            report_temp = report_path.with_name(".report.json.tmp")
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                if report_path.is_file() and not report_temp.exists():
                    break
                await asyncio.sleep(0.01)
            self.assertTrue(report_path.is_file(), "dispatch report was not finalized")
            self.assertFalse(report_temp.exists(), "dispatch report is still being written")
            await server.call_tool("interface_close", {})

    async def test_compiled_graph_routes_each_action_through_supervised_dispatch(self):
        generation = {"value": GENERATION}
        process = FakeProcess()
        identity = {"pid": 7101, "creation_time_100ns": 90101}
        op_owner = OperationOwner(clock_ns=time.monotonic_ns,
            process_identity_reader=lambda handle: identity if handle is process else None)
        supervisor = FakeSupervisor(op_owner)
        owner = OwnedWin32SessionOwner(op_owner, supervisor, synthetic_only=False)
        owner.bind_target_generation_reader(lambda: generation["value"])
        producer = FakeProducerFactory(process, identity)
        fixture_effects = []

        def effectful_producer(request):
            child, identity_reader, open_gate = producer(request)

            def commit_fixture_effect():
                # Model the fixture application's state separately from the
                # compiled graph predicate and the public dispatch receipt.
                fixture_effects.append({
                    "operation_id": request["operation_id"],
                    "target_generation": request["target_generation"],
                    "effect": "saved",
                })
                open_gate()

            return child, identity_reader, commit_fixture_effect

        effectful_producer.read_result = producer.read_result

        interface = {
            "format": "compiled-gui-interface-v1",
            "interface_id": "supervised-win32-generation-boundary",
            "session_scope": "fixture-session",
            "surface": "fixture",
            "predicates": ["ready", "first_done"],
            "symbols": {"fixture": {"kind": "target_reference",
                "target_reference": "fixture", "identity_predicate": "ready",
                "dependencies": ["ready"]}},
            "actions": {
                "first": {"target_symbol": "fixture", "operation": "save",
                    "expected_effect": {"first_done": True}},
                "suffix": {"target_symbol": "fixture", "operation": "save_again",
                    "expected_effect": {"first_done": True}},
            },
            "method": {"name": "two-step", "version": "1",
                "initial_state": "before", "max_transitions": 2,
                "max_runtime_ms": 5000,
                "states": {
                    "before": {"branches": [{"when": {"ready": True},
                        "outcome": "action", "action": "first",
                        "next_state": "after", "reason": None}]},
                    "after": {"branches": [{"when": {"first_done": True},
                        "outcome": "action", "action": "suffix",
                        "next_state": "after", "reason": None}]},
                }},
        }
        public_observations = 0
        dispatch_rows = []
        observation_call_ids = []
        oracle_calls = []

        def task_oracle(action):
            if not any(effect["operation_id"] == action["operation_id"]
                       and effect["target_generation"] == action["target_generation"]
                       and effect["effect"] == "saved"
                       for effect in fixture_effects):
                raise AssertionError("independent fixture effect does not match exact action")
            oracle_calls.append(dict(action))
            return {"call_id": action["call_id"],
                "operation_id": action["operation_id"],
                "target_generation": action["target_generation"],
                "oracle_id": "f" * 32, "outcome": "success",
                "observed_monotonic_ns": time.monotonic_ns(),
                "evidence_ref": "fixture-task-oracle:compiled-prefix"}

        def standard_observe(_targets, *, target, frame, region,
                             capture_directory=None, display_name=None):
            nonlocal public_observations
            del capture_directory, display_name
            public_observations += 1
            if public_observations == 2:
                # Replace the target between the standard caller's fresh
                # observation and any graph-selected suffix action.
                generation["value"] = "b" * 64
            return {"schema": "agent-interface/runtime-observation-v1",
                "observation_id": f"public-observation-{public_observations}",
                "status": "returned", "target": target,
                "target_generation": generation["value"],
                "target_generation_consistency": "matched",
                "observation": {"frame": frame, "region": region,
                    "capture_started_ns": time.monotonic_ns(),
                    "capture_ended_ns": time.monotonic_ns()},
                "side_effect_authority": False, "input_dispatched": False}

        with TemporaryDirectory() as root, patch(
                "runtime.cli_v1.mcp_server.observe", standard_observe):
            server = create_server({"fixture": 123}, root,
                session_mode="supervised-win32",
                _supervised_win32_owner_factory=lambda *_args: owner,
                _supervised_win32_producer_factory=lambda *_args: effectful_producer,
                supervised_win32_task_oracle=task_oracle)
            loop = asyncio.get_running_loop()

            def standard_observe(target, frame, region):
                reply = asyncio.run_coroutine_threadsafe(server.call_tool(
                    "interface_observe", {"target": target, "frame": frame,
                        "region": region}), loop).result(timeout=8)
                observation_call_ids.append(json.loads(
                    reply.content[0].text)["call_id"])
                return reply

            def standard_dispatch(program, sequence, binding_revision):
                self.assertEqual(program["source"]["target_generations"],
                    {"fixture": GENERATION})
                reply = asyncio.run_coroutine_threadsafe(server.call_tool(
                    "interface_dispatch", {"program": program,
                    "current_observation_seq": sequence,
                    "current_binding_revision": binding_revision,
                    "wait_for_result_ms": 5000}), loop).result(timeout=8)
                dispatch_rows.append(self.row(reply))
                return reply

            def stale_template():
                program = self.valid_program()
                program["source"]["target_generations"] = {"fixture": "c" * 64}
                return program

            def perceive(report, _reply):
                first_observation = report["observation_id"] == "public-observation-1"
                return {"ready": True,
                    "first_done": (not first_observation and any(
                        effect["effect"] == "saved"
                        and effect["target_generation"] == GENERATION
                        for effect in fixture_effects))}

            # Simulate the provider wait between its grounding observation and
            # compiled execution. The first fresh public observation must match
            # that original generation before perception or dispatch can start.
            generation["value"] = "b" * 64
            pre_wait = await asyncio.to_thread(run_public_compiled,
                interface,
                {"first": stale_template(), "suffix": stale_template()},
                target="fixture", current_binding_revision=1,
                region=[0, 0, 1, 1], observe=standard_observe,
                dispatch=standard_dispatch, perceive=perceive,
                verify_effect=lambda _request, _report, _reply: {
                    "status": "succeeded",
                    "evidence_ref": "unused-stale-generation"},
                expected_generation=GENERATION, cancelled=lambda: False)
            self.assertEqual(pre_wait["outcome"], "SAFE_YIELD", pre_wait)
            self.assertEqual(pre_wait["reason"], "association_changed")
            self.assertEqual(pre_wait["completed_transitions"], 0)
            self.assertEqual(pre_wait["observations"], [])
            self.assertEqual(dispatch_rows, [])
            self.assertEqual(len(observation_call_ids), 1)

            generation["value"] = GENERATION
            public_observations = 0
            observation_call_ids.clear()
            receipt = await asyncio.to_thread(run_public_compiled,
                interface,
                {"first": stale_template(), "suffix": stale_template()},
                target="fixture", current_binding_revision=1,
                region=[0, 0, 1, 1], observe=standard_observe,
                dispatch=standard_dispatch, perceive=perceive,
                verify_effect=lambda _request, _report, _reply: {
                    "status": "succeeded",
                    "evidence_ref": "test-effect-predicate-confirmation"},
                expected_generation=GENERATION,
                cancelled=lambda: False)
            try:
                self.assertEqual(receipt["outcome"], "SAFE_YIELD")
                self.assertEqual(receipt["reason"], "association_changed", receipt)
                self.assertEqual(receipt["completed_transitions"], 1)
                self.assertEqual([row["status"] for row in dispatch_rows], ["returned"])
                self.assertEqual(receipt["standard_action_call_ids"],
                    [dispatch_rows[0]["call_id"]])
                self.assertEqual(receipt["standard_observation_call_ids"],
                    observation_call_ids)
                self.assertEqual(len(observation_call_ids), 2)
                self.assertIsNone(receipt["task_success"])
                self.assertTrue(dispatch_rows[0]["input_dispatched"])
                self.assertEqual(producer.started, 1)
                self.assertEqual(len(owner.list_results()), 1)
                self.assertIsNone(dispatch_rows[0]["task_success"])
                retained = self.row(await server.call_tool("interface_results", {
                    "call_id": dispatch_rows[0]["call_id"]}))
                expected_action = dict(
                    dispatch_rows[0]["supervision"]["action"])
                expected_action["input_dispatched"] = dispatch_rows[0][
                    "input_dispatched"]
                self.assertEqual(retained["action"], expected_action)
                # Retrieval did not dispatch input: keep the query envelope
                # false while exposing the original action's dispatch evidence.
                self.assertFalse(retained["input_dispatched"])
                self.assertTrue(retained["action"]["input_dispatched"])
                self.assertIsNone(retained["task_success"])
                verified = json.loads((await server.call_tool(
                    "interface_verify_task", {
                        "call_id": dispatch_rows[0]["call_id"],
                        "wait_for_result_ms": 1000})).content[0].text)
                self.assertEqual(verified["status"], "verified", verified)
                self.assertTrue(verified["task_success"])
                self.assertFalse(verified["operation_invoked"])
                self.assertFalse(verified["input_dispatched"])
                self.assertFalse(verified["replay_allowed"])
                self.assertEqual(len(oracle_calls), 1)
                self.assertEqual(oracle_calls[0]["call_id"],
                    dispatch_rows[0]["call_id"])
                self.assertEqual(oracle_calls[0]["operation_id"],
                    dispatch_rows[0]["supervision"]["action"]["operation_id"])
                self.assertEqual(oracle_calls[0]["target_generation"], GENERATION)
                self.assertEqual(fixture_effects, [{
                    "operation_id": oracle_calls[0]["operation_id"],
                    "target_generation": GENERATION,
                    "effect": "saved",
                }])
                retained = self.row(await server.call_tool("interface_results", {
                    "call_id": dispatch_rows[0]["call_id"]}))
                self.assertTrue(retained["task_success"], retained)
                self.assertEqual(retained["task_effect"]["receipt"]["evidence_ref"],
                    "fixture-task-oracle:compiled-prefix")
                self.assertEqual(producer.started, 1)
            finally:
                await server.call_tool("interface_close", {})

    async def test_public_compiled_caller_joins_exact_result_query_and_task_oracle(self):
        process = FakeProcess()
        identity = {"pid": 7101, "creation_time_100ns": 90101}
        effects = []
        operation_owner = OperationOwner(clock_ns=time.monotonic_ns,
            process_identity_reader=lambda handle: identity if handle is process else None)
        supervisor = RecoveringFakeSupervisor(operation_owner, process)
        owner = OwnedWin32SessionOwner(operation_owner, supervisor,
            synthetic_only=False)
        owner.bind_target_generation_reader(lambda: GENERATION)

        class EffectfulProducer(FakeProducerFactory):
            fail_next = False

            def __call__(self, action):
                self.started += 1
                if self.process.pid is not None:
                    self.process.pid = None
                    self.process.exitcode = None
                    self.process.alive = False
                def authorize_start():
                    # Keep the public dispatch pending long enough for the
                    # caller to exercise exact-call result retrieval.
                    time.sleep(0.04)
                    if not self.fail_next:
                        effects.append({"operation_id": action["operation_id"],
                            "target_generation": action["target_generation"]})
                    self.process.alive = False
                    self.process.exitcode = 0
                return self.process, lambda: self.identity, authorize_start

            def read_result(self, process):
                if self.fail_next:
                    self.fail_next = False
                    if process is not self.process or process.is_alive():
                        raise RuntimeError("failure fixture did not exit")
                    return {"result": {"status": "runtime_failed",
                            "error_type": "RuntimeError",
                            "detail": "controlled result exception"},
                        "release_receipt": {"verified": False,
                            "keys_down": [], "buttons_down": [],
                            "keys_unknown": ["producer_exception"],
                            "buttons_unknown": []}}
                return super().read_result(process)

        producer = EffectfulProducer(process, identity)
        oracle_calls = []

        def task_oracle(action):
            matching = any(row["operation_id"] == action["operation_id"]
                and row["target_generation"] == action["target_generation"]
                for row in effects)
            if not matching:
                raise AssertionError("task oracle did not find the exact fixture effect")
            oracle_calls.append(dict(action))
            return {"call_id": action["call_id"],
                "operation_id": action["operation_id"],
                "target_generation": action["target_generation"],
                "oracle_id": "e" * 32, "outcome": "success",
                "observed_monotonic_ns": time.monotonic_ns(),
                "evidence_ref": "fixture-oracle:compiled-public-caller"}

        interface = {
            "format": "compiled-gui-interface-v1",
            "interface_id": "public-result-query-composition",
            "session_scope": "supervised-win32-fixture",
            "surface": "fixture",
            "predicates": ["ready", "saved"],
            "symbols": {"fixture": {"kind": "target_reference",
                "target_reference": "fixture", "identity_predicate": "ready",
                "dependencies": ["ready"]}},
            "actions": {"save": {"target_symbol": "fixture",
                "operation": "save", "expected_effect": {"saved": True}}},
            "method": {"name": "save-once", "version": "1",
                "initial_state": "before", "max_transitions": 1,
                "max_runtime_ms": 2000,
                "states": {
                    "before": {"branches": [{"when": {"ready": True},
                        "outcome": "action", "action": "save",
                        "next_state": "after", "reason": None}]},
                    "after": {"branches": [{"when": {"saved": True},
                        "outcome": "complete", "action": None,
                        "next_state": None, "reason": None}]}}},
        }
        observation_count = 0
        observed_call_ids = []
        dispatch_call_ids = []
        result_queries = []
        task_client_calls = []
        callback_errors = []
        observation_envelopes = []
        loop = asyncio.get_running_loop()

        def fake_observe(_targets, *, target, frame, region,
                         capture_directory=None, display_name=None):
            nonlocal observation_count
            observation_count += 1
            now = time.monotonic_ns()
            return {"schema": "agent-interface/runtime-observation-v1",
                "observation_id": f"public-composition-{observation_count}",
                "status": "returned", "target": target,
                "target_generation": GENERATION,
                "target_generation_consistency": "matched",
                "observation": {"frame": frame, "region": region,
                    "capture_started_ns": now, "capture_ended_ns": now},
                "predicates": {"ready": True, "saved": bool(effects)},
                "side_effect_authority": False, "input_dispatched": False}

        with TemporaryDirectory() as root, patch(
                "runtime.cli_v1.mcp_server.observe", fake_observe):
            server = create_server({"fixture": 123}, root,
                session_mode="supervised-win32",
                _supervised_win32_owner_factory=lambda *_args: owner,
                _supervised_win32_producer_factory=lambda *_args: producer,
                supervised_win32_task_oracle=task_oracle)

            def call_tool(name, arguments):
                return asyncio.run_coroutine_threadsafe(
                    server.call_tool(name, arguments), loop).result(timeout=8)

            def observe(target, frame, region):
                try:
                    reply = call_tool("interface_observe", {"target": target,
                        "frame": frame, "region": region})
                    envelope = json.loads(reply.content[0].text)
                    observation_envelopes.append(envelope)
                    observation_call_id = (self.row(reply).get("call_id")
                        or envelope.get("call_id"))
                    if isinstance(observation_call_id, str):
                        observed_call_ids.append(observation_call_id)
                    return reply
                except Exception as error:
                    callback_errors.append(repr(error))
                    raise

            def dispatch(program, sequence, revision):
                reply = call_tool("interface_dispatch", {"program": program,
                    "current_observation_seq": sequence,
                    "current_binding_revision": revision,
                    "wait_for_result_ms": 0})
                row = self.row(reply)
                self.assertEqual(row["status"], "pending", row)
                dispatch_call_ids.append(row["call_id"])
                return reply

            def resolve_pending(call_id, pending_reply):
                try:
                    pending = self.row(pending_reply)
                    pending_call = pending.get("call_id") or (
                        pending.get("call", {}).get("call_id")
                        if isinstance(pending.get("call"), dict) else None)
                    self.assertEqual(pending_call, call_id, pending)
                    self.assertEqual(pending.get("status"), "pending", pending)
                    deadline = time.monotonic() + 3
                    while time.monotonic() < deadline:
                        reply = call_tool("interface_results", {
                            "call_id": call_id, "include_image": False})
                        row = self.row(reply)
                        result_queries.append(row)
                        retrieved_call = row.get("call_id") or (
                            row.get("call", {}).get("call_id")
                            if isinstance(row.get("call"), dict) else None)
                        self.assertEqual(retrieved_call, call_id, row)
                        action = row.get("action")
                        if (isinstance(action, dict)
                                and action.get("status") in (
                                    "completed", "unknown", "recovered")):
                            return reply
                        time.sleep(0.01)
                    self.fail("exact-call interface_results did not reach completed")
                except Exception as error:
                    callback_errors.append("resolve_pending: " + repr(error))
                    raise

            def verify_task(call_id):
                task_client_calls.append(call_id)
                return call_tool("interface_verify_task", {
                    "call_id": call_id, "wait_for_result_ms": 1000})

            try:
                result = await asyncio.to_thread(run_public_compiled,
                    interface, {"save": self.valid_program()},
                    target="fixture", current_binding_revision=1,
                    region=[0, 0, 1, 1], observe=observe, dispatch=dispatch,
                    resolve_pending=resolve_pending,
                    perceive=lambda report, _reply: report["predicates"],
                    verify_effect=lambda _request, _report, _reply: {
                        "status": "succeeded", "evidence_ref": "fixture-pixels"},
                    verify_task=verify_task, cancelled=lambda: False)
                self.assertEqual(result["outcome"], "TASK_SUCCEEDED",
                    {"result": result, "callback_errors": callback_errors,
                     "observation_envelopes": observation_envelopes})
                self.assertEqual(result["standard_action_call_ids"], dispatch_call_ids)
                self.assertEqual(result["standard_observation_call_ids"], observed_call_ids)
                self.assertTrue(any(envelope.get("status") == "busy"
                    for envelope in observation_envelopes))
                busy_rows = [row for row in result["standard_target_evidence"]
                    if row["kind"] == "observation_busy"]
                self.assertTrue(busy_rows, result)
                self.assertTrue(all(row["operation_invoked"] is False
                    and row["input_dispatched"] is False for row in busy_rows))
                dispatch_evidence = next(row for row in result[
                    "standard_target_evidence"] if row["kind"] == "dispatch")
                self.assertEqual(dispatch_evidence["call_id"], dispatch_call_ids[0])
                self.assertEqual(dispatch_evidence["pending_result_resolution"],
                    "same_call_id")
                self.assertTrue(result["task_verification"]["valid"], result)
                self.assertIs(result["task_success"], True)
                self.assertEqual(result["task_verification"]["action_call_id"],
                    dispatch_call_ids[0])
                self.assertTrue(any(isinstance(row.get("action"), dict)
                    and row["action"].get("status") == "completed"
                    for row in result_queries))
                self.assertEqual(len(oracle_calls), 1)
                self.assertEqual(oracle_calls[0]["call_id"], dispatch_call_ids[0])
                self.assertEqual(oracle_calls[0]["operation_id"],
                    result["transitions"][-1]["action_id"])
                self.assertEqual(len(effects), 1)
                self.assertEqual(producer.started, 1)

                # A second exact-call readback carries an exception/unknown
                # action plus release-only recovery. Without a verified late
                # input horizon, the caller must retain uncertainty and skip
                # task-effect verification.
                effects.clear()
                producer.fail_next = True
                failed = await asyncio.to_thread(run_public_compiled,
                    interface, {"save": self.valid_program()},
                    target="fixture", current_binding_revision=1,
                    region=[0, 0, 1, 1], observe=observe, dispatch=dispatch,
                    resolve_pending=resolve_pending,
                    perceive=lambda report, _reply: report["predicates"],
                    verify_effect=lambda _request, _report, _reply: {
                        "status": "succeeded", "evidence_ref": "must-not-score"},
                    verify_task=verify_task, cancelled=lambda: False)
                self.assertEqual(failed["outcome"], "RUNTIME_FAILED", failed)
                self.assertIsNone(failed["task_success"])
                self.assertIsNone(failed["task_verification"])
                failed_dispatch = next(row for row in failed[
                    "standard_target_evidence"] if row["kind"] == "dispatch")
                self.assertEqual(len(dispatch_call_ids), 2)
                self.assertNotEqual(dispatch_call_ids[0], dispatch_call_ids[1])
                self.assertEqual(failed_dispatch["call_id"], dispatch_call_ids[1])
                self.assertEqual(result_queries[-1]["call_id"],
                    dispatch_call_ids[1])
                self.assertEqual(failed_dispatch["pending_result_resolution"],
                    "same_call_id")
                self.assertEqual(failed_dispatch["status"], "uncertain")
                self.assertFalse(failed_dispatch["release_verified"])
                self.assertEqual(task_client_calls, [dispatch_call_ids[0]])
                self.assertEqual(len(oracle_calls), 1)
                self.assertEqual(producer.started, 2)
                # The public result can become readable just before the
                # producer's atomic report replacement finishes.
                report_temps = list(Path(root).glob("*/.report.json.tmp"))
                deadline = time.monotonic() + 2
                while report_temps and time.monotonic() < deadline:
                    await asyncio.sleep(0.01)
                    report_temps = list(Path(root).glob("*/.report.json.tmp"))
                self.assertFalse(report_temps, report_temps)
            finally:
                await server.call_tool("interface_close", {})

    async def test_stdio_expiry_delayed_recovery_and_exact_call_effect(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        with TemporaryDirectory() as root:
            output = Path(root) / "child-receipts"
            params = StdioServerParameters(command=sys.executable,
                args=["-m", "runtime.cli_v1.mcp_supervised_stdio_test_server",
                      "--output-directory", str(output), "--mode", "delayed-expiry"],
                cwd=str(Path(__file__).resolve().parents[2]))
            async with stdio_client(params) as (reader, writer):
                async with ClientSession(reader, writer) as client:
                    await client.initialize()
                    listed = await client.list_tools()
                    names = {tool.name for tool in listed.tools}
                    self.assertTrue({"interface_dispatch", "interface_results",
                                     "interface_verify_task"}.issubset(names))
                    program = {
                        "schema": "agent-interface/program-v1",
                        "program_id": "stdio-expiry-recovery",
                        "source": {"observation_seq": 1,
                            "binding_revision": 1,
                            "target_generations": {"fixture": GENERATION}},
                        "authority": {"lease_id": "stdio-expiry-lease",
                            "expires_at_ns": time.monotonic_ns() + 1_500_000_000},
                        "terminal": {"release_all_required": True},
                        "ops": [{"op": "focus", "target": "fixture"},
                            {"op": "key_chord", "keys": ["CTRL", "S"]},
                            {"op": "release_all"}]}
                    dispatched = await client.call_tool("interface_dispatch", {
                        "program": program, "current_observation_seq": 1,
                        "current_binding_revision": 1, "wait_for_result_ms": 0})
                    pending = self.row(dispatched)
                    self.assertEqual(pending["status"], "pending", pending)
                    call_id = pending["call_id"]
                    expiry_ns = program["authority"]["expires_at_ns"]
                    while time.monotonic_ns() < expiry_ns:
                        await asyncio.sleep(0.01)
                    self.assertGreaterEqual(time.monotonic_ns(), expiry_ns)

                    deadline = time.monotonic() + 3
                    retained = None
                    while time.monotonic() < deadline:
                        reply = await client.call_tool("interface_results", {
                            "call_id": call_id, "include_image": False})
                        retained = self.row(reply)
                        cancellation = retained.get("cancellation")
                        action = retained.get("action")
                        if (isinstance(cancellation, dict)
                                and cancellation.get("status") == "recovered"
                                and isinstance(action, dict)
                                and action.get("status") == "recovered"):
                            break
                        await asyncio.sleep(0.01)
                    self.assertIsNotNone(retained)
                    self.assertEqual(retained["call_id"], call_id)
                    self.assertEqual(retained["cancellation"]["status"],
                                     "recovered", retained)
                    self.assertTrue(retained["cancellation"]["release_confirmed"])
                    self.assertEqual(retained["action"]["status"], "recovered")
                    self.assertEqual(retained["action"]["program_actions_lower_bound"], 2)
                    self.assertIsNone(retained["task_success"])
                    self.assertFalse(retained["replay_allowed"])

                    verified_reply = await client.call_tool(
                        "interface_verify_task", {"call_id": call_id,
                            "wait_for_result_ms": 1000})
                    verified = self.row(verified_reply)
                    self.assertEqual(verified["call_id"], call_id)
                    self.assertEqual(verified["status"], "verified", verified)
                    self.assertFalse(verified["task_success"])
                    self.assertEqual(verified["task_effect"]["receipt"]["operation_id"],
                                     retained["action"]["operation_id"])
                    self.assertFalse(verified["replay_allowed"])

    async def test_stdio_exception_unknown_then_fresh_generation_recovery(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        from runtime.guarded_win32_v1.input_obligations import derive_input_obligations

        recovery_generation = "b" * 64
        with TemporaryDirectory() as root:
            source_output = Path(root) / "source-receipts"
            source_params = StdioServerParameters(command=sys.executable,
                args=["-m", "runtime.cli_v1.mcp_supervised_stdio_test_server",
                      "--output-directory", str(source_output), "--mode", "exception-unknown"],
                cwd=str(Path(__file__).resolve().parents[2]))
            async with stdio_client(source_params) as (reader, writer):
                async with ClientSession(reader, writer) as client:
                    await client.initialize()
                    program = self.valid_program()
                    program["authority"]["expires_at_ns"] = time.monotonic_ns() + 5_000_000_000
                    reply = await client.call_tool("interface_dispatch", {
                        "program": program, "current_observation_seq": 1,
                        "current_binding_revision": 1, "wait_for_result_ms": 0})
                    pending = self.row(reply)
                    self.assertEqual(pending["status"], "pending", pending)
                    deadline = time.monotonic() + 2
                    retained = None
                    while time.monotonic() < deadline:
                        result = await client.call_tool("interface_results", {
                            "call_id": pending["call_id"], "include_image": False})
                        retained = self.row(result)
                        action = retained.get("action")
                        if isinstance(action, dict) and action.get("status") == "unknown":
                            break
                        await asyncio.sleep(0.01)
                    self.assertEqual(retained["action"]["result"]["status"],
                                     "unknown", retained)
                    self.assertFalse(retained["action"]["release_confirmed"])
                    self.assertEqual(retained["cancellation"]["status"],
                                     "unknown")
                    self.assertTrue(retained["cancellation"][
                        "automatic_completion_recovery"])
                    self.assertIsNone(retained["task_success"])
                    self.assertFalse(retained["replay_allowed"])
                    action = retained["action"]
                    obligations = derive_input_obligations(program)
                    custody = {
                        "classification": "UNKNOWN_RELEASE_UNCONFIRMED_STOPPED",
                        "operation_id": action["operation_id"],
                        "target_generation": action["target_generation"],
                        "obligations": obligations,
                        "do_not_replay": True,
                        "observed_producer_live": False,
                        "late_server_request_possible": True,
                        "dispatch": {"input_dispatched": None,
                            "release_confirmed": False, "task_success": None,
                            "replay_allowed": False}}

            recovery_output = Path(root) / "recovery-receipts"
            recovery_params = StdioServerParameters(command=sys.executable,
                args=["-m", "runtime.cli_v1.mcp_supervised_stdio_test_server",
                      "--output-directory", str(recovery_output), "--mode", "recovery",
                      "--recovery-generation", recovery_generation],
                cwd=str(Path(__file__).resolve().parents[2]))
            async with stdio_client(recovery_params) as (reader, writer):
                async with ClientSession(reader, writer) as client:
                    await client.initialize()
                    reply = await client.call_tool("interface_recover_orphaned_input", {
                        "source_operation_id": action["operation_id"],
                        "source_target_generation": action["target_generation"],
                        "recovery_target_generation": recovery_generation,
                        "obligations": obligations,
                        "source_custody_record": custody})
                    recovered = self.row(reply)
                    self.assertEqual(recovered["status"], "recovered", recovered)
                    self.assertEqual(recovered["source_action_status"], "unknown")
                    self.assertTrue(recovered["release_confirmed"])
                    self.assertTrue(recovered["recovery_receipt"][
                        "late_input_horizon_verified"])
                    self.assertEqual(recovered["recovery_receipt"][
                        "late_input_horizon_ns"], 2_000_000_000)
                    self.assertIsNone(recovered["task_success"])
                    self.assertFalse(recovered["replay_allowed"])
                    self.assertTrue(recovered["next_action_requires_fresh_generation"])


    async def test_stdio_exception_auto_recovers_and_keeps_action_unknown(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        with TemporaryDirectory() as root:
            output = Path(root) / "source-receipts"
            params = StdioServerParameters(command=sys.executable,
                args=["-m", "runtime.cli_v1.mcp_supervised_stdio_test_server",
                      "--output-directory", str(output), "--mode", "exception"],
                cwd=str(Path(__file__).resolve().parents[2]))
            async with stdio_client(params) as (reader, writer):
                async with ClientSession(reader, writer) as client:
                    await client.initialize()
                    reply = await client.call_tool("interface_dispatch", {
                        "program": self.valid_program(),
                        "current_observation_seq": 1,
                        "current_binding_revision": 1,
                        "wait_for_result_ms": 5000})
                    result = self.row(reply)
                    self.assertEqual(result["status"], "returned", result)
                    self.assertEqual(result["result"]["status"], "unknown")
                    self.assertTrue(result["release_confirmed"])
                    self.assertIsNone(result["input_dispatched"])
                    self.assertIsNone(result["task_success"])
                    self.assertFalse(result["replay_allowed"])
                    action = result["supervision"]["action"]
                    cancellation = result["supervision"]["cancellation"]
                    self.assertEqual(action["status"], "unknown")
                    self.assertFalse(action["release_confirmed"])
                    self.assertEqual(action["result"]["error"],
                                     "COMPLETION_EVIDENCE_UNCONFIRMED")
                    self.assertTrue(cancellation[
                        "automatic_completion_recovery"])
                    self.assertEqual(cancellation["status"], "recovered")
                    self.assertTrue(cancellation["release_confirmed"])
                    # Exact-call interface_results returns the retained owner
                    # row directly. Its result-query envelope lives outside
                    # that row in the actual MCP call response.
                    results_reply = await client.call_tool(
                        "interface_results", {
                            "call_id": result["call_id"],
                            "include_image": False})
                    self.assertFalse(results_reply.isError)
                    self.assertEqual(len(results_reply.content), 1)
                    self.assertEqual(results_reply.content[0].type, "text")
                    public_result_body = json.loads(
                        results_reply.content[0].text)
                    self.assertEqual(public_result_body["call_id"],
                                     result["call_id"])
                    self.assertEqual(public_result_body["action"]["status"],
                                     "unknown")
                    retained = self.row(results_reply)
                    self.assertEqual(retained["action"]["status"], "unknown")
                    self.assertFalse(retained["action"][
                        "release_confirmed"])
                    self.assertTrue(retained["cancellation"][
                        "automatic_completion_recovery"])
                    self.assertEqual(retained["cancellation"]["status"],
                                     "recovered")
                    self.assertTrue(retained["cancellation"][
                        "release_confirmed"])
                    self.assertIsNone(retained["task_effect"])
                    # This fake supervisor omits the required bounded late
                    # input horizon. The compiled caller must not treat its
                    # release boolean alone as verified recovery custody.
                    from runtime.cli_v1.supervised_win32_compiled import _terminal
                    terminal = _terminal(public_result_body, "move",
                        expected_call_id=result["call_id"],
                        expected_generation=result["target_generation"])
                    self.assertEqual(terminal["status"], "uncertain")
                    self.assertIs(terminal["release"]["verified"], False)
                    self.assertNotIn("input_dispatched", terminal)
                    # The public caller consumes the decoded text body. Passing
                    # the MCP SDK response object is not the caller contract.
                    sdk_terminal = _terminal(results_reply, "move",
                        expected_call_id=result["call_id"],
                        expected_generation=result["target_generation"])
                    self.assertEqual(sdk_terminal["status"], "uncertain")
                    self.assertFalse(sdk_terminal["release"]["verified"])
                    await client.call_tool("interface_close", {})


if __name__ == "__main__":
    unittest.main()
