"""Public MCP through the actual Win32 session/backend, with inert APIs only.

These tests catch lost caller custody/identity, duplicate producer admission,
recovery before exact producer retirement, and promotion of release to task
success. They do not exercise native Windows APIs or a live application.
"""
import asyncio
import json
import multiprocessing
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock

from runtime.backends.win32_v1.backend import VK_CONTROL, Win32Backend
from runtime.backends.win32_v1.test_supervised_session import (
    RetainedProcess, _identity, _producer_session, _recovery_observer_server,
)
from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.owned_win32_session import OwnedWin32SessionOwner
from runtime.guarded_win32_v1.operation_owner import OperationOwner
from runtime.guarded_win32_v1.process_cancellation import OperationCancellationSupervisor


class StartableRetainedProcess(RetainedProcess):
    def start(self):
        self.process.start()


class TracedHelperConnection:
    def __init__(self, connection, role, events):
        self.connection, self.role, self.events = connection, role, events

    def send(self, value):
        self.connection.send(value)

    def recv(self):
        request = self.connection.recv()
        if request is not None:
            self.events.append({"kind": self.role + "_request",
                                "request": request, "pid": os.getpid()})
        return request


def _traced_helper(connection, role, state, events):
    _recovery_observer_server(
        TracedHelperConnection(connection, role, events), role, state, events)


def _caller_producer(action, start_gate, state, events, entered, accept):
    if not start_gate.wait(5):
        return
    events.append({"kind": "producer_authorized", "action": action,
                   "pid": os.getpid()})
    _producer_session(start_gate, state, events, entered, accept)


