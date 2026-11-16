import ctypes
import hashlib
import json
import multiprocessing
from pathlib import Path
import sys
import tempfile
import time
import unittest


class Event:
    def __init__(self):
        self.opened = False

    def set(self):
        self.opened = True


class Process:
    def __init__(self, *, target, args, daemon):
        self.target, self.args, self.daemon = target, args, daemon
        self.pid = None
        self.exitcode = None
        self.alive = False

    def is_alive(self):
        return self.alive


class Context:
    def Event(self):
        self.event = Event()
        return self.event

    def Process(self, *, target, args, daemon):
        self.process = Process(target=target, args=args, daemon=daemon)
        return self.process

    def RawValue(self, *args, **kwargs):
        return multiprocessing.get_context("spawn").RawValue(*args, **kwargs)

    def RawArray(self, *args, **kwargs):
        return multiprocessing.get_context("spawn").RawArray(*args, **kwargs)


def _record_emission_then_block(counter, recorded):
    from runtime.backends.win32_v1.backend import (
        Win32Backend, _program_emissions,
    )
    backend = Win32Backend.__new__(Win32Backend)
    backend.emissions = 0
    backend._program_emission_counter = counter
    token = _program_emissions.set(0)
    try:
        backend._record_emission()
    finally:
        _program_emissions.reset(token)
    recorded.set()
    while True:
        time.sleep(1)


def _sendinput_inflight_then_block(operation_receipts, entered):
    from runtime.backends.win32_v1.backend import (
        INPUT, Win32Backend, _program_operation_receipt,
    )

    class BlockingUser32:
        def SendInput(self, _count, _inputs, _size):
            entered.set()
            while True:
                time.sleep(1)

    backend = Win32Backend.__new__(Win32Backend)
    backend.user32 = BlockingUser32()
    token = _program_operation_receipt.set((operation_receipts, 0))
    try:
        backend._send(INPUT())
    finally:
        _program_operation_receipt.reset(token)


class SharedEmissionCounterProcessTests(unittest.TestCase):
    def test_count_is_readable_after_forced_writer_retirement(self):
        context = multiprocessing.get_context("spawn")
        counter = context.RawValue(ctypes.c_long, 0)
        recorded = context.Event()
        process = context.Process(target=_record_emission_then_block,
            args=(counter, recorded), daemon=True)
        process.start()
        try:
            self.assertTrue(recorded.wait(2), "child did not record its emission")
            self.assertEqual(counter.value, 1)
            process.terminate()
            process.join(2)
            self.assertFalse(process.is_alive())
            self.assertEqual(counter.value, 1)
        finally:
            if process.is_alive():
                process.terminate()
                process.join(2)


class PrestartedWorkerProtocolTests(unittest.TestCase):
    def test_worker_requires_exact_authorization_before_native_dispatch(self):
        from runtime.cli_v1.win32_standard_producer import (
            _run_prestarted_standard_worker,
        )

        context = multiprocessing.get_context("spawn")
        parent, child = context.Pipe(duplex=True)
        action_counter = context.RawValue(ctypes.c_long, 0)
        operation_receipts = context.RawArray(ctypes.c_long, 8)
        with tempfile.TemporaryDirectory() as root:
            packet_path = str(Path(root) / "result.json")
            action = {"call_id": "1" * 32, "operation_id": "2" * 32,
                "target_generation": "a" * 64,
                "program": {"source": {"observation_seq": 1,
                    "binding_revision": 1}, "ops": [{"op": "verify"}]}}
            body = {"action": action, "packet_path": packet_path,
                "operation_count": 1}
            digest = hashlib.sha256(json.dumps(body, sort_keys=True,
                separators=(",", ":"), ensure_ascii=False,
                allow_nan=False).encode("utf-8")).hexdigest()
            process = context.Process(target=_run_prestarted_standard_worker,
                args=(child, {"fixture": 42}, action_counter,
                      operation_receipts, 2), daemon=True)
            process.start()
            child.close()
            try:
                self.assertTrue(parent.poll(30), "worker did not become ready")
                self.assertEqual(parent.recv(), {"status": "ready",
                    "protocol": "win32-producer-v1"})
                parent.send({**body, "request_sha256": digest})
                self.assertTrue(parent.poll(5), "worker did not acknowledge request")
                prepared = parent.recv()
                self.assertEqual(prepared, {"status": "prepared",
                    "call_id": action["call_id"],
                    "operation_id": action["operation_id"],
                    "target_generation": action["target_generation"],
                    "request_sha256": digest})
                parent.send({"status": "authorize", "call_id": action["call_id"],
                    "operation_id": action["operation_id"],
                    "target_generation": action["target_generation"],
                    "request_sha256": "0" * 64})
                process.join(5)
                self.assertFalse(process.is_alive(), "refused worker did not retire")
                self.assertEqual(process.exitcode, 0)
                self.assertEqual(action_counter.value, 0)
                self.assertEqual(list(operation_receipts), [0] * 8)
                self.assertFalse(Path(packet_path).exists())
            finally:
                parent.close()
                if process.is_alive():
                    process.terminate()
                    process.join(2)

    def test_inflight_sendinput_is_retained_as_unknown_after_child_termination(self):
        context = multiprocessing.get_context("spawn")
        receipts = context.RawArray(ctypes.c_long, 4)
        entered = context.Event()
        process = context.Process(target=_sendinput_inflight_then_block,
            args=(receipts, entered), daemon=True)
        process.start()
        try:
            self.assertTrue(entered.wait(2), "child did not enter SendInput")
            self.assertEqual(list(receipts), [3, 1, 0, 0])
            process.terminate()
            process.join(2)
            self.assertFalse(process.is_alive())
            self.assertEqual(list(receipts), [3, 1, 0, 0])
        finally:
            if process.is_alive():
                process.terminate()
                process.join(2)


