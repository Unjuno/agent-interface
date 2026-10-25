import json
import time
import unittest
import asyncio
import threading
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch

from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.owned_win32_session import OwnedWin32SessionOwner
from runtime.cli_v1.supervised_win32_compiled import run_public_compiled
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
                "execution": {"emissions": 1}},
            "release_receipt": {"verified": True, "keys_down": [],
                "buttons_down": [], "keys_unknown": [], "buttons_unknown": []}}


class HeldProducerFactory:
    def __init__(self, process, identity):
        self.process = process
        self.identity = identity
        self.started = threading.Event()

    def __call__(self, _action):
        return self.process, lambda: self.identity, self.started.set

    def read_result(self, process):
        if process is not self.process or process.is_alive():
            raise RuntimeError("producer has not exited")
        raise AssertionError("a cancelled producer has no normal completion receipt")


class RecoveringFakeSupervisor(FakeSupervisor):
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
        readback = {"operation_id": operation_id,
            "target_generation": generation,
            "recovery_id": recovery["recovery_id"], "neutral": True}
        if not self.operation_owner.recovery_completed(operation_id, generation,
                recovery["recovery_id"], release_accepted=True,
                readback=readback):
            raise AssertionError("fake recovery was not confirmed")
        return self.operation_owner.result(operation_id)


class DelayedRecoveringFakeSupervisor(RecoveringFakeSupervisor):
    """Model lease expiry returning before the recovery receipt is published."""
    def __init__(self, operation_owner, process):
        super().__init__(operation_owner, process)
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
            "recovery_id": recovery["recovery_id"], "neutral": True}

        def finish_recovery():
            time.sleep(0.05)
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
            close = self.row(await server.call_tool("interface_close", {}))
            self.assertEqual(close["status"], "closed")
            self.assertFalse(close["release_confirmed"])
            self.assertTrue(retrieved["action"]["release_confirmed"])
        self.assertTrue(supervisor.closed)

    async def test_public_dispatch_keeps_child_release_unconfirmed_without_observer_readback(self):
        owner, producer, supervisor = self.make_components()
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
            self.assertEqual(action["result"]["status"], "completed")
            self.assertEqual(action["status"], "unknown")
            self.assertFalse(result["release_confirmed"])
            self.assertFalse(action["release_confirmed"])
            self.assertEqual(action["completion_custody"]["completion_readback_outcome"],
                             "missing")
            self.assertIsNone(action["completion_custody"]["completion_readback"])
            self.assertIsNone(result["task_success"])
            self.assertFalse(result["replay_allowed"])
            close = self.row(await server.call_tool("interface_close", {}))
            self.assertEqual(close["status"], "busy")
            self.assertFalse(close["release_confirmed"])
        self.assertFalse(supervisor.closed)

    async def test_task_oracle_is_not_invoked_for_unknown_public_custody(self):
        owner, producer, supervisor = self.make_components()

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
            self.assertEqual(action["completion_custody"]["completion_readback_outcome"],
                             "non_neutral")
            self.assertIsNone(verified["task_success"])
            self.assertFalse(verified["replay_allowed"])
            self.assertEqual(oracle_calls, [])
            close = self.row(await server.call_tool("interface_close", {}))
            self.assertEqual(close["status"], "busy")
        self.assertFalse(supervisor.closed)

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
                if retained["action"]["status"] != "running":
                    break
                self.assertLess(time.monotonic(), deadline, retained)
                await asyncio.sleep(0.01)
            self.assertEqual(retained["cancellation"]["status"], "recovered")

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
                    if old_result["action"]["status"] != "running":
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
            self.assertTrue(await asyncio.wait_for(
                asyncio.to_thread(producer.started.wait, 1), 1))

            cancelled = self.row(await server.call_tool("interface_cancel", {
                "call_id": pending["call_id"]}))
            self.assertEqual(cancelled["status"], "recovered")
            deadline = time.monotonic() + 2
            while True:
                retained = self.row(await server.call_tool("interface_results", {
                    "call_id": pending["call_id"]}))
                if retained["action"]["status"] != "running":
                    break
                self.assertLess(time.monotonic(), deadline, retained)
                await asyncio.sleep(0.01)
            self.assertEqual(retained["cancellation"]["status"], "recovered")
            self.assertTrue(retained["cancellation"]["release_confirmed"])
            self.assertEqual(retained["action"]["status"], "recovered", retained)
            action_result = retained["action"]["result"]
            self.assertEqual(action_result["status"], "recovered")
            cleanup = retained["cancellation"]["result"]
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
            self.assertIsNone(action_result["input_dispatched"])
            self.assertEqual(action_result["effect_status"], "unknown")
            self.assertIsNone(action_result["task_success"])
            self.assertFalse(action_result["replay_allowed"])
            self.assertIsNone(retained["task_success"])
            self.assertFalse(retained["replay_allowed"])

    async def test_late_recovery_after_dispatch_return_promotes_action_receipt(self):
        process = FakeProcess()
        identity = {"pid": 7101, "creation_time_100ns": 90101}
        op_owner = OperationOwner(clock_ns=time.monotonic_ns,
            process_identity_reader=lambda handle: identity if handle is process else None)
        supervisor = DelayedRecoveringFakeSupervisor(op_owner, process)
        owner = OwnedWin32SessionOwner(op_owner, supervisor, synthetic_only=False)
        owner.bind_target_generation_reader(lambda: GENERATION)
        producer = HeldProducerFactory(process, identity)
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
                        and cancellation.get("status") == "recovered"):
                    break
                await asyncio.sleep(0.01)

            self.assertIsNotNone(retained)
            self.assertEqual(retained["cancellation"]["status"], "recovered")
            self.assertTrue(retained["cancellation"]["release_confirmed"])
            self.assertEqual(retained["action"]["status"], "recovered", retained)
            self.assertEqual(retained["action"]["result"]["status"], "recovered")
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

            receipt = await asyncio.to_thread(run_public_compiled,
                interface,
                {"first": stale_template(), "suffix": stale_template()},
                target="fixture", current_binding_revision=1,
                region=[0, 0, 1, 1], observe=standard_observe,
                dispatch=standard_dispatch, perceive=perceive,
                verify_effect=lambda _request, _report, _reply: {
                    "status": "succeeded",
                    "evidence_ref": "test-effect-predicate-confirmation"},
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
                self.assertEqual(retained["action"],
                    dispatch_rows[0]["supervision"]["action"])
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


if __name__ == "__main__":
    unittest.main()