class GuardedWin32BackendCompositionTests(unittest.IsolatedAsyncioTestCase):
    async def test_public_mcp_rejects_changed_window_thread_before_operation_creation(self):
        """Compose native identity reads through the public route with fake APIs."""
        with tempfile.TemporaryDirectory() as root:
            backend = object.__new__(Win32Backend)
            backend.targets = {"fixture": 123}
            backend.user32 = Mock()
            backend.user32.IsWindow.return_value = True
            backend.user32.GetPropW.return_value = 1234
            backend._window_owner_identity_for_hwnd = Mock(return_value={
                "pid": 5101, "creation_time_100ns": 7001,
                "window_thread_id": 701})
            process_factory_calls = []

            class Supervisor:
                def cancel(self, *_args, **_kwargs):
                    raise AssertionError("cancel is outside this admission test")

                def producer_started(self, *_args, **_kwargs):
                    raise AssertionError("producer start is outside this admission test")

                def close(self):
                    return None

            owner = None

            def owner_factory(*_args):
                nonlocal owner
                operation_owner = OperationOwner(clock_ns=time.monotonic_ns,
                    process_identity_reader=_identity)
                owner = OwnedWin32SessionOwner(operation_owner, Supervisor())
                owner.bind_target_generation_reader(
                    lambda: backend.target_generation("fixture"))
                return owner

            def producer_factory(action):
                process_factory_calls.append(action)
                raise AssertionError("generation refusal must precede producer factory")

            server = create_server({"fixture": 123}, root,
                session_mode="guarded-win32",
                _guarded_win32_owner_factory=owner_factory,
                _guarded_win32_producer_factory=producer_factory)

            async def call(name, **arguments):
                response = await server.call_tool(name, arguments)
                return response, json.loads(response.content[0].text)

            try:
                _, binding = await call("interface_guarded_win32_bind_target")
                self.assertEqual(binding["status"], "bound")
                # Model numeric HWND reuse by another thread in the same process.
                backend._window_owner_identity_for_hwnd.return_value["window_thread_id"] = 702
                response, result = await call("interface_guarded_win32_admit",
                    action_operation_id="d" * 32,
                    target_binding_id=binding["target_binding_id"],
                    operation_deadline_ns=time.monotonic_ns() + 5_000_000_000,
                    obligations=["key:CTRL"])

                self.assertTrue(response.isError)
                self.assertEqual(result["error"], "TARGET_GENERATION_CHANGED")
                self.assertFalse(result["operation_invoked"])
                self.assertFalse(result["input_dispatched"])
                self.assertEqual(owner._calls, {})
                self.assertEqual(owner._owner._records, {})
                self.assertEqual(process_factory_calls, [])
            finally:
                owner.close()

    async def _run_case(self, *, accept, stubborn=False, cancel_before_gate=False):
        context = multiprocessing.get_context("spawn")
        with context.Manager() as manager, tempfile.TemporaryDirectory() as root:
            state, events = manager.dict(), manager.list()
            entered, start_gate = context.Event(), context.Event()
            helpers, producers, adapters, factory_calls, supervisors = [], [], [], [], []
            generation, operation_id = "c" * 64, "d" * 32
            query_entered, query_release = threading.Event(), threading.Event()
            start_task = None

            def read_generation():
                if cancel_before_gate and producers:
                    query_entered.set()
                    if not query_release.wait(8):
                        raise TimeoutError("test generation query timeout")
                return generation

            def helper_factory(role):
                parent, child = context.Pipe(duplex=True)
                process = context.Process(target=_traced_helper,
                    args=(child, role, state, events), daemon=True)
                helpers.append((process, parent, child))
                return process, parent

            def owner_factory(*_args):
                gate = OperationOwner(clock_ns=time.monotonic_ns,
                                      process_identity_reader=_identity)
                supervisor = OperationCancellationSupervisor(gate,
                    recovery_process_factory=lambda: helper_factory("recovery"),
                    observer_process_factory=lambda: helper_factory("observer"),
                    process_identity_reader=_identity,
                    terminate_grace_s=0.05, kill_grace_s=0.05)
                supervisors.append(supervisor)
                adapter = OwnedWin32SessionOwner(gate, supervisor)
                adapter.bind_target_generation_reader(read_generation)
                adapters.append(adapter)
                return adapter

            def producer_factory(action):
                factory_calls.append(action["operation_id"])
                process = context.Process(target=_caller_producer,
                    args=(action, start_gate, state, events, entered, accept), daemon=True)
                producers.append(process)
                retained = StartableRetainedProcess(process, events, stubborn=stubborn)
                return retained, lambda: _identity(retained), start_gate.set

            try:
                server = create_server({"fixture": 123}, root,
                    session_mode="guarded-win32",
                    _guarded_win32_owner_factory=owner_factory,
                    _guarded_win32_producer_factory=producer_factory)

                async def call(name, **arguments):
                    response = await server.call_tool(name, arguments)
                    return json.loads(response.content[0].text)

                self.assertEqual(len(helpers), 2)
                helper_pids = [process.pid for process, _, _ in helpers]
                self.assertTrue(all(process.is_alive() for process, _, _ in helpers))
                binding = await call("interface_guarded_win32_bind_target")
                admitted = await call("interface_guarded_win32_admit",
                    action_operation_id=operation_id,
                    target_binding_id=binding["target_binding_id"],
                    operation_deadline_ns=time.monotonic_ns() + 15_000_000_000,
                    obligations=["key:CTRL"])
                call_id = admitted["call_id"]
                start_task = asyncio.create_task(call("interface_guarded_win32_start",
                    call_id=call_id, wait_for_result_ms=10000))
                if cancel_before_gate:
                    self.assertTrue(await asyncio.to_thread(query_entered.wait, 5))
                    self.assertFalse(start_gate.is_set())
                    self.assertFalse(entered.is_set())
                else:
                    started = await start_task
                    self.assertEqual(started["status"], "running", started)
                    self.assertTrue(await asyncio.to_thread(entered.wait, 5))
                    self.assertEqual(bool(state.get(VK_CONTROL, False)), accept)
                await call("interface_guarded_win32_start",
                    call_id=call_id, wait_for_result_ms=2000)
                self.assertEqual(factory_calls, [operation_id])

                cancel = await call("interface_guarded_win32_cancel", call_id=call_id,
                    cleanup_deadline_ns=time.monotonic_ns() + 5_000_000_000)
                duplicate = await call("interface_guarded_win32_cancel", call_id=call_id,
                    cleanup_deadline_ns=time.monotonic_ns() + 5_000_000_000)
                self.assertEqual(duplicate["operation_id"], cancel["operation_id"])
                deadline = time.monotonic() + 6
                while True:
                    result = await call("interface_results", call_id=call_id)
                    cancellation = result["cancellation"]
                    if cancellation["status"] in ("recovered", "unknown"):
                        break
                    self.assertLess(time.monotonic(), deadline, result)
                    await asyncio.sleep(0.005)

                self.assertIsNone(result["task_success"])
                self.assertIsNone(result["task_effect"])
                self.assertFalse(cancellation["replay_allowed"])
                self.assertIsNone(cancellation["task_success"])
                self.assertEqual([process.pid for process, _, _ in helpers], helper_pids)
                trace = list(events)
                trace_dir = os.environ.get("WIN32_COMPOSITION_TRACE_DIR")
                if trace_dir:
                    path = Path(trace_dir)
                    path.mkdir(parents=True, exist_ok=True)
                    (path / (self._testMethodName + ".json")).write_text(json.dumps({
                        "scope": "synthetic_only", "accept_before_block": accept,
                        "stubborn_producer": stubborn, "cancel_before_gate": cancel_before_gate,
                        "result": result, "events": trace, "helper_pids": helper_pids,
                        "producer_factory_calls": factory_calls,
                    }, indent=2) + "\n", encoding="utf-8")
                if cancel_before_gate:
                    self.assertEqual(cancellation["status"], "unknown", result)
                    self.assertFalse(cancellation["release_confirmed"])
                    self.assertFalse(producers[0].is_alive())
                    self.assertFalse(start_gate.is_set())
                    self.assertEqual(cancellation["result"]["producer_gate_state"], "closed")
                    self.assertEqual([row["kind"] for row in trace],
                                     ["producer_exit_confirmed"])
                    query_release.set()
                    await start_task
                    self.assertFalse(start_gate.is_set())
                    return
                authorization = next(row for row in trace
                                     if row["kind"] == "producer_authorized")
                self.assertEqual(authorization["action"]["operation_id"], operation_id)
                self.assertEqual(authorization["action"]["target_generation"], generation)
                self.assertEqual(result["call_id"], call_id)
                self.assertEqual(result["action"]["operation_id"], operation_id)
                self.assertEqual(cancellation["action_operation_id"], operation_id)
                self.assertEqual(authorization["pid"], producers[0].pid)
                kinds = [row["kind"] for row in trace]
                if stubborn:
                    self.assertEqual(cancellation["status"], "unknown", result)
                    self.assertFalse(cancellation["release_confirmed"])
                    self.assertTrue(producers[0].is_alive())
                    self.assertTrue(state.get(VK_CONTROL, False))
                    self.assertNotIn("recovery_request", kinds)
                    self.assertNotIn("recovery_up", kinds)
                    self.assertNotIn("observer_request", kinds)
                else:
                    self.assertEqual(cancellation["status"], "recovered", result)
                    self.assertTrue(cancellation["release_confirmed"])
                    self.assertFalse(producers[0].is_alive())
                    self.assertFalse(state.get(VK_CONTROL, False))
                    self.assertLess(kinds.index("producer_exit_confirmed"),
                                    kinds.index("recovery_up"))
                    self.assertLess(kinds.index("recovery_up"),
                                    kinds.index("observer_request"))
                    self.assertEqual(kinds.count("recovery_up"), 1)
                    requests = [row for row in trace if row["kind"] in
                                ("recovery_request", "observer_request")]
                    self.assertEqual(len(requests), 2)
                    for row in requests:
                        self.assertEqual(row["request"]["operation_id"], operation_id)
                        self.assertEqual(row["request"]["target_generation"], generation)
                        self.assertEqual(row["request"]["obligations"], ["key:CTRL"])
                    self.assertNotEqual(requests[0]["pid"], requests[1]["pid"])
                    self.assertEqual(requests[0]["request"]["recovery_id"],
                                     requests[1]["request"]["recovery_id"])
            finally:
                query_release.set()
                if start_task is not None:
                    await start_task
                for adapter in adapters:
                    adapter.close()
                # UNKNOWN intentionally keeps the adapter busy; reclaim test helpers
                # without promoting that operation's retained result to clean/closed.
                for supervisor in supervisors:
                    supervisor.close()
                for process in producers + [row[0] for row in helpers]:
                    try:
                        if process.is_alive():
                            process.terminate()
                            process.join(2)
                        self.assertFalse(process.is_alive(), "test child failed cleanup")
                        process.close()
                    except ValueError:
                        pass  # Supervisor may already have closed its helper handle.
                for _, parent, child in helpers:
                    parent.close()
                    child.close()

    async def test_public_caller_backend_block_before_acceptance(self):
        await self._run_case(accept=False)

    async def test_public_caller_backend_accept_before_return(self):
        await self._run_case(accept=True)

    async def test_public_caller_backend_unretired_producer_stays_unknown(self):
        await self._run_case(accept=True, stubborn=True)

    async def test_cancel_during_final_generation_read_sends_no_compensating_input(self):
        await self._run_case(accept=False, cancel_before_gate=True)


if __name__ == "__main__":
    unittest.main()
