"""Regression and fake-session composition for returning scorer overruns."""
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import patch

from main_thread_scorer_polling_v1 import MainThreadScorerPolling
from map01_scorer_stdio_adapter_v1 import MainThreadScorerStdin
import session_map01_v13 as session

PERIOD = 100_000_000
FINISH = '{"op":"finish"}'

class Clock:
    def __init__(self):
        self.ns = 0
    def now(self):
        return self.ns

class ReadyInput:
    def __init__(self, clock):
        self.clock = clock
        self.chunks = [FINISH.encode() + b"\n"]
        self.events = []
    def wait(self, fd, timeout):
        self.events.append(("wait", self.clock.ns, timeout, threading.get_ident()))
        return bool(self.chunks)
    def read(self, fd, size):
        self.events.append(("read", self.clock.ns, threading.get_ident()))
        return self.chunks.pop(0)

class Stream:
    def fileno(self):
        return 0

class ScorerCommandService(unittest.TestCase):
    def fixture(self, sample_cost, sink_cost):
        clock = Clock()
        io = ReadyInput(clock)
        receipts = []
        samples = []
        def sample():
            if len(samples) >= 4:
                raise RuntimeError("finite diagnostic sample budget")
            samples.append(threading.get_ident())
            clock.ns += sample_cost
            return {"scorer_private": 17}
        def sink(row):
            receipts.append(row)
            clock.ns += sink_cost
        loop = MainThreadScorerPolling(sample_hz=10, clock_ns=clock.now,
                                      wait_readable=io.wait, read_fn=io.read)
        return clock, io, receipts, samples, sample, sink, loop

    def test_polling_serves_ready_finish_despite_repeated_sample_or_sink_overrun(self):
        for sample_cost, sink_cost in ((PERIOD, 0), (3*PERIOD, 0), (0, PERIOD), (0, 3*PERIOD)):
            with self.subTest(sample_cost=sample_cost, sink_cost=sink_cost):
                clock, io, receipts, samples, sample, sink, loop = self.fixture(sample_cost, sink_cost)
                commands = []
                stats = loop.run(0, sample_fn=sample, scorer_sink=sink,
                    command_handler=lambda line: commands.append(line) or False, max_samples=3)
                self.assertEqual(commands, [FINISH])
                self.assertTrue(stats.stopped_by_command)
                self.assertEqual(stats.samples, 1)
                self.assertEqual(stats.commands, 1)
                self.assertEqual(clock.ns, sample_cost + sink_cost)
                self.assertEqual(io.events[0][0:3], ("wait", clock.ns, 0))
                self.assertEqual(set(samples + [e[-1] for e in io.events]), {stats.owner_thread_id})
                self.assertEqual(receipts[0]["payload"], {"scorer_private": 17})
                self.assertNotIn("scorer_private", commands[0])

    def test_stdin_returns_ready_finish_before_another_sample(self):
        for sample_cost, sink_cost in ((PERIOD, 0), (3*PERIOD, 0), (0, PERIOD), (0, 3*PERIOD)):
            with self.subTest(sample_cost=sample_cost, sink_cost=sink_cost):
                clock, io, receipts, samples, sample, sink, loop = self.fixture(sample_cost, sink_cost)
                adapter = MainThreadScorerStdin(Stream(), sample, sink, loop=loop)
                command = None
                diagnostic = None
                try:
                    command = next(adapter)
                except RuntimeError as exc:
                    diagnostic = str(exc)
                self.assertEqual(command, FINISH, diagnostic)
                self.assertEqual(adapter.samples, 1)
                self.assertEqual(adapter.commands, 1)
                self.assertEqual(clock.ns, sample_cost + sink_cost)
                self.assertEqual(io.events[0][0:3], ("wait", clock.ns, 0))
                self.assertEqual(set(samples + [e[-1] for e in io.events]), {adapter.owner_thread})

    def test_polling_max_samples_still_terminates_before_command_dispatch(self):
        clock, io, receipts, samples, sample, sink, loop = self.fixture(PERIOD, 0)
        commands = []
        stats = loop.run(0, sample_fn=sample, scorer_sink=sink,
            command_handler=lambda line: commands.append(line), max_samples=1)
        self.assertEqual(stats.samples, 1)
        self.assertFalse(stats.stopped_by_command)
        self.assertEqual(commands, [])
        self.assertEqual(io.events, [])

    def test_polling_retains_trailing_misses_at_finish_eof_and_sample_cap(self):
        for sample_cost, sink_cost in ((3*PERIOD, 0), (0, 3*PERIOD)):
            for terminal in ("finish", "eof", "sample_cap"):
                with self.subTest(sample_cost=sample_cost, sink_cost=sink_cost, terminal=terminal):
                    clock, io, receipts, samples, sample, sink, loop = self.fixture(sample_cost, sink_cost)
                    if terminal == "eof":
                        io.chunks = [b""]
                    stats = loop.run(0, sample_fn=sample, scorer_sink=sink,
                        command_handler=lambda line: False,
                        max_samples=1 if terminal == "sample_cap" else 3)
                    self.assertEqual(stats.samples, 1)
                    self.assertEqual(stats.missed_sample_periods, 2)
                    self.assertEqual(stats.commands, int(terminal == "finish"))
                    self.assertEqual(stats.eof, terminal == "eof")
                    self.assertEqual(receipts[0]["missed_periods_before"], 0)

    def test_stdin_snapshot_accounts_pending_misses_without_double_counting(self):
        for sample_cost, sink_cost in ((3*PERIOD, 0), (0, 3*PERIOD)):
            for terminal in ("finish", "eof"):
                with self.subTest(sample_cost=sample_cost, sink_cost=sink_cost, terminal=terminal):
                    clock, io, receipts, samples, sample, sink, loop = self.fixture(sample_cost, sink_cost)
                    if terminal == "eof":
                        io.chunks = [b""]
                    adapter = MainThreadScorerStdin(Stream(), sample, sink, loop=loop)
                    self.assertEqual(adapter.stats()["missed_sample_periods"], 0)
                    if terminal == "eof":
                        with self.assertRaises(StopIteration):
                            next(adapter)
                    else:
                        self.assertEqual(next(adapter), FINISH)
                    self.assertEqual(adapter.stats()["missed_sample_periods"], 2)
                    self.assertEqual(adapter.stats()["missed_sample_periods"], 2)
                    self.assertEqual(adapter.samples, 1)
                    self.assertEqual(receipts[0]["missed_periods_before"], 0)
            with self.subTest(sample_cost=sample_cost, sink_cost=sink_cost, continuing=True):
                clock, io, receipts, samples, sample, sink, loop = self.fixture(sample_cost, sink_cost)
                io.chunks = [b"continue\n"]
                adapter = MainThreadScorerStdin(Stream(), sample, sink, loop=loop)
                self.assertEqual(next(adapter), "continue")
                self.assertEqual(adapter.stats()["missed_sample_periods"], 2)
                io.chunks = [FINISH.encode() + b"\n"]
                adapter.sample_fn = lambda: {"scorer_private": 17}
                adapter.sink = receipts.append
                self.assertEqual(next(adapter), FINISH)
                self.assertEqual(adapter.stats()["missed_sample_periods"], 2)
                self.assertEqual(adapter.stats()["missed_sample_periods"], 2)
                self.assertEqual(adapter.samples, 2)
                self.assertEqual(receipts[-1]["missed_periods_before"], 2)

    def test_v13_uses_repaired_stdin_and_real_separate_scorer_sink(self):
        clock = Clock()
        io = ReadyInput(clock)
        seen = []
        sample_calls = []
        base = types.ModuleType("session_map01_v12")
        backend = types.ModuleType("doom_retained_input_backend_v3")
        backend.Backend = object()
        class FakeGame:
            def init(self): pass
            def close(self): pass
            def get_episode_time(self): return 1
            def is_episode_finished(self): return False
            def is_player_dead(self): return False
            def get_game_variable(self, variable): return 0
            def get_ticrate(self): return 35
        original_ctor = FakeGame
        base.vd = types.SimpleNamespace(DoomGame=original_ctor,
            GameVariable=types.SimpleNamespace(KILLCOUNT="kills", DEATHCOUNT="deaths"))
        base.sys = sys
        base.Backend = object()
        def base_main():
            game = base.vd.DoomGame()
            game.init()
            try:
                line = next(base.sys.stdin)
                seen.append((json.loads(line), threading.get_ident()))
            finally:
                game.close()
        base.main = base_main
        real_adapter = MainThreadScorerStdin
        def make_adapter(stream, sample_fn, sink, sample_hz):
            loop = MainThreadScorerPolling(sample_hz=sample_hz, clock_ns=clock.now,
                wait_readable=io.wait, read_fn=io.read)
            def costly_sample():
                if len(sample_calls) >= 4:
                    raise RuntimeError("finite fake-session sample budget")
                sample_calls.append(threading.get_ident())
                payload = sample_fn()
                clock.ns += 3 * loop.period_ns
                return payload
            return real_adapter(stream, costly_sample, sink, sample_hz=sample_hz, loop=loop)
        with tempfile.TemporaryDirectory() as tmp:
            stream = Stream()
            with patch.dict(sys.modules, {"session_map01_v12": base,
                    "doom_retained_input_backend_v3": backend}), patch.object(sys, "stdin", stream), \
                    patch.object(sys, "argv", ["session_map01_v13.py", "--out", tmp]), \
                    patch.object(session, "MainThreadScorerStdin", make_adapter):
                session.main()
                self.assertIs(base.vd.DoomGame, original_ctor)
                self.assertIs(sys.stdin, stream)
            summary = json.loads((Path(tmp)/"scorer-summary.json").read_text())
            rows = [json.loads(line) for line in (Path(tmp)/"scorer-samples.jsonl").read_text().splitlines()]
            self.assertEqual([x[0] for x in seen], [{"op":"finish"}])
            self.assertEqual(set(sample_calls + [x[1] for x in seen]), {threading.get_ident()})
            self.assertEqual(summary["scheduler"]["samples"], 1)
            self.assertEqual(summary["scheduler"]["commands"], 1)
            self.assertEqual(summary["scheduler"]["missed_sample_periods"], 2)
            self.assertEqual(len(rows), 2)
            self.assertIs(rows[-1]["direct_final_sample"], True)
            self.assertTrue(all(row["controller_visible"] is False for row in rows))

if __name__ == "__main__":
    unittest.main()
