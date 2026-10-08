"""Response admission over fd-backed transport with controlled peer replies."""
import io
import json
import os
import queue
import threading
import unittest
from unittest.mock import patch

import codex_app_server_client_v2 as module
from codex_app_server_client_v2 import AppServerError, CodexAppServerClient


class Lines:
    def __init__(self):
        self.rows = queue.Queue()
        self.previous = None

    def __iter__(self):
        return self

    def __next__(self):
        if self.previous is not None:
            self.previous.set()
        value, self.previous = self.rows.get(timeout=3)
        if value is None:
            raise StopIteration
        return json.dumps(value) + "\n"

    def emit(self, value):
        consumed = threading.Event()
        self.rows.put((value, consumed))
        if not consumed.wait(2):
            raise TimeoutError("fixture reader did not consume row")

    def finish(self):
        self.rows.put((None, None))


class FdInput:
    """The client writes through os.write; this owns only a real pipe fd."""
    def __init__(self, fd):
        self._fd = fd
        self.closed = False

    def fileno(self):
        if self.closed:
            raise ValueError("I/O operation on closed pipe")
        return self._fd

    def close(self):
        if not self.closed:
            self.closed = True
            os.close(self._fd)


class Process:
    def __init__(self):
        self.read_fd, write_fd = os.pipe()
        self.stdout = Lines()
        self.stdin = FdInput(write_fd)
        self.stderr = io.StringIO()
        self.sent = []
        self.wire = bytearray()
        self.reply = lambda row: None
        self.dispatch_fault = None

    def poll(self):
        # This inert custom factory has no child to terminate.
        return 0

    def consume_written_bytes(self, data):
        self.wire.extend(data)
        while b"\n" in self.wire:
            line, _, rest = self.wire.partition(b"\n")
            self.wire = bytearray(rest)
            row = json.loads(line)
            self.sent.append(row)
            self.reply(row)


class ObservedLock:
    def __init__(self):
        self.lock = threading.Lock()
        self.entered = threading.Event()

    def acquire(self, timeout=-1):
        self.entered.set()
        if timeout is None or timeout < 0:
            return self.lock.acquire()
        return self.lock.acquire(timeout=timeout)

    def release(self):
        return self.lock.release()

    def locked(self):
        return self.lock.locked()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *_):
        self.release()


