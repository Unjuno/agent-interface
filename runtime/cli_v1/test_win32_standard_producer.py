import json
import sys
import tempfile
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
                                    "binding_revision": 3}}}

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
            self.assertFalse(context.event.opened)
            self.assertEqual(identity_reader(), {"pid": 41,
                "creation_time_100ns": 99})
            open_gate()
            self.assertTrue(context.event.opened)

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


if __name__ == "__main__":
    unittest.main()
