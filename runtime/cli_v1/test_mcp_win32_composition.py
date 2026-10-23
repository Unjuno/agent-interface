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
    _handle_blocked_observation,
    _handle_fake_observation, _handle_fake_recovery,
    _handle_wrong_recovery_receipt, _persistent_helper_factory,
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


def _spawned_gate_producer(start_gate, down, application_request, started):
    if start_gate.wait(5):
        down.set()
        application_request.set()
        started.set()
        while True:
            time.sleep(0.01)


def _synthetic_application_worker(application_request, application_completed,
                                  application_ready, stop):
    application_ready.set()
    if application_request.wait(5):
        application_completed.set()
    stop.wait(5)


def _synthetic_task_effect_oracle(application_completed, action, oracle_id, send):
    outcome = "success" if application_completed.wait(5) else "unknown"
    send.send({
        "call_id": action["call_id"],
        "operation_id": action["operation_id"],
        "target_generation": action["target_generation"],
        "oracle_id": oracle_id,
        "outcome": outcome,
        "observed_monotonic_ns": time.monotonic_ns(),
        "evidence_ref": "synthetic-application-state:completed" if outcome == "success"
            else "synthetic-application-state:timeout",
    })
    send.close()


def _synthetic_wrong_recovery_worker(start_gate, send, request):
    if start_gate.wait(3):
        send.send({
            "operation_id": "f" * 32,
            "target_generation": request["target_generation"],
            "recovery_id": request["recovery_id"],
            "release_accepted": True,
        })
    send.close()


def _synthetic_process_identity(process):
    return {"pid": process.pid, "creation_time_100ns": id(process) or 1}


