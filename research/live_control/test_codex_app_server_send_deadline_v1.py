"""Send regressions using owned pipes; no app-server, model or native input."""
from contextlib import contextmanager
import io
import json
import os
import queue
import threading
import time
import unittest
from unittest.mock import Mock, patch

from research.live_control import codex_app_server_client_v2 as module


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


@contextmanager
def owned_client():
    read_fd, write_fd = os.pipe()

    class ReceiveLane:
        def __init__(self):
            self.rows = queue.Queue()

        def __iter__(self):
            return self

        def __next__(self):
            self.rows.get(timeout=5)
            raise StopIteration

        def close(self):
            self.rows.put(None)

    class Process:
        stdin = os.fdopen(write_fd, "w", encoding="utf-8", buffering=1)
        stdout = ReceiveLane()
        stderr = io.StringIO("")

        exited = False

        def poll(self):
            return 0 if self.exited else None

        def terminate(self):
            self.exited = True
            self.stdout.close()

        def wait(self, timeout=None):
            return 0

    client = module.CodexAppServerClient([], process_factory=lambda *_a, **_k: Process())
    try:
        yield client, read_fd
    finally:
        client.close(timeout=1)
        if client._reader.is_alive():
            raise AssertionError("fixture reader leaked")
        client.process.stdin.close()
        client.process.stdout.close()
        client.process.stderr.close()
        os.close(read_fd)


def wire(message):
    return (json.dumps(message, separators=(",", ":")) + "\n").encode("utf-8")


