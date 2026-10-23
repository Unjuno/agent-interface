"""Public MCP composition checks for the synthetic guarded-Win32 route."""
import tempfile
import unittest
import json
import time
import asyncio
import threading
import multiprocessing
from unittest.mock import Mock, patch

from runtime.cli_v1.mcp_server import create_server
from runtime.guarded_win32_v1.operation_owner import OperationOwner
from runtime.cli_v1.owned_win32_session import OwnedWin32SessionOwner
from runtime.guarded_win32_v1.process_cancellation import OperationCancellationSupervisor
from runtime.guarded_win32_v1.test_process_cancellation import (
    _fake_readback_worker, _fake_recovery_worker,
)


class GatedSyntheticProcess:
    def __init__(self, pid):
        self._requested_pid = pid
        self.pid = None
        self.exitcode = None
        self.alive = False

    def start(self):
        self.pid = self._requested_pid
        self.alive = True

    def is_alive(self):
        return self.alive

    def terminate(self):
        self.alive = False
        self.exitcode = -15

    def join(self, _timeout=None):
        return None

    def kill(self):
        self.alive = False
        self.exitcode = -9

    def close(self):
        return None


def _spawned_gate_producer(start_gate, down, task_done, started):
    if start_gate.wait(5):
        down.set()
        task_done.set()
        started.set()
        while True:
            time.sleep(0.01)


def _synthetic_task_effect_oracle(task_done, action, oracle_id, send):
    outcome = "success" if task_done.wait(5) else "unknown"
    send.send({
        "call_id": action["call_id"],
        "operation_id": action["operation_id"],
        "target_generation": action["target_generation"],
        "oracle_id": oracle_id,
        "outcome": outcome,
        "observed_monotonic_ns": time.monotonic_ns(),
        "evidence_ref": "synthetic-task-event:completed" if outcome == "success"
            else "synthetic-task-event:timeout",
    })
    send.close()


def _synthetic_process_identity(process):
    return {"pid": process.pid, "creation_time_100ns": id(process) or 1}


