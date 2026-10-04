"""Test the distinct per-key measurement path without relabeling its raw events."""
import importlib
import copy
import json
import socket
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "map01_v39_perkey_measurement_consumer_a03_20261005" / "INPUT_EVENTS.jsonl"


class MeasuredReleaseBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events = [json.loads(line) for line in RAW.read_text(encoding="utf-8").splitlines()]
        cls.down = next(row for row in cls.events if row["event"] == "input_admission")
        cls.up = next(row for row in cls.events if row["event"] == "input_release_measurement")
        try:
            cls.adapter = importlib.import_module("map01_scorer_stdio_adapter_v3")
        except ModuleNotFoundError:
            cls.adapter = None

    def validate(self, down=None, up=None, held=()):
        self.assertIsNotNone(self.adapter, "measured-release adapter module is missing")
        validator = getattr(self.adapter, "validate_measured_release_pair", None)
        self.assertTrue(callable(validator), "measured-release adapter is missing")
        return validator(self.down if down is None else down,
                         self.up if up is None else up,
                         backend_held_after=list(held))

    def test_boundary_uses_measured_up_sample_and_preserves_distinct_events(self):
        down_before, up_before = dict(self.down), dict(self.up)
        result = self.validate()
        self.assertEqual(result.schema, "map01-v39-perkey-tail-boundary-v1")
        self.assertEqual(result.program_id, "cover-7")
        self.assertEqual(result.step, 2)
        self.assertEqual(result.key, "F8")
        self.assertEqual(result.release_after_ns, 87811364949416)
        self.assertEqual(result.source_event_types,
                         ("input_admission", "input_release_measurement"))
        self.assertEqual(self.down, down_before)
        self.assertEqual(self.up, up_before)

    def test_transition_event_cannot_be_substituted_for_measurement_event(self):
        release = copy.deepcopy(self.up)
        release["event"] = "input_release_transition"
        with self.assertRaisesRegex(ValueError, "remain input_release_measurement"):
            self.validate(up=release)

    def test_wrong_key_in_physical_up_edge_is_rejected(self):
        release = copy.deepcopy(self.up)
        release["physical_key_measurement"]["adapter_edge"]["key"] = "F9"
        with self.assertRaisesRegex(ValueError, "nested physical edge identity"):
            self.validate(up=release)

    def test_mismatched_actuation_is_rejected(self):
        release = copy.deepcopy(self.up)
        release["physical_key_measurement"]["actuation_id"] = "another-actuation"
        with self.assertRaisesRegex(ValueError, "actuation identities differ"):
            self.validate(up=release)

    def test_unconfirmed_up_is_rejected(self):
        release = copy.deepcopy(self.up)
        release["physical_key_measurement"]["classification"] = "UNCERTAIN"
        with self.assertRaisesRegex(ValueError, "physical up edge is not confirmed"):
            self.validate(up=release)

    def test_remaining_held_key_blocks_scorer_boundary(self):
        with self.assertRaisesRegex(ValueError, "no remaining held keys"):
            self.validate(held=("F9",))

    def test_boolean_step_alias_is_rejected(self):
        down = copy.deepcopy(self.down)
        release = copy.deepcopy(self.up)
        down["step"] = release["step"] = True
        with self.assertRaisesRegex(ValueError, "exact nonnegative integer"):
            self.validate(down=down, up=release)

    def test_measured_tail_yields_to_ready_command_without_consuming_it(self):
        scorer_type = getattr(self.adapter, "MainThreadScorerStdin", None)
        self.assertTrue(callable(scorer_type), "measured scorer-tail adapter is missing")
        receiver, sender = socket.socketpair()
        stream = receiver
        samples = []
        sink = []
        from main_thread_scorer_polling_v1 import MainThreadScorerPolling
        now = time.perf_counter_ns()
        class ReadyLoop(MainThreadScorerPolling):
            def __init__(self):
                super().__init__(sample_hz=35.0, clock_ns=lambda: now,
                                 wait_readable=lambda _fd, _timeout: True)
                self.checks = 0

            def wait_readable(self, fd, timeout):
                self.checks += 1
                if self.checks == 1:
                    return True
                return self.read_ready(fd)

            def read_ready(self, fd):
                import select
                return bool(select.select([fd], [], [], 0)[0])

        loop = ReadyLoop()
        loop.read_fn = lambda _fd, count: receiver.recv(count)
        scorer = scorer_type(stream, lambda: samples.append("sample") or "state",
                             sink.append, loop=loop)
        try:
            sender.sendall(b"finish\n")
            import select
            self.assertTrue(select.select([receiver], [], [], 0)[0])
            down = copy.deepcopy(self.down)
            up = copy.deepcopy(self.up)
            shift = now - up["physical_key_measurement"]["adapter_edge"]["interval"][1]
            for row, edge_name, bracket_name in (
                (down, "down", "physical_down_interval"),
                (up, "up", "physical_up_interval"),
            ):
                measure = row["physical_key_measurement"]
                edge = measure["adapter_edge"]
                edge["interval"] = [value + shift for value in edge["interval"]]
                bracket = measure["bracket"]
                bracket[bracket_name] = [value + shift for value in bracket[bracket_name]]
                for name in ("sync_return_ns", "release_request_ns"):
                    if type(measure.get(name)) is int:
                        measure[name] += shift
                for name in ("pre_sample", "post_sample"):
                    if type(measure.get(name)) is dict:
                        measure[name]["finished_ns"] += shift
                if row is down:
                    row["admitted_ns"] += shift
                    row["input_ack_ns"] += shift
            result = scorer.sample_measured_tail(
                admission_event=down,
                release_measurement=up,
                backend_held_after=[],
                max_duration_ns=1_000_000_000,
                max_samples=4,
            )
            self.assertEqual(result["termination"], "command_ready")
            self.assertEqual(result["tail_samples"], 0)
            self.assertEqual(result["release_boundary_ns"],
                             up["physical_key_measurement"]["adapter_edge"]["interval"][1])
            self.assertEqual(result["source_event_types"],
                             ["input_admission", "input_release_measurement"])
            self.assertEqual(samples, [])
            self.assertEqual(next(scorer), "finish")
            self.assertEqual(scorer.commands, 1)
        finally:
            receiver.close()
            sender.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
