import os
import threading
import time
import unittest

from main_thread_scorer_polling_v1 import MainThreadScorerPolling, _wait_readable


class FakeClock:
    def __init__(self):
        self.ns = 0

    def now(self):
        return self.ns

    def advance(self, ns):
        self.ns += ns


class ScriptedIO:
    def __init__(self, clock, chunks):
        self.clock = clock
        self.chunks = list(chunks)

    def wait(self, _fd, timeout_s):
        if self.chunks:
            return True
        self.clock.advance(round(timeout_s * 1e9))
        return False

    def read(self, _fd, _size):
        if not self.chunks:
            return b""
        return self.chunks.pop(0)


class PollingTests(unittest.TestCase):
    def test_periodic_sampling_without_commands(self):
        clock = FakeClock()
        io = ScriptedIO(clock, [])
        receipts = []
        loop = MainThreadScorerPolling(sample_hz=10, clock_ns=clock.now, wait_readable=io.wait, read_fn=io.read)
        stats = loop.run(0, sample_fn=lambda: {"x": 1}, scorer_sink=receipts.append,
                         command_handler=lambda _line: True, max_samples=4)
        self.assertEqual(stats.samples, 4)
        self.assertEqual(stats.commands, 0)
        self.assertEqual(stats.missed_sample_periods, 0)
        self.assertEqual([r["scheduled_ns"] for r in receipts], [0, 100_000_000, 200_000_000, 300_000_000])

    def test_commands_and_samples_share_owner_thread(self):
        clock = FakeClock()
        io = ScriptedIO(clock, [b'{"a":1}\nSTOP\n'])
        sample_threads = []
        command_threads = []
        loop = MainThreadScorerPolling(sample_hz=10, clock_ns=clock.now, wait_readable=io.wait, read_fn=io.read)
        stats = loop.run(
            0,
            sample_fn=lambda: sample_threads.append(threading.get_ident()) or {"k": 0},
            scorer_sink=lambda _row: None,
            command_handler=lambda line: command_threads.append(threading.get_ident()) or (line != "STOP"),
        )
        self.assertTrue(stats.stopped_by_command)
        self.assertEqual(stats.commands, 2)
        self.assertTrue(sample_threads)
        self.assertTrue(command_threads)
        self.assertEqual(set(sample_threads + command_threads), {stats.owner_thread_id})

    def test_scorer_payload_never_enters_command_callback(self):
        clock = FakeClock()
        io = ScriptedIO(clock, [b'PING\nSTOP\n'])
        commands = []
        scorer = []
        loop = MainThreadScorerPolling(sample_hz=10, clock_ns=clock.now, wait_readable=io.wait, read_fn=io.read)
        loop.run(0, sample_fn=lambda: {"privileged": 7}, scorer_sink=scorer.append,
                 command_handler=lambda line: commands.append(line) or (line != "STOP"))
        self.assertEqual(commands, ["PING", "STOP"])
        self.assertEqual(scorer[0]["payload"], {"privileged": 7})
        self.assertNotIn("privileged", " ".join(commands))

    def test_long_sample_records_missed_periods_without_catchup(self):
        clock = FakeClock()
        io = ScriptedIO(clock, [])
        receipts = []
        calls = 0

        def sample():
            nonlocal calls
            calls += 1
            if calls == 1:
                clock.advance(250_000_000)
            return calls

        loop = MainThreadScorerPolling(sample_hz=10, clock_ns=clock.now, wait_readable=io.wait, read_fn=io.read)
        stats = loop.run(0, sample_fn=sample, scorer_sink=receipts.append,
                         command_handler=lambda _line: True, max_samples=3)
        self.assertEqual(stats.samples, 3)
        self.assertEqual(stats.missed_sample_periods, 1)
        self.assertEqual([r["scheduled_ns"] for r in receipts], [0, 100_000_000, 300_000_000])
        self.assertEqual(receipts[1]["missed_periods_before"], 1)

    def test_long_command_records_missed_periods(self):
        clock = FakeClock()
        io = ScriptedIO(clock, [b'SLOW\n'])
        receipts = []

        def command(line):
            if line == "SLOW":
                clock.advance(260_000_000)
            return True

        loop = MainThreadScorerPolling(sample_hz=10, clock_ns=clock.now, wait_readable=io.wait, read_fn=io.read)
        stats = loop.run(0, sample_fn=lambda: 1, scorer_sink=receipts.append,
                         command_handler=command, max_samples=3)
        self.assertEqual(stats.commands, 1)
        self.assertEqual(stats.missed_sample_periods, 1)
        self.assertEqual(receipts[1]["missed_periods_before"], 1)

    def test_multiple_commands_in_one_read(self):
        clock = FakeClock()
        io = ScriptedIO(clock, [b'A\nB\nSTOP\n'])
        seen = []
        loop = MainThreadScorerPolling(sample_hz=10, clock_ns=clock.now, wait_readable=io.wait, read_fn=io.read)
        stats = loop.run(0, sample_fn=lambda: None, scorer_sink=lambda _row: None,
                         command_handler=lambda line: seen.append(line) or (line != "STOP"))
        self.assertEqual(seen, ["A", "B", "STOP"])
        self.assertEqual(stats.commands, 3)

    def test_split_command_across_reads(self):
        clock = FakeClock()
        io = ScriptedIO(clock, [b'HE', b'LLO\nSTOP\n'])
        seen = []
        loop = MainThreadScorerPolling(sample_hz=10, clock_ns=clock.now, wait_readable=io.wait, read_fn=io.read)
        loop.run(0, sample_fn=lambda: None, scorer_sink=lambda _row: None,
                 command_handler=lambda line: seen.append(line) or (line != "STOP"))
        self.assertEqual(seen, ["HELLO", "STOP"])

    def test_eof_with_empty_buffer_stops_cleanly(self):
        clock = FakeClock()
        io = ScriptedIO(clock, [b""])
        loop = MainThreadScorerPolling(sample_hz=10, clock_ns=clock.now, wait_readable=io.wait, read_fn=io.read)
        stats = loop.run(0, sample_fn=lambda: None, scorer_sink=lambda _row: None,
                         command_handler=lambda _line: True)
        self.assertTrue(stats.eof)

    def test_eof_with_partial_command_fails_closed(self):
        clock = FakeClock()
        io = ScriptedIO(clock, [b'PART', b""])
        loop = MainThreadScorerPolling(sample_hz=10, clock_ns=clock.now, wait_readable=io.wait, read_fn=io.read)
        with self.assertRaisesRegex(ValueError, "unterminated"):
            loop.run(0, sample_fn=lambda: None, scorer_sink=lambda _row: None,
                     command_handler=lambda _line: True)

    def test_buffer_limit_fails_closed(self):
        clock = FakeClock()
        io = ScriptedIO(clock, [b'12345'])
        loop = MainThreadScorerPolling(sample_hz=10, clock_ns=clock.now, wait_readable=io.wait,
                                       read_fn=io.read, max_buffer_bytes=4)
        with self.assertRaisesRegex(ValueError, "buffer exceeded"):
            loop.run(0, sample_fn=lambda: None, scorer_sink=lambda _row: None,
                     command_handler=lambda _line: True)

    def test_invalid_sample_rate_rejected(self):
        for value in (0, -1, True):
            with self.assertRaises(ValueError):
                MainThreadScorerPolling(sample_hz=value)

    def test_real_pipe_delayed_command_is_serviced_during_sample_wait(self):
        read_fd, write_fd = os.pipe()
        seen = []
        thread_ids = []

        def send_late_command():
            threading.Event().wait(0.015)
            os.write(write_fd, b'LATE\n')
            os.close(write_fd)

        sender = threading.Thread(target=send_late_command)
        sender.start()
        loop = MainThreadScorerPolling(sample_hz=100)

        def handle(line):
            seen.append(line)
            thread_ids.append(threading.get_ident())
            return False

        try:
            stats = loop.run(
                read_fd,
                sample_fn=lambda: thread_ids.append(threading.get_ident()) or 1,
                scorer_sink=lambda _row: None,
                command_handler=handle,
            )
            sender.join(1)
            self.assertFalse(sender.is_alive())
            self.assertEqual(seen, ["LATE"])
            self.assertEqual(stats.commands, 1)
            self.assertGreaterEqual(stats.samples, 1)
            self.assertTrue(stats.stopped_by_command)
            self.assertEqual(set(thread_ids), {stats.owner_thread_id})
        finally:
            sender.join(1)
            os.close(read_fd)
    def test_real_pipe_eof_and_same_thread(self):
        read_fd, write_fd = os.pipe()
        try:
            os.write(write_fd, b'X\nSTOP\n')
            seen = []
            thread_ids = []
            loop = MainThreadScorerPolling(sample_hz=1000)
            stats = loop.run(
                read_fd,
                sample_fn=lambda: thread_ids.append(threading.get_ident()) or 1,
                scorer_sink=lambda _row: None,
                command_handler=lambda line: seen.append(line) or thread_ids.append(threading.get_ident()) or (line != "STOP"),
            )
            self.assertEqual(seen, ["X", "STOP"])
            self.assertEqual(set(thread_ids), {stats.owner_thread_id})
        finally:
            os.close(read_fd)
            os.close(write_fd)

    def test_real_empty_pipe_times_out_without_reading(self):
        read_fd, write_fd = os.pipe()
        try:
            started = time.monotonic()
            self.assertFalse(_wait_readable(read_fd, 0.01))
            elapsed = time.monotonic() - started
            self.assertGreaterEqual(elapsed, 0.005)
            self.assertLess(elapsed, 2.0)  # Gross hang detection, not a latency claim.
            self.assertFalse(_wait_readable(read_fd, 0))
            os.write(write_fd, b'X')
            self.assertTrue(_wait_readable(read_fd, 0))
            self.assertEqual(os.read(read_fd, 1), b'X')
        finally:
            os.close(read_fd)
            os.close(write_fd)

    def test_real_pipe_closed_writer_drains_data_then_reports_eof(self):
        read_fd, write_fd = os.pipe()
        os.write(write_fd, b'X\n')
        os.close(write_fd)
        try:
            seen = []
            loop = MainThreadScorerPolling(sample_hz=100)
            stats = loop.run(read_fd, sample_fn=lambda: None,
                scorer_sink=lambda _row: None,
                command_handler=lambda line: seen.append(line))
            self.assertEqual(seen, ['X'])
            self.assertTrue(stats.eof)
            self.assertEqual(stats.commands, 1)
            self.assertFalse(stats.stopped_by_command)
        finally:
            os.close(read_fd)

    def test_real_pipe_invalid_descriptor_raises(self):
        with self.assertRaises((OSError, ValueError)):
            _wait_readable(-1, 0)

    def test_real_pipe_callbacks_follow_run_thread_not_constructor_thread(self):
        read_fd, write_fd = os.pipe()
        loop = MainThreadScorerPolling(sample_hz=100)
        constructor_thread = threading.get_ident()
        os.write(write_fd, b'STOP\n')
        stats, errors, callbacks = [], [], []

        def run():
            try:
                stats.append(loop.run(read_fd,
                    sample_fn=lambda: callbacks.append(threading.get_ident()),
                    scorer_sink=lambda _row: callbacks.append(threading.get_ident()),
                    command_handler=lambda _line: callbacks.append(threading.get_ident()) or False,
                    max_samples=100))
            except BaseException as error:
                errors.append(error)

        worker = threading.Thread(target=run, daemon=True)
        try:
            worker.start()
            worker.join(2)
            self.assertFalse(worker.is_alive())
            self.assertEqual(errors, [])
            self.assertEqual(len(stats), 1)
            self.assertTrue(stats[0].stopped_by_command)
            self.assertNotEqual(stats[0].owner_thread_id, constructor_thread)
            self.assertEqual(set(callbacks), {stats[0].owner_thread_id})
        finally:
            os.close(read_fd)
            os.close(write_fd)


if __name__ == "__main__":
    unittest.main()
