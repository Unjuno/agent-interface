"""Public supervised MCP composition with inert Win32 API boundaries."""
import asyncio
import json
import multiprocessing
import os
import tempfile
import time
import unittest

from runtime.backends.win32_v1.backend import VK_CONTROL, Win32Backend
from runtime.backends.win32_v1.session import Win32RuntimeSession
from runtime.backends.win32_v1.test_supervised_session import (
    FakeUser32, RetainedProcess, _identity, _recovery_observer_server,
)
from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.owned_win32_session import OwnedWin32SessionOwner
from runtime.guarded_win32_v1.operation_owner import OperationOwner
from runtime.guarded_win32_v1.process_cancellation import OperationCancellationSupervisor


GENERATION = "a" * 64


class StartableRetainedProcess(RetainedProcess):
    def start(self):
        self.process.start()


class TracedHelperConnection:
    def __init__(self, connection, role, events):
        self.connection = connection
        self.role = role
        self.events = events

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


class BlockedProducerFactory:
    def __init__(self, context, state, events, entered, start_gate, producers):
        self.context = context
        self.state = state
        self.events = events
        self.entered = entered
        self.start_gate = start_gate
        self.producers = producers

    def __call__(self, action):
        process = self.context.Process(target=_supervised_backend_producer,
            args=(action, self.start_gate, self.state, self.events,
                  self.entered, True), daemon=True)
        self.producers.append(process)
        retained = StartableRetainedProcess(process, self.events)
        return retained, lambda: _identity(retained), self.start_gate.set

    def read_result(self, _process):
        raise AssertionError("cancelled producer must not yield a completion receipt")


def _supervised_backend_producer(action, start_gate, state, events, entered,
                                accept_before_block):
    if not start_gate.wait(5):
        return
    backend = Win32Backend.__new__(Win32Backend)
    backend.targets = {"fixture": 123}
    backend.user32 = FakeUser32(state, events, "producer", entered,
                                accept_before_block)
    backend.held_keys = {}
    backend.held_key_targets = {}
    backend.held_buttons = set()
    backend.held_button_targets = {}
    backend.focused_target = None
    backend.pending_unicode_ups = set()
    backend.emissions = 0
    backend._last_state_query_witness = []
    backend.manifest = lambda: Win32Backend.manifest(backend)
    backend.monotonic_ns = time.monotonic_ns
    backend.preflight = lambda *_args, **_kwargs: None
    backend.focus = lambda target: setattr(backend, "focused_target", target)
    backend.target_generation = lambda _target: action["target_generation"]
    session = Win32RuntimeSession(backend)
    program = action["program"]
    session.dispatch(program,
        current_observation_seq=program["source"]["observation_seq"],
        current_binding_revision=program["source"]["binding_revision"])