class WriteAdmissionTests(unittest.TestCase):
    def client(self):
        process = Process()
        client = CodexAppServerClient([], process_factory=lambda *a, **k: process)
        real_write = os.write

        def observed_write(fd, data):
            if fd != process.stdin.fileno():
                return real_write(fd, data)
            fault = process.dispatch_fault
            if fault == "before-write":
                raise OSError("fixture pre-write failure")
            count = real_write(fd, data)
            process.consume_written_bytes(os.read(process.read_fd, count))
            if fault == "after-write":
                raise OSError("fixture post-write failure")
            if fault == "interrupt-after-write":
                raise KeyboardInterrupt("fixture interrupt")
            return count

        patcher = patch.object(module.os, "write", side_effect=observed_write)
        patcher.start()

        def close():
            try:
                process.stdout.finish()
                client.close(timeout=1)
                self.assertFalse(client._reader.is_alive())
            finally:
                process.stdin.close()
                process.stderr.close()
                os.close(process.read_fd)
                patcher.stop()

        self.addCleanup(close)
        return client, process

    def assert_retired(self, client):
        self.assertEqual(getattr(client, "_pending", set()), set())
        self.assertEqual(client._responses, {})

    def launch(self, client, method="fixture/request"):
        values, errors = [], []

        def request():
            try:
                values.append(client.request(method, timeout=1))
            except BaseException as error:
                errors.append(error)

        thread = threading.Thread(target=request)
        thread.start()
        return thread, values, errors

    def test_numeric_float_success_preserves_adopted_contract(self):
        client, process = self.client()
        process.reply = lambda row: process.stdout.emit({"id": float(row["id"]), "result": "proper"})
        self.assertEqual(client.request("fixture/float", timeout=1), "proper")
        self.assertEqual(process.sent, [{"method": "fixture/float", "id": 1}])
        self.assert_retired(client)

    def test_numeric_float_error_preserves_original_server_error(self):
        client, process = self.client()
        process.reply = lambda row: process.stdout.emit({"id": float(row["id"]), "error": {"code": -42, "message": "proper-error"}})
        with self.assertRaisesRegex(AppServerError, "proper-error"):
            client.request("fixture/float-error", timeout=1)
        self.assert_retired(client)

    def test_immediate_reply_during_write_is_retained(self):
        client, process = self.client()
        process.reply = lambda row: process.stdout.emit({"id": row["id"], "result": "proper"})
        self.assertEqual(client.request("fixture/immediate", timeout=1), "proper")
        self.assert_retired(client)

    def test_request_waiting_for_write_slot_cannot_accept_reply(self):
        client, process = self.client()
        gate = ObservedLock()
        client._write_lock = gate
        process.reply = lambda row: process.stdout.emit({"id": row["id"], "result": "proper"})
        gate.lock.acquire()
        thread, values, errors = self.launch(client)
        poison = {"id": 1, "result": "before-write-slot"}
        try:
            self.assertTrue(gate.entered.wait(1))
            self.assertEqual(process.sent, [])
            process.stdout.emit(poison)
            cached_before_write = dict(client._responses)
            pending_before_write = set(getattr(client, "_pending", set()))
        finally:
            gate.lock.release()
            thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(cached_before_write, {})
        self.assertEqual(pending_before_write, set())
        self.assertEqual(values, ["proper"])
        self.assertEqual(errors, [])
        self.assertEqual(list(client._notifications), [poison])
        self.assert_retired(client)

    def test_journal_preparation_does_not_admit_reply(self):
        client, process = self.client()
        entered, release = threading.Event(), threading.Event()

        def record(direction, _message):
            if direction == "send_prepared":
                entered.set()
                if not release.wait(2):
                    raise TimeoutError("fixture journal not released")

        client._record = record
        process.reply = lambda row: process.stdout.emit({"id": row["id"], "result": "proper"})
        thread, values, errors = self.launch(client)
        poison = {"id": 1.0, "result": "before-journal-completion"}
        try:
            self.assertTrue(entered.wait(1))
            process.stdout.emit(poison)
            cached_before_write = dict(client._responses)
            self.assertEqual(process.sent, [])
        finally:
            release.set()
            thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(cached_before_write, {})
        self.assertEqual(values, ["proper"])
        self.assertEqual(errors, [])
        self.assertEqual(list(client._notifications), [poison])
        self.assert_retired(client)

    def test_duplicate_cannot_replace_first_terminal_reply(self):
        client, process = self.client()
        duplicate = {"id": 1.0, "error": {"message": "duplicate"}}

        def reply(row):
            process.stdout.emit({"id": row["id"], "result": "first"})
            process.stdout.emit(duplicate)

        process.reply = reply
        self.assertEqual(client.request("fixture/duplicate", timeout=1), "first")
        self.assertEqual(list(client._notifications), [duplicate])
        self.assert_retired(client)

    def test_foreign_ids_and_method_envelopes_do_not_correlate(self):
        client, process = self.client()
        packets = [{"id": value, "result": "foreign"} for value in (True, False, "1", None, 1.5, [], {}, float("inf"), float("nan"))]
        packets.append({"id": 1, "method": "fixture/server-request"})

        def reply(row):
            for packet in packets:
                process.stdout.emit(packet)
            process.stdout.emit({"id": row["id"], "result": "proper"})

        process.reply = reply
        self.assertEqual(client.request("fixture/noise", timeout=1), "proper")
        self.assertEqual(len(client._notifications), len(packets))
        self.assert_retired(client)

    def test_future_id_is_not_cached_for_later_request(self):
        client, process = self.client()
        future = {"id": 2, "result": "future"}

        def reply(row):
            process.stdout.emit(future)
            process.stdout.emit({"id": row["id"], "result": "proper"})

        process.reply = reply
        self.assertEqual(client.request("fixture/first", timeout=1), "proper")
        self.assert_retired(client)
        self.assertEqual(list(client._notifications), [future])

    def test_concurrent_requests_accept_reverse_response_order(self):
        client, process = self.client()
        issued = threading.Event()
        rows = []

        def reply(message):
            rows.append(message)
            if len(rows) == 2:
                issued.set()

        process.reply = reply
        calls = [self.launch(client, label) for label in ("first", "second")]
        try:
            self.assertTrue(issued.wait(1))
            for row in reversed(rows):
                process.stdout.emit({"id": float(row["id"]), "result": row["method"]})
        finally:
            for thread, _, _ in calls:
                thread.join(2)
        for label, (thread, values, errors) in zip(("first", "second"), calls):
            self.assertFalse(thread.is_alive())
            self.assertEqual(values, [label])
            self.assertEqual(errors, [])
        self.assert_retired(client)

    def test_timeout_retires_id_and_late_reply_is_not_cached(self):
        client, process = self.client()
        with self.assertRaises(TimeoutError):
            client.request("fixture/timeout", timeout=0.01)
        late = {"id": 1.0, "result": "late"}
        process.stdout.emit(late)
        self.assert_retired(client)
        self.assertEqual(list(client._notifications), [late])
        self.assertEqual(len(process.sent), 1)

    def test_eof_retires_request(self):
        client, process = self.client()
        process.reply = lambda _row: process.stdout.finish()
        with self.assertRaisesRegex(AppServerError, "closed during"):
            client.request("fixture/eof", timeout=1)
        self.assert_retired(client)

    def test_serialization_and_journal_errors_do_not_send(self):
        for fault in ("serialization", "journal"):
            with self.subTest(fault=fault):
                client, process = self.client()
                params = {"bad": object()} if fault == "serialization" else None
                if fault == "journal":
                    def fail(*_):
                        raise OSError("fixture journal failed")
                    client._record = fail
                with self.assertRaises(TypeError if fault == "serialization" else OSError):
                    client.request("fixture/failure", params=params, timeout=1)
                self.assertEqual(process.sent, [])
                self.assert_retired(client)

    def test_prewrite_postwrite_and_baseexception_retire_without_resend(self):
        for fault in ("before-write", "after-write", "interrupt-after-write"):
            with self.subTest(fault=fault):
                client, process = self.client()
                process.dispatch_fault = fault
                process.reply = lambda row: process.stdout.emit({"id": row["id"], "result": "arrived-before-failure"})
                expected = KeyboardInterrupt if fault == "interrupt-after-write" else module.AppServerWriteUncertain
                with self.assertRaises(expected) as raised:
                    client.request("fixture/failure", timeout=1)
                if fault == "after-write":
                    self.assertIsInstance(raised.exception.__cause__, OSError)
                if fault == "interrupt-after-write":
                    self.assertIsInstance(raised.exception, KeyboardInterrupt)
                self.assert_retired(client)
                process.dispatch_fault = None
                process.stdout.emit({"id": 1, "result": "late"})
                self.assert_retired(client)
                self.assertEqual(len(process.sent), 1 if fault != "before-write" else 0)


if __name__ == "__main__":
    unittest.main()
