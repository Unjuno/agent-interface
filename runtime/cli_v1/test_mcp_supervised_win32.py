import json
import time
import unittest
import asyncio
import threading
from tempfile import TemporaryDirectory
from pathlib import Path

from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.owned_win32_session import OwnedWin32SessionOwner
from runtime.guarded_win32_v1.operation_owner import OperationOwner


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
                "execution": {"program_emissions": 1}},
            "release_receipt": {"verified": True, "keys_down": [],
                "buttons_down": [], "keys_unknown": [], "buttons_unknown": []}}


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
            await server.call_tool("interface_close", {})
        self.assertTrue(supervisor.closed)

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
            await server.call_tool("interface_close", {})


if __name__ == "__main__":
    unittest.main()