class SupervisedBackendCompositionTests(unittest.IsolatedAsyncioTestCase):
    async def test_public_cancel_recovers_after_actual_session_is_blocked_in_sendinput(self):
        context = multiprocessing.get_context("spawn")
        with context.Manager() as manager, tempfile.TemporaryDirectory() as root:
            state, events = manager.dict(), manager.list()
            entered, start_gate = context.Event(), context.Event()
            helpers, producers = [], []
            server = None
            call_id = None
            operation_owner = OperationOwner(clock_ns=time.monotonic_ns,
                process_identity_reader=_identity)

            def helper_factory(role):
                parent, child = context.Pipe(duplex=True)
                process = context.Process(target=_traced_helper,
                    args=(child, role, state, events), daemon=True)
                helpers.append((process, parent, child))
                return process, parent

            supervisor = OperationCancellationSupervisor(operation_owner,
                recovery_process_factory=lambda: helper_factory("recovery"),
                observer_process_factory=lambda: helper_factory("observer"),
                process_identity_reader=_identity,
                terminate_grace_s=0.05, kill_grace_s=0.05)
            owner = OwnedWin32SessionOwner(operation_owner, supervisor,
                synthetic_only=False)
            owner.bind_target_generation_reader(lambda: GENERATION)

            def producer_factory(_targets, _output_directory, _display_name):
                return BlockedProducerFactory(context, state, events, entered,
                    start_gate, producers)

            server = create_server({"fixture": 123}, root,
                session_mode="supervised-win32",
                _supervised_win32_owner_factory=lambda *_args: owner,
                _supervised_win32_producer_factory=producer_factory)

            def row(reply):
                result = json.loads(reply.content[0].text)
                source = (result.get("receipt", {}).get("source", {})
                          if isinstance(result.get("receipt"), dict) else {})
                raw = source.get("raw_report") if isinstance(source, dict) else None
                return raw if isinstance(raw, dict) else result

            program = {
                "schema": "agent-interface/program-v1",
                "program_id": "blocked-sendinput-public-cancel",
                "source": {"observation_seq": 1, "binding_revision": 1,
                    "target_generations": {"fixture": GENERATION}},
                "authority": {"lease_id": "blocked-sendinput-public-cancel",
                    "expires_at_ns": time.monotonic_ns() + 10_000_000_000},
                "terminal": {"release_all_required": True},
                "ops": [{"op": "focus", "target": "fixture"},
                    {"op": "key_state", "key": "CTRL", "down": True},
                    {"op": "release_all"}],
            }
            try:
                self.assertEqual(len(helpers), 2)
                dispatched = row(await server.call_tool("interface_dispatch", {
                    "program": program,
                    "current_observation_seq": 1,
                    "current_binding_revision": 1,
                    "wait_for_result_ms": 0}))
                call_id = dispatched.get("call_id")
                self.assertEqual(dispatched["status"], "pending", dispatched)
                self.assertTrue(await asyncio.wait_for(
                    asyncio.to_thread(entered.wait, 5), 5))
                self.assertTrue(state.get(VK_CONTROL, False))
                cancel_started_ns = time.perf_counter_ns()
                cancelled = row(await server.call_tool("interface_cancel", {
                    "call_id": call_id}))
                cancel_returned_ns = time.perf_counter_ns()
                self.assertIn(cancelled["status"], ("pending", "recovered"), cancelled)
                deadline = time.monotonic() + 6
                while True:
                    retained = row(await server.call_tool("interface_results", {
                        "call_id": call_id}))
                    if retained["cancellation"]["status"] in ("recovered", "unknown"):
                        break
                    self.assertLess(time.monotonic(), deadline, retained)
                    await asyncio.sleep(0.01)

                cancellation = retained["cancellation"]
                recovery_confirmed_ns = time.perf_counter_ns()
                self.assertEqual(cancellation["status"], "recovered", retained)
                self.assertTrue(cancellation["release_confirmed"], retained)
                self.assertFalse(cancellation["replay_allowed"], retained)
                self.assertIsNone(retained["task_success"], retained)
                self.assertLess(cancel_returned_ns - cancel_started_ns,
                                3_000_000_000)
                self.assertLess(recovery_confirmed_ns - cancel_started_ns,
                                3_000_000_000)
                self.assertFalse(state.get(VK_CONTROL, False))
                trace = list(events)
                kinds = [event["kind"] for event in trace]
                self.assertIn("producer_down_entered", kinds)
                self.assertIn("producer_exit_confirmed", kinds)
                self.assertIn("recovery_up", kinds)
                self.assertLess(kinds.index("producer_exit_confirmed"),
                                kinds.index("recovery_up"), trace)
                self.assertLess(kinds.index("recovery_up"),
                                kinds.index("observer_request"), trace)
                self.assertEqual(kinds.count("recovery_up"), 1, trace)
                requests = [event for event in trace
                    if event["kind"] in ("recovery_request", "observer_request")]
                self.assertEqual(len(requests), 2, trace)
                self.assertNotEqual(requests[0]["pid"], requests[1]["pid"], trace)
                self.assertEqual(requests[0]["request"]["operation_id"],
                                 requests[1]["request"]["operation_id"], trace)
                self.assertEqual(requests[0]["request"]["target_generation"],
                                 GENERATION)
                close_deadline = time.monotonic() + 3
                while True:
                    closed = row(await server.call_tool("interface_close", {}))
                    if closed["status"] == "closed":
                        break
                    self.assertEqual(closed["status"], "busy", closed)
                    self.assertLess(time.monotonic(), close_deadline, closed)
                    await asyncio.sleep(0.02)
            finally:
                if server is not None:
                    if call_id is not None:
                        try:
                            await server.call_tool("interface_cancel", {
                                "call_id": call_id})
                            recovery_deadline = time.monotonic() + 6
                            while time.monotonic() < recovery_deadline:
                                latest = row(await server.call_tool(
                                    "interface_results", {"call_id": call_id}))
                                status = latest.get("cancellation", {}).get("status")
                                if status in ("recovered", "unknown"):
                                    break
                                await asyncio.sleep(0.01)
                        except Exception:
                            pass
                    close_deadline = time.monotonic() + 3
                    while time.monotonic() < close_deadline:
                        try:
                            latest_close = row(await server.call_tool(
                                "interface_close", {}))
                            if latest_close.get("status") == "closed":
                                break
                        except Exception:
                            break
                        await asyncio.sleep(0.02)
                if owner.state != "closed":
                    supervisor.close()
                for process in producers:
                    try:
                        if process.is_alive():
                            process.terminate()
                            process.join(2)
                        process.close()
                    except (OSError, ValueError):
                        pass
                for process, parent, child in helpers:
                    try:
                        if process.is_alive():
                            process.terminate()
                            process.join(2)
                        process.close()
                    except (OSError, ValueError):
                        pass
                    parent.close()
                    child.close()
                for process in producers:
                    try:
                        if process.is_alive():
                            process.terminate()
                            process.join(2)
                        process.close()
                    except (OSError, ValueError):
                        pass


if __name__ == "__main__":
    unittest.main()