class GuardedWin32PublicRouteTests(unittest.IsolatedAsyncioTestCase):
    def test_route_requires_an_explicit_inert_owner_factory_and_one_target(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ValueError, "explicit injected owner factory"):
                create_server({"fixture": 123}, root, session_mode="guarded-win32")
            with self.assertRaisesRegex(ValueError, "exactly one"):
                create_server({"first": 123, "second": 456}, root,
                    session_mode="guarded-win32",
                    _guarded_win32_owner_factory=lambda *_args: None)

    def test_route_refuses_non_windows_before_calling_owner_factory(self):
        factory = Mock()
        with tempfile.TemporaryDirectory() as root, \
                patch("runtime.cli_v1.mcp_server.os.name", "posix"):
            with self.assertRaisesRegex(ValueError, "Windows host"):
                create_server({"fixture": 123}, root, session_mode="guarded-win32",
                    _guarded_win32_owner_factory=factory)
        factory.assert_not_called()

    async def test_guarded_win32_route_is_opt_in_and_exposes_its_own_tools(self):
        generation = "a" * 64

        class SyntheticSupervisor:
            def __init__(self, operation_owner):
                self.owner = operation_owner

            def producer_started(self, *args, **kwargs):
                return self.owner.producer_started(*args, **kwargs)

            def cancel(self, operation_id, target_generation, *, cleanup_deadline_ns):
                self.owner.request_cancel(operation_id, target_generation,
                    cleanup_deadline_ns=cleanup_deadline_ns)
                return self.owner.result(operation_id)

            def close(self):
                return None

        processes = {}

        def make_owner(*_args):
            gate = OperationOwner(clock_ns=time.monotonic_ns,
                process_identity_reader=lambda handle: processes.get(handle))
            adapter = OwnedWin32SessionOwner(gate, SyntheticSupervisor(gate))
            adapter.bind_target_generation_reader(lambda: generation)
            return adapter

        def make_producer(_action):
            process = GatedSyntheticProcess(4301)
            identity = {"pid": 4301, "creation_time_100ns": 9301}
            processes[process] = identity
            return process, identity, lambda: setattr(process, "authorized", True)

        with tempfile.TemporaryDirectory() as root:
            server = create_server(
                {"fixture": 123}, root, session_mode="guarded-win32",
                _guarded_win32_owner_factory=make_owner,
                _guarded_win32_producer_factory=make_producer)
            names = {tool.name for tool in await server.list_tools()}
            self.assertIn("interface_guarded_win32_admit", names)
            self.assertIn("interface_guarded_win32_start", names)
            self.assertIn("interface_guarded_win32_bind_target", names)
            self.assertIn("interface_guarded_win32_cancel", names)
            self.assertIn("interface_results", names)
            self.assertNotIn("interface_guarded_win32_verify_task", names)
            self.assertNotIn("interface_guarded_input", names)
            self.assertNotIn("interface_guarded_compiled", names)
            binding = json.loads((await server.call_tool(
                "interface_guarded_win32_bind_target", {})).content[0].text)
            result = await server.call_tool("interface_guarded_win32_admit", {
                "action_operation_id": "c" * 32,
                "target_binding_id": binding["target_binding_id"],
                "operation_deadline_ns": 9999999999999999999,
                "obligations": ["left_mouse_button"],
            })
            receipt = json.loads(result.content[0].text)
            self.assertEqual(receipt.get("status"), "admitted", receipt)
            self.assertFalse(receipt["input_dispatched"])
            self.assertIsNone(receipt["task_success"])
            call_id = receipt["call_id"]
            self.assertEqual(receipt["action"]["target_generation"], generation)
            rejected = await server.call_tool("interface_guarded_win32_admit", {
                "action_operation_id": "d" * 32,
                "target_generation": "f" * 64,
                "target_binding_id": "f" * 32,
                "operation_deadline_ns": time.monotonic_ns() + 2_000_000_000,
                "obligations": ["left_mouse_button"],
            })
            self.assertTrue(rejected.isError)
            self.assertIn("target_generation", json.loads(rejected.content[0].text)["unknown_arguments"])
            listed = json.loads((await server.call_tool("interface_results", {})).content[0].text)
            self.assertEqual(listed["total_calls"], 1)
            self.assertEqual(listed["calls"][0]["call_id"], call_id)
            lookup = json.loads((await server.call_tool("interface_results", {
                "call_id": call_id})).content[0].text)
            self.assertEqual(lookup["action"]["status"], "admitted")
            started = json.loads((await server.call_tool(
                "interface_guarded_win32_start", {
                    "call_id": call_id, "wait_for_result_ms": 1000})).content[0].text)
            self.assertEqual(started["status"], "running")
            self.assertTrue(next(iter(processes)).authorized)
            canceled = json.loads((await server.call_tool(
                "interface_guarded_win32_cancel", {
                    "call_id": call_id,
                    "cleanup_deadline_ns": time.monotonic_ns() + 2_000_000_000,
                })).content[0].text)
            self.assertEqual(canceled["status"], "pending")
            self.assertFalse(canceled["release_confirmed"])
            self.assertIsNone(canceled["task_success"])
            retained = json.loads((await server.call_tool("interface_results", {
                "call_id": call_id})).content[0].text)
            self.assertEqual(retained["action"]["status"], "running")
            self.assertEqual(retained["cancellation"]["status"], "pending")

    async def test_target_generation_change_after_binding_refuses_admission(self):
        generation = ["a" * 64]

        class SyntheticSupervisor:
            def __init__(self, owner):
                self.owner = owner

            def producer_started(self, *args, **kwargs):
                return self.owner.producer_started(*args, **kwargs)

            def cancel(self, operation_id, target_generation, *, cleanup_deadline_ns):
                self.owner.request_cancel(operation_id, target_generation,
                    cleanup_deadline_ns=cleanup_deadline_ns)
                return self.owner.result(operation_id)

            def close(self):
                return None

        def make_owner(*_args):
            gate = OperationOwner(clock_ns=time.monotonic_ns,
                process_identity_reader=lambda _handle: None)
            adapter = OwnedWin32SessionOwner(gate, SyntheticSupervisor(gate))
            adapter.bind_target_generation_reader(lambda: generation[0])
            return adapter

        with tempfile.TemporaryDirectory() as root:
            server = create_server({"fixture": 123}, root,
                session_mode="guarded-win32", _guarded_win32_owner_factory=make_owner,
                _guarded_win32_producer_factory=lambda _action: None)
            binding = json.loads((await server.call_tool(
                "interface_guarded_win32_bind_target", {})).content[0].text)
            self.assertEqual(binding["status"], "bound")
            generation[0] = "b" * 64  # model wait / caller delay
            refused = await server.call_tool("interface_guarded_win32_admit", {
                "action_operation_id": "e" * 32,
                "target_binding_id": binding["target_binding_id"],
                "operation_deadline_ns": time.monotonic_ns() + 2_000_000_000,
                "obligations": ["left_mouse_button"],
            })
            refusal = json.loads(refused.content[0].text)
            self.assertTrue(refused.isError)
            self.assertEqual(refusal["error"], "TARGET_GENERATION_CHANGED")
            listed = json.loads((await server.call_tool("interface_results", {})).content[0].text)
            self.assertEqual(listed["total_calls"], 0)

    async def test_public_cancel_during_blocked_factory_keeps_late_child_gated(self):
        generation = "a" * 64
        factory_entered, factory_release, factory_returned = (
            threading.Event(), threading.Event(), threading.Event())
        start_gate = threading.Event()
        processes = {}
        adapters = []

        class SyntheticSupervisor:
            def __init__(self, owner):
                self.owner = owner

            def producer_started(self, *args, **kwargs):
                return self.owner.producer_started(*args, **kwargs)

            def cancel(self, operation_id, target_generation, *, cleanup_deadline_ns):
                self.owner.request_cancel(operation_id, target_generation,
                    cleanup_deadline_ns=cleanup_deadline_ns)
                return self.owner.result(operation_id)

            def close(self):
                return None

        def make_owner(*_args):
            gate = OperationOwner(clock_ns=time.monotonic_ns,
                process_identity_reader=lambda process: processes.get(process))
            adapter = OwnedWin32SessionOwner(gate, SyntheticSupervisor(gate))
            adapter.bind_target_generation_reader(lambda: generation)
            adapters.append(adapter)
            return adapter

        def blocked_factory(_action):
            factory_entered.set()
            try:
                if not factory_release.wait(2):
                    raise RuntimeError("test factory deadline")
                process = GatedSyntheticProcess(4401)
                identity = {"pid": 4401, "creation_time_100ns": 9401}
                processes[process] = identity
                return process, identity, start_gate.set
            finally:
                factory_returned.set()

        with tempfile.TemporaryDirectory() as root:
            server = create_server({"fixture": 123}, root,
                session_mode="guarded-win32", _guarded_win32_owner_factory=make_owner,
                _guarded_win32_producer_factory=blocked_factory)
            binding = json.loads((await server.call_tool(
                "interface_guarded_win32_bind_target", {})).content[0].text)
            admitted = json.loads((await server.call_tool(
                "interface_guarded_win32_admit", {
                    "action_operation_id": "f" * 32,
                    "target_binding_id": binding["target_binding_id"],
                    "operation_deadline_ns": time.monotonic_ns() + 5_000_000_000,
                    "obligations": ["key:a"],
                })).content[0].text)
            call_id = admitted["call_id"]
            pending = json.loads((await server.call_tool(
                "interface_guarded_win32_start", {
                    "call_id": call_id, "wait_for_result_ms": 0,
                })).content[0].text)
            self.assertEqual(pending["status"], "pending")
            self.assertTrue(await asyncio.to_thread(factory_entered.wait, 1))
            cancel = json.loads((await server.call_tool(
                "interface_guarded_win32_cancel", {
                    "call_id": call_id,
                    "cleanup_deadline_ns": time.monotonic_ns() + 2_000_000_000,
                })).content[0].text)
            self.assertEqual(cancel["status"], "pending")
            factory_release.set()
            self.assertTrue(await asyncio.to_thread(factory_returned.wait, 1))
            for _ in range(100):
                current = adapters[0].interface_result(call_id)
                if current["action"]["status"] == "cancel_pending":
                    break
                await asyncio.sleep(0.005)
            self.assertEqual(current["action"]["status"], "cancel_pending")
            self.assertFalse(start_gate.is_set())
            process = next(iter(processes))
            self.assertTrue(process.is_alive())
            process.terminate()
            process.join(0.1)
            self.assertTrue(adapters[0]._owner.producer_retired(
                "f" * 32, generation, process))
            process.close()

    async def test_public_cancel_composes_spawned_recovery_and_independent_readback(self):
        context = multiprocessing.get_context("spawn")
        down, neutral, task_done, producer_started = (
            context.Event(), context.Event(), context.Event(), context.Event())
        child_handles = []
        adapter_holder = []
        generation = "a" * 64

        def make_owner(*_args):
            gate = OperationOwner(clock_ns=time.monotonic_ns,
                process_identity_reader=_synthetic_process_identity)

            def recovery_factory(request, start_gate):
                receive, send = context.Pipe(duplex=False)
                process = context.Process(target=_fake_recovery_worker,
                    args=(down, neutral, start_gate, send, request))
                child_handles.append((process, receive, send))
                return process, receive

            def observer_factory(request):
                receive, send = context.Pipe(duplex=False)
                process = context.Process(target=_fake_readback_worker,
                    args=(neutral, request, send))
                child_handles.append((process, receive, send))
                return process, receive

            supervisor = OperationCancellationSupervisor(gate,
                recovery_process_factory=recovery_factory,
                observer_process_factory=observer_factory,
                process_identity_reader=_synthetic_process_identity)
            adapter = OwnedWin32SessionOwner(gate, supervisor)
            adapter.bind_target_generation_reader(lambda: generation)
            adapter_holder.append(adapter)
            return adapter

        def producer_factory(_action):
            start_gate = context.Event()
            process = context.Process(target=_spawned_gate_producer,
                args=(start_gate, down, task_done, producer_started))
            child_handles.append((process, None, None))
            return process, lambda: _synthetic_process_identity(process), start_gate.set

        def task_oracle(action):
            receive, send = context.Pipe(duplex=False)
            process = context.Process(target=_synthetic_task_effect_oracle,
                args=(task_done, action, "b" * 32, send))
            child_handles.append((process, receive, send))
            process.start()
            try:
                if not receive.poll(3):
                    raise TimeoutError("synthetic task oracle deadline")
                return receive.recv()
            finally:
                process.join(1)

        with tempfile.TemporaryDirectory() as root:
            server = create_server({"fixture": 123}, root,
                session_mode="guarded-win32", _guarded_win32_owner_factory=make_owner,
                _guarded_win32_producer_factory=producer_factory,
                _guarded_win32_task_oracle=task_oracle)
            try:
                names = {tool.name for tool in await server.list_tools()}
                self.assertIn("interface_guarded_win32_verify_task", names)
                binding = json.loads((await server.call_tool(
                    "interface_guarded_win32_bind_target", {})).content[0].text)
                admitted = json.loads((await server.call_tool(
                    "interface_guarded_win32_admit", {
                        "action_operation_id": "9" * 32,
                        "target_binding_id": binding["target_binding_id"],
                        "operation_deadline_ns": time.monotonic_ns() + 10_000_000_000,
                        "obligations": ["key:a"],
                    })).content[0].text)
                call_id = admitted["call_id"]
                started = json.loads((await server.call_tool(
                    "interface_guarded_win32_start", {
                        "call_id": call_id, "wait_for_result_ms": 2000,
                    })).content[0].text)
                self.assertEqual(started["status"], "running")
                self.assertTrue(await asyncio.to_thread(producer_started.wait, 5))
                self.assertTrue(down.is_set())

                effect = json.loads((await server.call_tool(
                    "interface_guarded_win32_verify_task", {
                        "call_id": call_id, "wait_for_result_ms": 3000,
                    })).content[0].text)
                self.assertEqual(effect["status"], "verified", effect)
                self.assertTrue(effect["task_success"])
                self.assertEqual(effect["task_effect"]["receipt"]["oracle_id"], "b" * 32)

                before_cancel = time.monotonic_ns()
                cancel = json.loads((await server.call_tool(
                    "interface_guarded_win32_cancel", {
                        "call_id": call_id,
                        "cleanup_deadline_ns": time.monotonic_ns() + 5_000_000_000,
                    })).content[0].text)
                elapsed_ms = (time.monotonic_ns() - before_cancel) / 1_000_000
                self.assertLess(elapsed_ms, 500, cancel)
                self.assertIn(cancel["status"], ("pending", "recovered"), cancel)
                if cancel["status"] == "pending":
                    self.assertFalse(cancel["release_confirmed"])
                else:
                    self.assertTrue(cancel["release_confirmed"])
                self.assertIsNone(cancel["task_success"])

                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    retained = json.loads((await server.call_tool(
                        "interface_results", {"call_id": call_id})).content[0].text)
                    if retained["cancellation"]["status"] in ("recovered", "unknown"):
                        break
                    await asyncio.sleep(0.01)
                cancellation = retained["cancellation"]
                self.assertEqual(cancellation["status"], "recovered", retained)
                self.assertTrue(cancellation["release_confirmed"])
                self.assertIsNone(cancellation["task_success"])
                self.assertFalse(cancellation["replay_allowed"])
                self.assertEqual(retained["action"]["status"], "running")
                self.assertTrue(retained["task_success"])
                self.assertTrue(retained["task_effect"]["task_success"])
                self.assertIsNone(retained["cancellation"]["task_success"])
                self.assertFalse(down.is_set())
                self.assertTrue(neutral.is_set())
                self.assertIsInstance(cancellation["result"]["producer_exit_code"], int)
            finally:
                if adapter_holder:
                    adapter_holder[0].close()
                for process, receive, send in child_handles:
                    try:
                        if process.is_alive():
                            process.terminate()
                            process.join(2)
                    except (OSError, ValueError):
                        pass
                    for connection in (receive, send):
                        if connection is not None:
                            try:
                                connection.close()
                            except OSError:
                                pass
                    try:
                        process.close()
                    except (OSError, ValueError):
                        pass


if __name__ == "__main__":
    unittest.main()