class GuardedWin32PublicRouteTests(unittest.IsolatedAsyncioTestCase):
    async def test_public_task_oracle_rejects_stale_and_future_observation_times(self):
        from runtime.cli_v1.test_owned_win32_session import FakeCancellationSupervisor

        for observed in (1, 2**63):
            with self.subTest(observed=observed), tempfile.TemporaryDirectory() as root:
                adapters, oracle_calls = [], []

                def make_owner(*_args):
                    gate = OperationOwner(clock_ns=time.monotonic_ns,
                                          process_identity_reader=lambda _process: None)
                    adapter = OwnedWin32SessionOwner(gate, FakeCancellationSupervisor(gate))
                    adapter.bind_target_generation_reader(lambda: "a" * 64)
                    adapters.append(adapter)
                    return adapter

                def oracle(action):
                    oracle_calls.append(action["operation_id"])
                    return {"call_id": action["call_id"],
                            "operation_id": action["operation_id"],
                            "target_generation": action["target_generation"],
                            "oracle_id": "7" * 32, "outcome": "success",
                            "observed_monotonic_ns": observed,
                            "evidence_ref": "synthetic-stale-or-future-state"}

                server = create_server({"fixture": 123}, root, session_mode="guarded-win32",
                    _guarded_win32_owner_factory=make_owner,
                    _guarded_win32_producer_factory=lambda _action: None,
                    _guarded_win32_task_oracle=oracle)
                binding = json.loads((await server.call_tool(
                    "interface_guarded_win32_bind_target", {})).content[0].text)
                admitted = json.loads((await server.call_tool("interface_guarded_win32_admit", {
                    "action_operation_id": "6" * 32,
                    "target_binding_id": binding["target_binding_id"],
                    "operation_deadline_ns": time.monotonic_ns() + 5_000_000_000,
                    "obligations": [],
                })).content[0].text)
                result = json.loads((await server.call_tool("interface_guarded_win32_verify_task", {
                    "call_id": admitted["call_id"], "wait_for_result_ms": 1000,
                })).content[0].text)
                self.assertEqual(result["status"], "unknown", result)
                self.assertIsNone(result["task_success"])
                self.assertFalse(result["replay_allowed"])
                self.assertIn("outside the oracle request/receipt window",
                              result["task_effect"]["uncertainty"])
                retained = adapters[0].interface_result(admitted["call_id"])
                await server.call_tool("interface_guarded_win32_verify_task", {
                    "call_id": admitted["call_id"], "wait_for_result_ms": 1000})
                self.assertEqual(oracle_calls, ["6" * 32])
                self.assertEqual(adapters[0].interface_result(admitted["call_id"]), retained)

    async def test_target_generation_is_rechecked_after_admission_and_before_start_gate(self):
        from runtime.cli_v1.test_owned_win32_session import FakeCancellationSupervisor

        for change_at in ("admission", "factory", "identity", "unavailable", "unavailable_identity"):
            with self.subTest(change_at=change_at), tempfile.TemporaryDirectory() as root:
                current = ["a" * 64]
                processes, adapters, supervisors, invocations = [], [], [], []

                def read_generation():
                    if current[0] is None:
                        raise RuntimeError("target identity query failed")
                    return current[0]

                def identity(process):
                    if change_at in ("identity", "unavailable_identity"):
                        current[0] = "b" * 64 if change_at == "identity" else None
                    return {"pid": process.pid, "creation_time_100ns": 9301}

                def make_owner(*_args):
                    gate = OperationOwner(clock_ns=time.monotonic_ns,
                                          process_identity_reader=identity)
                    supervisor = FakeCancellationSupervisor(gate)
                    adapter = OwnedWin32SessionOwner(gate, supervisor)
                    adapter.bind_target_generation_reader(read_generation)
                    adapters.append(adapter)
                    supervisors.append(supervisor)
                    return adapter

                def make_producer(action):
                    invocations.append(action["operation_id"])
                    if change_at == "factory":
                        current[0] = "b" * 64
                    process = GatedSyntheticProcess(4301)
                    process.authorized = False
                    processes.append(process)
                    return (process, lambda: identity(process),
                            lambda: setattr(process, "authorized", True))

                server = create_server({"fixture": 123}, root,
                    session_mode="guarded-win32", _guarded_win32_owner_factory=make_owner,
                    _guarded_win32_producer_factory=make_producer)
                binding = json.loads((await server.call_tool(
                    "interface_guarded_win32_bind_target", {})).content[0].text)
                admitted = json.loads((await server.call_tool("interface_guarded_win32_admit", {
                    "action_operation_id": "8" * 32,
                    "target_binding_id": binding["target_binding_id"],
                    "operation_deadline_ns": time.monotonic_ns() + 5_000_000_000,
                    "obligations": ["key:CTRL"],
                })).content[0].text)
                if change_at in ("admission", "unavailable"):
                    current[0] = "b" * 64 if change_at == "admission" else None
                response = json.loads((await server.call_tool("interface_guarded_win32_start", {
                    "call_id": admitted["call_id"], "wait_for_result_ms": 1000,
                })).content[0].text)
                self.assertEqual(response["status"], "unknown", response)
                self.assertFalse(any(process.authorized for process in processes))
                self.assertFalse(any(process.is_alive() for process in processes))
                self.assertEqual(len(invocations), 0 if change_at in
                                 ("admission", "unavailable") else 1)
                self.assertEqual(supervisors[0].calls, [])
                retained = adapters[0].interface_result(admitted["call_id"])
                self.assertIsNone(retained["cancellation"])
                self.assertFalse(response["replay_allowed"])
                self.assertEqual(retained["action"]["result"]["error"],
                    "target_generation_unavailable_before_start" if "unavailable" in change_at
                    else "target_generation_changed_before_start")
                previous_invocations = list(invocations)
                await server.call_tool("interface_guarded_win32_start", {
                    "call_id": admitted["call_id"], "wait_for_result_ms": 1000})
                self.assertEqual(invocations, previous_invocations)
                self.assertEqual(adapters[0].interface_result(admitted["call_id"]), retained)

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
        producer_factory_calls = []

        def make_owner(*_args):
            gate = OperationOwner(clock_ns=time.monotonic_ns,
                process_identity_reader=lambda handle: processes.get(handle))
            adapter = OwnedWin32SessionOwner(gate, SyntheticSupervisor(gate))
            adapter.bind_target_generation_reader(lambda: generation)
            return adapter

        def make_producer(_action):
            producer_factory_calls.append(_action["operation_id"])
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
            repeated_start = json.loads((await server.call_tool(
                "interface_guarded_win32_start", {
                    "call_id": call_id, "wait_for_result_ms": 1000})).content[0].text)
            self.assertEqual(repeated_start["status"], "running")
            self.assertEqual(producer_factory_calls, ["c" * 32])
            canceled = json.loads((await server.call_tool(
                "interface_guarded_win32_cancel", {
                    "call_id": call_id,
                    "cleanup_deadline_ns": time.monotonic_ns() + 2_000_000_000,
                })).content[0].text)
            self.assertEqual(canceled["status"], "pending")
            self.assertFalse(canceled["release_confirmed"])
            self.assertIsNone(canceled["task_success"])
            repeated_cancel = json.loads((await server.call_tool(
                "interface_guarded_win32_cancel", {
                    "call_id": call_id,
                    "cleanup_deadline_ns": time.monotonic_ns() + 2_000_000_000,
                })).content[0].text)
            self.assertEqual(repeated_cancel["cancellation"]["operation_id"],
                             canceled["cancellation"]["operation_id"])
            self.assertEqual(repeated_cancel["cancellation"]["status"], "pending")
            retained = json.loads((await server.call_tool("interface_results", {
                "call_id": call_id})).content[0].text)
            self.assertEqual(retained["action"]["status"], "running")
            self.assertEqual(retained["cancellation"]["status"], "pending")

    async def test_public_oracle_timeout_stays_unknown_after_late_receipt(self):
        generation = "a" * 64
        process_identities = {}
        producer_calls = []
        oracle_calls = []
        release_oracle = threading.Event()
        adapter_holder = []

        class SyntheticSupervisor:
            def __init__(self, operation_owner):
                self.owner = operation_owner

            def producer_started(self, *args, **kwargs):
                return self.owner.producer_started(*args, **kwargs)

            def cancel(self, operation_id, target_generation, *, cleanup_deadline_ns):
                return self.owner.request_cancel(operation_id, target_generation,
                    cleanup_deadline_ns=cleanup_deadline_ns)

            def close(self):
                return None

        def make_owner(*_args):
            operation_owner = OperationOwner(clock_ns=time.monotonic_ns,
                process_identity_reader=lambda process: process_identities.get(process))
            adapter = OwnedWin32SessionOwner(operation_owner,
                SyntheticSupervisor(operation_owner))
            adapter.bind_target_generation_reader(lambda: generation)
            adapter_holder.append(adapter)
            return adapter

        def make_producer(action):
            producer_calls.append(action["operation_id"])
            process = GatedSyntheticProcess(4317)
            identity = {"pid": 4317, "creation_time_100ns": 9317}
            process_identities[process] = identity
            return process, identity, lambda: setattr(process, "authorized", True)

        def delayed_oracle(action):
            oracle_calls.append(action["call_id"])
            if not release_oracle.wait(2):
                raise TimeoutError("test oracle remained blocked")
            return {
                "call_id": action["call_id"],
                "operation_id": action["operation_id"],
                "target_generation": action["target_generation"],
                "oracle_id": "b" * 32,
                "outcome": "success",
                "observed_monotonic_ns": time.monotonic_ns(),
                "evidence_ref": "late-test-oracle",
            }

        with tempfile.TemporaryDirectory() as root:
            server = create_server({"fixture": 123}, root,
                session_mode="guarded-win32",
                _guarded_win32_owner_factory=make_owner,
                _guarded_win32_producer_factory=make_producer,
                _guarded_win32_task_oracle=delayed_oracle)
            try:
                binding = json.loads((await server.call_tool(
                    "interface_guarded_win32_bind_target", {})).content[0].text)
                admitted = json.loads((await server.call_tool(
                    "interface_guarded_win32_admit", {
                        "action_operation_id": "c" * 32,
                        "target_binding_id": binding["target_binding_id"],
                        "operation_deadline_ns": time.monotonic_ns() + 5_000_000_000,
                        "obligations": ["key:a"],
                    })).content[0].text)
                call_id = admitted["call_id"]
                started = json.loads((await server.call_tool(
                    "interface_guarded_win32_start", {
                        "call_id": call_id, "wait_for_result_ms": 1000,
                    })).content[0].text)
                self.assertEqual(started["status"], "running")
                timed_out = json.loads((await server.call_tool(
                    "interface_guarded_win32_verify_task", {
                        "call_id": call_id, "wait_for_result_ms": 0,
                    })).content[0].text)
                self.assertEqual(timed_out["status"], "unknown")
                self.assertIsNone(timed_out["task_success"])
                release_oracle.set()
                await asyncio.sleep(0.05)

                repeated = json.loads((await server.call_tool(
                    "interface_guarded_win32_verify_task", {
                        "call_id": call_id, "wait_for_result_ms": 1000,
                    })).content[0].text)
                retained = json.loads((await server.call_tool(
                    "interface_results", {"call_id": call_id})).content[0].text)
                self.assertEqual(repeated["status"], "unknown")
                self.assertIsNone(repeated["task_success"])
                self.assertFalse(repeated["operation_invoked"])
                self.assertEqual(retained["task_effect"]["status"], "unknown")
                self.assertIsNone(retained["task_effect"]["receipt"])
                self.assertIsNone(retained["task_success"])
                self.assertFalse(retained["replay_allowed"])
                self.assertEqual(oracle_calls, [call_id])
                self.assertEqual(producer_calls, ["c" * 32])
            finally:
                release_oracle.set()
                for adapter in adapter_holder:
                    adapter._supervisor.close()

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
        down, neutral, application_request, application_completed = (
            context.Event(), context.Event(), context.Event(), context.Event())
        application_ready, application_stop, producer_started = (
            context.Event(), context.Event(), context.Event())
        child_handles = []
        adapter_holder = []
        generation = "a" * 64

        application = context.Process(target=_synthetic_application_worker,
            args=(application_request, application_completed,
                  application_ready, application_stop))
        child_handles.append((application, None, None))
        application.start()
        self.assertTrue(application_ready.wait(5))

        def make_owner(*_args):
            gate = OperationOwner(clock_ns=time.monotonic_ns,
                process_identity_reader=_synthetic_process_identity)

            recovery_factory = _persistent_helper_factory(context, "recovery",
                _handle_fake_recovery, (down, neutral), child_handles)
            observer_factory = _persistent_helper_factory(context, "observer",
                _handle_fake_observation, (neutral,), child_handles)

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
                args=(start_gate, down, application_request, producer_started))
            child_handles.append((process, None, None))
            return process, lambda: _synthetic_process_identity(process), start_gate.set

        def task_oracle(action):
            receive, send = context.Pipe(duplex=False)
            process = context.Process(target=_synthetic_task_effect_oracle,
                args=(application_completed, action, "b" * 32, send))
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
                self.assertTrue(await asyncio.to_thread(
                    application_completed.wait, 5))

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
                application_stop.set()
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

    async def test_public_fresh_generation_scores_separately_from_old_unknown(self):
        context = multiprocessing.get_context("spawn")
        generations = ("c" * 64, "d" * 64)
        child_handles = []
        adapter_holders = [[], []]
        roots = [tempfile.TemporaryDirectory(), tempfile.TemporaryDirectory()]
        old_down = context.Event()
        old_oracle_started = threading.Event()
        old_oracle_release = threading.Event()
        old_oracle_finished = threading.Event()
        producer_calls = [[], []]
        oracle_calls = [[], []]
        new_down, new_neutral, new_request, new_completed = (
            context.Event(), context.Event(), context.Event(), context.Event())
        app_ready, app_stop, old_producer_started, new_started = (
            context.Event(), context.Event(), context.Event(), context.Event())
        application = context.Process(target=_synthetic_application_worker,
            args=(new_request, new_completed, app_ready, app_stop))
        child_handles.append((application, None, None))
        application.start()

        def build_server(index):
            generation = generations[index]
            down = old_down if index == 0 else new_down
            neutral = context.Event() if index == 0 else new_neutral
            request = context.Event() if index == 0 else new_request
            started = old_producer_started if index == 0 else new_started

            def make_owner(*_args):
                owner = OperationOwner(clock_ns=time.monotonic_ns,
                    process_identity_reader=_synthetic_process_identity)

                recovery_factory = _persistent_helper_factory(context, "recovery",
                    _handle_wrong_recovery_receipt if index == 0
                    else _handle_fake_recovery,
                    () if index == 0 else (down, neutral), child_handles)
                observer_factory = _persistent_helper_factory(context, "observer",
                    _handle_fake_observation, (neutral,), child_handles)

                supervisor = OperationCancellationSupervisor(owner,
                    recovery_process_factory=recovery_factory,
                    observer_process_factory=observer_factory,
                    process_identity_reader=_synthetic_process_identity)
                adapter = OwnedWin32SessionOwner(owner, supervisor)
                adapter.bind_target_generation_reader(lambda: generation)
                adapter_holders[index].append(adapter)
                return adapter

            def producer_factory(_action):
                producer_calls[index].append(_action["operation_id"])
                start_gate = context.Event()
                process = context.Process(target=_spawned_gate_producer,
                    args=(start_gate, down, request, started))
                child_handles.append((process, None, None))
                return process, lambda: _synthetic_process_identity(process), start_gate.set

            kwargs = {
                "session_mode": "guarded-win32",
                "_guarded_win32_owner_factory": make_owner,
                "_guarded_win32_producer_factory": producer_factory,
            }
            def task_oracle(action):
                oracle_calls[index].append(action["call_id"])
                if index == 0:
                    old_oracle_started.set()
                    try:
                        if not old_oracle_release.wait(5):
                            raise TimeoutError("generation-A oracle remained blocked")
                        return {
                            "call_id": action["call_id"],
                            "operation_id": action["operation_id"],
                            "target_generation": action["target_generation"],
                            "oracle_id": "d" * 32,
                            "outcome": "success",
                            "observed_monotonic_ns": time.monotonic_ns(),
                            "evidence_ref": "late-generation-A-oracle",
                        }
                    finally:
                        old_oracle_finished.set()
                else:
                    receive, send = context.Pipe(duplex=False)
                    process = context.Process(target=_synthetic_task_effect_oracle,
                        args=(new_completed, action, "e" * 32, send))
                    child_handles.append((process, receive, send))
                    process.start()
                    try:
                        if not receive.poll(3):
                            raise TimeoutError("generation-B oracle deadline")
                        return receive.recv()
                    finally:
                        process.join(1)
            kwargs["_guarded_win32_task_oracle"] = task_oracle
            return create_server({"fixture": 123}, roots[index].name, **kwargs)

        servers = []
        try:
            self.assertTrue(await asyncio.to_thread(app_ready.wait, 5))
            servers = [build_server(0), build_server(1)]

            old_binding = json.loads((await servers[0].call_tool(
                "interface_guarded_win32_bind_target", {})).content[0].text)
            old_admitted = json.loads((await servers[0].call_tool(
                "interface_guarded_win32_admit", {
                    "action_operation_id": "9" * 32,
                    "target_binding_id": old_binding["target_binding_id"],
                    "operation_deadline_ns": time.monotonic_ns() + 10_000_000_000,
                    "obligations": ["key:old"],
                })).content[0].text)
            old_call = old_admitted["call_id"]
            old_start_result = json.loads((await servers[0].call_tool(
                "interface_guarded_win32_start", {
                    "call_id": old_call, "wait_for_result_ms": 2000,
                })).content[0].text)
            self.assertEqual(old_start_result["status"], "running")
            self.assertEqual(producer_calls[0], ["9" * 32])
            self.assertTrue(await asyncio.to_thread(old_producer_started.wait, 5),
                {"start": old_start_result, "admit": old_admitted})
            self.assertTrue(old_down.is_set())
            old_timeout = json.loads((await servers[0].call_tool(
                "interface_guarded_win32_verify_task", {
                    "call_id": old_call, "wait_for_result_ms": 0,
                })).content[0].text)
            self.assertEqual(old_timeout["status"], "unknown")
            self.assertIsNone(old_timeout["task_success"])
            self.assertTrue(await asyncio.to_thread(old_oracle_started.wait, 5))
            cancel = json.loads((await servers[0].call_tool(
                "interface_guarded_win32_cancel", {
                    "call_id": old_call,
                    "cleanup_deadline_ns": time.monotonic_ns() + 4_000_000_000,
                })).content[0].text)
            self.assertIn(cancel["status"], ("pending", "unknown"), cancel)

            repeated_cancel = json.loads((await servers[0].call_tool(
                "interface_guarded_win32_cancel", {
                    "call_id": old_call,
                    "cleanup_deadline_ns": time.monotonic_ns() + 4_000_000_000,
                })).content[0].text)
            self.assertEqual(repeated_cancel["cancellation"]["operation_id"],
                             cancel["cancellation"]["operation_id"])

            deadline = time.monotonic() + 4
            while time.monotonic() < deadline:
                old_result = json.loads((await servers[0].call_tool(
                    "interface_results", {"call_id": old_call})).content[0].text)
                if old_result.get("cancellation", {}).get("status") == "unknown":
                    break
                await asyncio.sleep(0.01)
            self.assertEqual(old_result["cancellation"]["status"], "unknown", old_result)
            self.assertEqual(old_result["action"]["target_generation"], generations[0])
            self.assertIsNone(old_result["cancellation"]["task_success"])
            self.assertIsNone(old_result["task_success"])
            self.assertFalse(old_result["cancellation"]["release_confirmed"])
            self.assertFalse(old_result["cancellation"]["replay_allowed"])
            self.assertEqual(old_result["task_effect"]["status"], "unknown")
            self.assertIsNone(old_result["task_effect"]["receipt"])
            self.assertEqual(oracle_calls[0], [old_call])
            frozen_old = json.loads(json.dumps(old_result, sort_keys=True))

            old_oracle_release.set()
            self.assertTrue(await asyncio.to_thread(old_oracle_finished.wait, 5))
            duplicate_oracle = json.loads((await servers[0].call_tool(
                "interface_guarded_win32_verify_task", {
                    "call_id": old_call, "wait_for_result_ms": 1000,
                })).content[0].text)
            self.assertEqual(duplicate_oracle["status"], "unknown")
            self.assertFalse(duplicate_oracle["operation_invoked"])
            self.assertEqual(oracle_calls[0], [old_call])

            new_binding = json.loads((await servers[1].call_tool(
                "interface_guarded_win32_bind_target", {})).content[0].text)
            new_admitted = json.loads((await servers[1].call_tool(
                "interface_guarded_win32_admit", {
                    "action_operation_id": "a" * 32,
                    "target_binding_id": new_binding["target_binding_id"],
                    "operation_deadline_ns": time.monotonic_ns() + 10_000_000_000,
                    "obligations": ["key:new"],
                })).content[0].text)
            new_call = new_admitted["call_id"]
            self.assertNotEqual(old_call, new_call)
            self.assertEqual(new_admitted["action"]["target_generation"], generations[1])
            new_started_result = json.loads((await servers[1].call_tool(
                "interface_guarded_win32_start", {
                    "call_id": new_call, "wait_for_result_ms": 2000,
                })).content[0].text)
            self.assertEqual(new_started_result["status"], "running")
            self.assertEqual(producer_calls[1], ["a" * 32])
            self.assertTrue(await asyncio.to_thread(new_started.wait, 5))
            self.assertTrue(await asyncio.to_thread(new_completed.wait, 5))
            new_effect = json.loads((await servers[1].call_tool(
                "interface_guarded_win32_verify_task", {
                    "call_id": new_call, "wait_for_result_ms": 3000,
                })).content[0].text)
            self.assertEqual(new_effect["status"], "verified", new_effect)
            self.assertTrue(new_effect["task_success"])
            self.assertEqual(oracle_calls[1], [new_call])
            self.assertEqual(new_effect["task_effect"]["receipt"]["oracle_id"], "e" * 32)
            self.assertNotEqual(new_effect["task_effect"]["receipt"]["oracle_id"],
                ((frozen_old.get("task_effect") or {}).get("receipt") or {}).get("oracle_id"))

            old_after = json.loads((await servers[0].call_tool(
                "interface_results", {"call_id": old_call})).content[0].text)
            self.assertEqual(old_after, frozen_old)
            new_after = json.loads((await servers[1].call_tool(
                "interface_results", {"call_id": new_call})).content[0].text)
            self.assertTrue(new_after["task_success"])
            self.assertEqual(new_after["action"]["target_generation"], generations[1])
            self.assertEqual(new_after["action"]["operation_id"], "a" * 32)
            self.assertIsNone(new_after["cancellation"])
        finally:
            app_stop.set()
            old_oracle_release.set()
            for holder in adapter_holders:
                for adapter in holder:
                    adapter._supervisor.close()
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
            for root in roots:
                root.cleanup()

    async def test_public_observer_timeout_keeps_release_unknown(self):
        context = multiprocessing.get_context("spawn")
        generation = "a" * 64
        down, producer_started, observer_started = (
            context.Event(), context.Event(), context.Event())
        child_handles = []
        adapters = []

        def make_owner(*_args):
            operation_owner = OperationOwner(clock_ns=time.monotonic_ns,
                process_identity_reader=_synthetic_process_identity)
            recovery_factory = _persistent_helper_factory(context, "recovery",
                _handle_fake_recovery, (down, context.Event()), child_handles)
            observer_factory = _persistent_helper_factory(context, "observer",
                _handle_blocked_observation, (observer_started,), child_handles)
            supervisor = OperationCancellationSupervisor(operation_owner,
                recovery_process_factory=recovery_factory,
                observer_process_factory=observer_factory,
                process_identity_reader=_synthetic_process_identity,
                terminate_grace_s=0.05, kill_grace_s=0.05)
            adapter = OwnedWin32SessionOwner(operation_owner, supervisor)
            adapter.bind_target_generation_reader(lambda: generation)
            adapters.append(adapter)
            return adapter

        def producer_factory(_action):
            start_gate = context.Event()
            process = context.Process(target=_spawned_gate_producer,
                args=(start_gate, down, context.Event(), producer_started))
            child_handles.append((process, None, None))
            return process, lambda: _synthetic_process_identity(process), start_gate.set

        with tempfile.TemporaryDirectory() as root:
            server = create_server({"fixture": 123}, root,
                session_mode="guarded-win32",
                _guarded_win32_owner_factory=make_owner,
                _guarded_win32_producer_factory=producer_factory)
            try:
                binding = json.loads((await server.call_tool(
                    "interface_guarded_win32_bind_target", {})).content[0].text)
                admitted = json.loads((await server.call_tool(
                    "interface_guarded_win32_admit", {
                        "action_operation_id": "e" * 32,
                        "target_binding_id": binding["target_binding_id"],
                        "operation_deadline_ns": time.monotonic_ns() + 4_000_000_000,
                        "obligations": ["key:a"],
                    })).content[0].text)
                call_id = admitted["call_id"]
                started = json.loads((await server.call_tool(
                    "interface_guarded_win32_start", {
                        "call_id": call_id, "wait_for_result_ms": 1000,
                    })).content[0].text)
                self.assertEqual(started["status"], "running")
                self.assertTrue(await asyncio.to_thread(producer_started.wait, 5))

                canceled = json.loads((await server.call_tool(
                    "interface_guarded_win32_cancel", {
                        "call_id": call_id,
                        "cleanup_deadline_ns": time.monotonic_ns() + 1_500_000_000,
                    })).content[0].text)
                self.assertIn(canceled["status"], ("pending", "unknown"))
                self.assertTrue(await asyncio.to_thread(observer_started.wait, 5))
                deadline = time.monotonic() + 3
                retained = None
                while time.monotonic() < deadline:
                    retained = json.loads((await server.call_tool(
                        "interface_results", {"call_id": call_id})).content[0].text)
                    if retained["cancellation"]["status"] == "unknown":
                        break
                    await asyncio.sleep(0.01)
                self.assertEqual(retained["cancellation"]["status"], "unknown")
                self.assertFalse(retained["cancellation"]["release_confirmed"])
                self.assertIsNone(retained["cancellation"]["task_success"])
                self.assertFalse(retained["cancellation"]["replay_allowed"])
            finally:
                for adapter in adapters:
                    adapter._supervisor.close()
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