@unittest.skipUnless(sys.platform == "win32", "native Win32 producer factory")
class NativeWin32StandardProducerFactoryTests(unittest.TestCase):
    def setUp(self):
        try:
            from runtime.cli_v1.win32_standard_producer import (
                NativeWin32StandardProducerFactory,
            )
        except ModuleNotFoundError:
            self.fail("native standard Win32 producer factory is missing")
        self.factory_type = NativeWin32StandardProducerFactory

    def make_action(self, call_id="1" * 32):
        return {"call_id": call_id, "operation_id": "2" * 32,
            "target_generation": "a" * 64,
            "program": {"source": {"observation_seq": 7,
                                    "binding_revision": 3},
                        "ops": [{"op": "verify"}, {"op": "pointer_button",
                            "button": "left", "down": True}, {"op": "verify"}]}}

    def test_prestarted_factory_is_ready_before_assignment_and_closes_idle_worker(self):
        with tempfile.TemporaryDirectory() as root:
            factory = self.factory_type({"fixture": 42}, root,
                prestarted=True, worker_startup_timeout_s=30.0)
            try:
                self.assertTrue(factory.ensure_ready())
                process = factory._worker
                self.assertIsNotNone(process.pid)
                self.assertTrue(process.is_alive())
                self.assertTrue(factory._worker_ready)
                process.terminate()
                process.join(2)
                self.assertFalse(process.is_alive())
                factory._replenish_after_retirement(process)
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline and not factory.ensure_ready():
                    time.sleep(0.01)
                self.assertTrue(factory.ensure_ready())
                self.assertIsNot(factory._worker, process)
            finally:
                closed = factory.close()
            self.assertEqual(closed["status"], "closed")
            self.assertTrue(closed["worker_retired"])

    def test_factory_returns_an_unstarted_gated_child_bound_to_the_action(self):
        with tempfile.TemporaryDirectory() as root:
            context = Context()
            factory = self.factory_type({"fixture": 42}, root,
                context=context, process_identity_reader=lambda _process: {
                    "pid": 41, "creation_time_100ns": 99})

            process, identity_reader, open_gate = factory(self.make_action())

            self.assertIsNone(process.pid)
            self.assertEqual(process.args[1], {"fixture": 42})
            self.assertEqual(process.args[2]["operation_id"], "2" * 32)
            self.assertEqual(process.args[4].value, 0)
            self.assertFalse(context.event.opened)
            self.assertEqual(identity_reader(), {"pid": 41,
                "creation_time_100ns": 99})
            open_gate()
            self.assertTrue(context.event.opened)

    def test_emission_lower_bound_survives_producer_retirement(self):
        with tempfile.TemporaryDirectory() as root:
            factory = self.factory_type({"fixture": 42}, root,
                context=Context(), process_identity_reader=lambda _process: {
                    "pid": 41, "creation_time_100ns": 99})
            process, _, _ = factory(self.make_action())
            process.alive, process.exitcode = False, -15
            process.args[4].value = 2

            self.assertEqual(
                factory.read_program_actions_lower_bound(process), 2)

    def test_operation_receipts_distinguish_completed_and_deadline_refused_ops(self):
        with tempfile.TemporaryDirectory() as root:
            factory = self.factory_type({"fixture": 42}, root,
                context=Context(), process_identity_reader=lambda _process: {
                    "pid": 41, "creation_time_100ns": 99})
            process, _, _ = factory(self.make_action())
            process.alive, process.exitcode = False, -15
            buffer = process.args[5]
            buffer[0:4] = (5, 1, 1, 0)
            buffer[4:8] = (6, 0, 0, 0)
            buffer[8:12] = (3, 1, 0, 0)

            receipt = factory.read_program_operation_receipts(process)

        self.assertEqual(receipt["schema"],
                         "win32-program-operation-receipts-v1")
        self.assertEqual(receipt["status"], "observed")
        self.assertEqual(receipt["operations"][0], {
            "operation_index": 0, "phase": "completed",
            "sendinput_attempts": 1, "sendinput_returned_count": 1,
            "local_action_count": 0})
        self.assertEqual(receipt["operations"][1], {
            "operation_index": 1, "phase": "lease_refused_before_sendinput",
            "sendinput_attempts": 0, "sendinput_returned_count": 0,
            "local_action_count": 0})
        self.assertEqual(receipt["operations"][2], {
            "operation_index": 2, "phase": "sendinput_in_flight",
            "sendinput_attempts": 1, "sendinput_returned_count": 0,
            "local_action_count": 0})

    def test_result_reader_checks_identity_and_consumes_one_packet_once(self):
        with tempfile.TemporaryDirectory() as root:
            factory = self.factory_type({"fixture": 42}, root,
                context=Context(), process_identity_reader=lambda _process: {
                    "pid": 41, "creation_time_100ns": 99})
            process, _, _ = factory(self.make_action())
            process.alive, process.exitcode = False, 0
            packet_path = process.args[3]
            packet = {"call_id": "1" * 32, "operation_id": "2" * 32,
                "target_generation": "a" * 64,
                "result": {"status": "completed"},
                "producer_timing": {"clock": "time.monotonic_ns",
                    "child_ready_monotonic_ns": 123},
                "release_receipt": {"verified": True}}
            with open(packet_path, "x", encoding="utf-8") as stream:
                json.dump(packet, stream)

            self.assertEqual(factory.read_result(process), {
                "result": packet["result"],
                "producer_timing": packet["producer_timing"],
                "release_receipt": packet["release_receipt"]})
            with self.assertRaisesRegex(ValueError, "already consumed"):
                factory.read_result(process)

    def test_result_reader_refuses_mismatched_operation_identity(self):
        with tempfile.TemporaryDirectory() as root:
            factory = self.factory_type({"fixture": 42}, root,
                context=Context(), process_identity_reader=lambda _process: {
                    "pid": 41, "creation_time_100ns": 99})
            process, _, _ = factory(self.make_action())
            process.alive, process.exitcode = False, 0
            packet = {"call_id": "1" * 32, "operation_id": "3" * 32,
                "target_generation": "a" * 64,
                "result": {"status": "completed"},
                "release_receipt": {"verified": True}}
            with open(process.args[3], "x", encoding="utf-8") as stream:
                json.dump(packet, stream)
            with self.assertRaisesRegex(RuntimeError, "identity or schema mismatch"):
                factory.read_result(process)

    def test_dispatch_exception_persists_unknown_receipt_for_parent_reader(self):
        from unittest.mock import patch
        from runtime.cli_v1.win32_standard_producer import _run_standard_program

        class OpenGate:
            def wait(self):
                return True

        class FakeBackend:
            def __init__(self, targets, *, program_emission_counter,
                         program_operation_receipts):
                self.targets = targets
                self.program_emission_counter = program_emission_counter
                self.program_operation_receipts = program_operation_receipts

            def close(self):
                return {"status": "closed"}

        class RaisingSession:
            def __init__(self, _backend):
                pass

            def dispatch(self, _program, *, current_observation_seq,
                         current_binding_revision):
                raise RuntimeError("controlled dispatch exception")

        with tempfile.TemporaryDirectory() as root:
            factory = self.factory_type({"fixture": 42}, root,
                context=Context(), process_identity_reader=lambda _process: {
                    "pid": 41, "creation_time_100ns": 99})
            process, _, _ = factory(self.make_action())
            with patch("runtime.backends.win32_v1.backend.Win32Backend",
                       FakeBackend), patch(
                    "runtime.backends.win32_v1.session.Win32RuntimeSession",
                    RaisingSession):
                _run_standard_program(OpenGate(), {"fixture": 42},
                    self.make_action(), process.args[3], process.args[4],
                    process.args[5])

            process.alive, process.exitcode = False, 0
            result = factory.read_result(process)

        self.assertEqual(result["result"], {
            "status": "runtime_failed", "error_type": "RuntimeError",
            "detail": "controlled dispatch exception"})
        self.assertEqual(result["release_receipt"], {
            "verified": False, "keys_down": [], "buttons_down": [],
            "keys_unknown": ["producer_exception"], "buttons_unknown": []})
        self.assertEqual(result["producer_timing"]["clock"],
                         "time.monotonic_ns")


if __name__ == "__main__":
    unittest.main()