class AppServerSendDeadlineTests(unittest.TestCase):
    def assert_uncertain(self, operation, sent, total):
        with self.assertRaises(module.AppServerError) as result:
            operation()
        self.assertEqual(type(result.exception).__name__, "AppServerWriteUncertain")
        self.assertEqual((result.exception.sent, result.exception.total), (sent, total))
        return result.exception

    def test_large_record_is_preserved_across_partial_pipe_writes(self):
        message = {"method": "turn/start", "id": 1, "params": {"text": "あ" * 90000}}
        expected = wire(message)
        self.assertGreater(len(expected), 262144)
        with owned_client() as (client, read_fd):
            observed = bytearray()

            def drain():
                while len(observed) < len(expected):
                    chunk = os.read(read_fd, 4096)
                    if not chunk:
                        break
                    observed.extend(chunk)

            reader = threading.Thread(target=drain, daemon=True)
            reader.start()
            try:
                client._write(message, deadline=time.monotonic() + 2)
            finally:
                client.process.stdin.close()
                reader.join(timeout=2)
            self.assertFalse(reader.is_alive())
            self.assertEqual(bytes(observed), expected)

    def test_full_owned_pipe_times_out_and_quarantines_followup(self):
        with owned_client() as (client, _read_fd):
            fd = client.process.stdin.fileno()
            os.set_blocking(fd, False)
            prefill = 0
            while True:
                try:
                    prefill += os.write(fd, b"P" * 4096)
                except BlockingIOError:
                    break
            self.assertGreater(prefill, 0)
            message = {"method": "short", "id": 1}
            error = self.assert_uncertain(
                lambda: client._write(message, deadline=time.monotonic() + .02),
                0, len(wire(message)))
            self.assertIsInstance(error.__cause__, TimeoutError)
            with patch.object(module.os, "write") as write, patch.object(client, "_record") as record:
                self.assert_uncertain(lambda: client._write(message, deadline=time.monotonic() + 1), 0, 0)
                write.assert_not_called()
                record.assert_not_called()

    @unittest.skipUnless(os.name == "posix", "POSIX descriptor-number regression")
    def test_saturated_high_descriptor_times_out_not_descriptor_range_error(self):
        # A usable high FD must retain the same timeout contract as a low FD.
        # F_DUPFD allocates one owned descriptor; it does not overwrite any FD.
        import fcntl
        with owned_client() as (client, _read_fd):
            high_fd = fcntl.fcntl(client.process.stdin.fileno(), fcntl.F_DUPFD, 2048)
            client.process.stdin.close()
            client.process.stdin = os.fdopen(high_fd, "w", encoding="utf-8")
            self.assertGreaterEqual(high_fd, 2048)
            os.set_blocking(high_fd, False)
            filled = 0
            while True:
                try:
                    filled += os.write(high_fd, b"P" * 4096)
                except BlockingIOError:
                    break
            self.assertGreater(filled, 0)
            message = {"method": "high-fd"}
            error = self.assert_uncertain(
                lambda: client._write(message, deadline=time.monotonic() + .02),
                0, len(wire(message)))
            self.assertIsInstance(error.__cause__, TimeoutError)
            self.assert_uncertain(lambda: client.notify("followup", timeout=.1), 0, 0)

    def test_partial_record_reports_exact_prefix_and_no_replay(self):
        clock = Clock()
        message = {"method": "sample", "id": 1}
        attempts = []

        def write(_fd, data):
            attempts.append(bytes(data))
            if len(attempts) == 1:
                return 7
            raise BlockingIOError()

        def wait(*_args):
            clock.now = 11
            return [], [], []

        waiter = Mock()
        waiter.poll.side_effect = wait

        with owned_client() as (client, _read_fd), patch.object(module.time, "monotonic", clock), \
                patch.object(module.os, "write", write), patch.object(module.select, "select", wait), \
                patch.object(module.select, "poll", return_value=waiter, create=True), \
                patch.object(module.time, "sleep", wait):
            self.assert_uncertain(lambda: client._write(message, deadline=10), 7, len(wire(message)))
            self.assertEqual(attempts, [wire(message), wire(message)[7:]])
            client._closed = False
            self.assert_uncertain(lambda: client._write(message, deadline=20), 0, 0)
            self.assertEqual(len(attempts), 2)

    def test_lock_timeout_has_no_send_or_journal_and_does_not_poison(self):
        with owned_client() as (client, _read_fd):
            client._write_lock.acquire()
            try:
                with patch.object(module.os, "write") as write, patch.object(client, "_record") as record:
                    with self.assertRaises(TimeoutError):
                        client._write({"method": "wait"}, deadline=time.monotonic())
                    write.assert_not_called()
                    record.assert_not_called()
            finally:
                client._write_lock.release()
            client._write({"method": "later"}, deadline=time.monotonic() + 1)

    def test_expired_prewrite_budget_does_not_poison(self):
        with owned_client() as (client, _read_fd), patch.object(module.os, "write") as write:
            with self.assertRaises(TimeoutError):
                client._write({"method": "expired"}, deadline=time.monotonic())
            write.assert_not_called()
        with owned_client() as (client, read_fd):
            clock = Clock()
            with patch.object(module.time, "monotonic", clock), patch.object(client, "_record", side_effect=lambda *_: setattr(clock, "now", 11)):
                with self.assertRaises(TimeoutError):
                    client._write({"method": "journal-over-budget"}, deadline=10)
            clock.now = 0
            client._write({"method": "later"}, deadline=time.monotonic() + 1)
            self.assertEqual(os.read(read_fd, 4096), wire({"method": "later"}))

    def test_request_spends_one_budget_on_send_and_response_wait(self):
        clock = Clock()
        captured = []
        waits = []
        with owned_client() as (client, _read_fd):
            client._closed = False

            def send(_message, deadline=None):
                captured.append(deadline)
                clock.now = .04

            def wait(remaining):
                waits.append(remaining)
                clock.now = .11

            with patch.object(module.time, "monotonic", clock), patch.object(client, "_write", send), patch.object(client._condition, "wait", wait):
                with self.assertRaises(TimeoutError):
                    client.request("sample", timeout=.05)
            self.assertEqual(captured, [.05])
            self.assertEqual(len(waits), 1)
            self.assertAlmostEqual(waits[0], .01)

    def test_notify_supplies_default_and_explicit_deadline(self):
        clock = Clock()
        captured = []
        with owned_client() as (client, _read_fd), patch.object(module.time, "monotonic", clock), \
                patch.object(client, "_write", side_effect=lambda _message, deadline=None: captured.append(deadline)):
            client.notify("initialized")
            client.notify("custom", timeout=.5)
        self.assertEqual(captured, [30, .5])

    def test_invalid_timeouts_are_refused_before_id_or_send(self):
        with owned_client() as (client, _read_fd), patch.object(client, "_write") as write:
            for timeout in [True, -1, float("inf"), float("nan"), 10 ** 400, "1", None]:
                with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                    client.request("invalid", timeout=timeout)
                with self.subTest(notify=timeout), self.assertRaises(ValueError):
                    client.notify("invalid", timeout=timeout)
            self.assertEqual(client._next_id, 1)
            write.assert_not_called()

    def test_broken_pipe_preserves_cause_and_quarantines(self):
        with owned_client() as (client, _read_fd), patch.object(module.os, "write", side_effect=BrokenPipeError("closed")):
            error = self.assert_uncertain(lambda: client._write({"method": "fault"}, deadline=time.monotonic() + 1), 0, len(wire({"method": "fault"})))
            self.assertIsInstance(error.__cause__, BrokenPipeError)

    def test_cancellation_preserves_exception_and_quarantines(self):
        fault = KeyboardInterrupt("owned cancellation")
        with owned_client() as (client, _read_fd), patch.object(module.os, "write", side_effect=fault) as write:
            with self.assertRaises(KeyboardInterrupt) as result:
                client._write({"method": "cancel"}, deadline=time.monotonic() + 1)
            self.assertIs(result.exception, fault)
            self.assertTrue(client._send_uncertain)
            with patch.object(client, "_record") as record:
                self.assert_uncertain(lambda: client.notify("after-cancel", timeout=1), 0, 0)
                record.assert_not_called()
            self.assertEqual(write.call_count, 1)
        with owned_client() as (client, _read_fd), patch.object(module.os, "write", return_value=0):
            self.assert_uncertain(lambda: client._write({"method": "zero"}, deadline=time.monotonic() + 1), 0, len(wire({"method": "zero"})))

    def test_serialization_error_has_no_pipe_effect(self):
        with owned_client() as (client, _read_fd), patch.object(module.os, "write") as write:
            with self.assertRaises(TypeError):
                client._write({"bad": object()}, deadline=time.monotonic() + 1)
            write.assert_not_called()

    def test_unsupported_pipe_mode_fails_before_journal_or_send(self):
        with owned_client() as (client, _read_fd), patch.object(module.os, "set_blocking", side_effect=OSError("unsupported pipe")), \
                patch.object(module.os, "write") as write, patch.object(client, "_record") as record:
            with self.assertRaises(OSError):
                client._write({"method": "unsupported"}, deadline=time.monotonic() + 1)
            self.assertFalse(client._send_uncertain)
            self.assertIsNone(client._stdin_fd)
            write.assert_not_called()
            record.assert_not_called()

    def test_failed_journal_prevents_pipe_send_without_poisoning(self):
        with owned_client() as (client, read_fd):
            with patch.object(client, "_record", side_effect=OSError("journal failed")), patch.object(module.os, "write") as write:
                with self.assertRaises(OSError):
                    client._write({"method": "journal-fault"}, deadline=time.monotonic() + 1)
                write.assert_not_called()
                self.assertFalse(client._send_uncertain)
            client._write({"method": "later"}, deadline=time.monotonic() + 1)
            self.assertEqual(os.read(read_fd, 4096), wire({"method": "later"}))

    def test_ready_response_and_notification_records_are_preserved(self):
        with owned_client() as (client, read_fd):
            response = {"id": 1, "result": {"text": "正しい結果"}}
            notice = {"method": "notice", "params": {"value": 1}}
            client._responses[1] = response
            client._notifications.append(notice)
            self.assertEqual(client.request("healthy", {"text": "あ"}, timeout=1), response["result"])
            self.assertEqual(json.loads(os.read(read_fd, 4096)), {"method": "healthy", "id": 1, "params": {"text": "あ"}})
            self.assertEqual(list(client._notifications), [notice])

    def test_windows_wait_branch_uses_sleep_not_socket_select(self):
        clock = Clock()
        attempts = []

        def write(_fd, data):
            attempts.append(bytes(data))
            if len(attempts) == 1:
                raise BlockingIOError()
            return len(data)

        with owned_client() as (client, _read_fd), patch.object(module.time, "monotonic", clock), \
                patch.object(module.os, "name", "nt"), patch.object(module.os, "write", write), \
                patch.object(module.time, "sleep", side_effect=lambda amount: setattr(clock, "now", clock.now + amount)) as sleep, \
                patch.object(module.select, "select") as select:
            client._write({"method": "win-branch"}, deadline=.02)
            sleep.assert_called_once_with(.01)
            select.assert_not_called()
            self.assertEqual(attempts[0], attempts[1])


if __name__ == "__main__":
    unittest.main()
