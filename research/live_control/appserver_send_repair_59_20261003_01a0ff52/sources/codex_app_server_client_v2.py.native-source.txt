"""Journaled synchronous client for the Codex app-server JSONL protocol."""
from collections import deque
import json
import math
import os
import select
import subprocess
import threading
import time


class AppServerError(RuntimeError):
    pass


class AppServerWriteUncertain(AppServerError):
    """A pipe send failed; sent bytes are not proof of server acceptance."""

    def __init__(self, sent, total, reason):
        self.sent, self.total, self.reason = sent, total, reason
        super().__init__(f"app-server write uncertain: {sent}/{total} bytes ({reason})")


def _deadline(timeout):
    if (type(timeout) not in (int, float) or not 0 <= timeout <= threading.TIMEOUT_MAX
            or not math.isfinite(timeout)):
        raise ValueError("timeout must be finite, nonnegative and within the lock wait range")
    return time.monotonic() + timeout


class CodexAppServerClient:
    def __init__(self, command, cwd=None, process_factory=subprocess.Popen, journal_path=None):
        self._journal = None if journal_path is None else open(journal_path, "x", encoding="utf-8")
        self._journal_lock = threading.Lock()
        self.process = process_factory(
            command, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, bufsize=1)
        self._condition = threading.Condition()
        self._write_lock = threading.Lock()
        self._send_uncertain = False
        self._stdin_fd = None
        self._responses = {}
        self._notifications = deque()
        self._next_id = 1
        self._closed = False
        self._reader = threading.Thread(target=self._read, daemon=True)
        self._reader.start()

    def _read(self):
        try:
            for line in self.process.stdout:
                message = json.loads(line)
                self._record("received", message)
                with self._condition:
                    if "id" in message:
                        self._responses[message["id"]] = message
                    else:
                        self._notifications.append(message)
                    self._condition.notify_all()
        finally:
            with self._condition:
                self._closed = True
                self._condition.notify_all()

    def _write(self, message, *, deadline=None):
        # This client exclusively owns stdin. Never mix buffered TextIO writes
        # with these direct descriptor writes; retain the wrapper only for close.
        deadline = _deadline(30) if deadline is None else deadline
        data = (json.dumps(message, separators=(",", ":")) + "\n").encode("utf-8")
        remaining = max(0, deadline - time.monotonic())
        if not self._write_lock.acquire(timeout=remaining):
            raise TimeoutError("app-server write lock timed out; no send attempted")
        try:
            if self._send_uncertain:
                raise AppServerWriteUncertain(0, 0, "previous send failure")
            if deadline <= time.monotonic():
                raise TimeoutError("app-server send budget expired; no send attempted")
            if self._stdin_fd is None:
                fd = self.process.stdin.fileno()
                # Unsupported pipe modes fail before journaling or sending.
                # Windows pipe support requires Python 3.12 or later.
                os.set_blocking(fd, False)
                self._stdin_fd = fd
            self._record("sent", message)
            if deadline <= time.monotonic():
                raise TimeoutError("app-server send budget expired; no send attempted")
            sent = 0
            view = memoryview(data)
            try:
                while sent < len(data):
                    if deadline <= time.monotonic():
                        raise TimeoutError("app-server pipe send timed out")
                    try:
                        # Bound each syscall, not the size of the JSON record.
                        count = os.write(self._stdin_fd, view[sent:sent + 65536])
                        if count <= 0:
                            raise OSError("app-server pipe write made no progress")
                        sent += count
                    except BlockingIOError:
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            raise TimeoutError("app-server pipe send timed out")
                        if os.name == "nt":
                            # Windows select accepts sockets, not pipe handles.
                            time.sleep(min(.01, remaining))
                        else:
                            select.select([], [self._stdin_fd], [], remaining)
            except BaseException as error:
                self._send_uncertain = True
                if not isinstance(error, Exception):
                    raise
                raise AppServerWriteUncertain(sent, len(data), type(error).__name__) from error
        finally:
            self._write_lock.release()

    def _record(self, direction, message):
        if self._journal is None:
            return
        row = {"direction": direction, "observed_ns": time.perf_counter_ns(),
               "message": message}
        with self._journal_lock:
            self._journal.write(json.dumps(row, separators=(",", ":")) + "\n")
            self._journal.flush()

    def request(self, method, params=None, timeout=30):
        deadline = _deadline(timeout)
        with self._condition:
            identifier = self._next_id
            self._next_id += 1
        message = {"method": method, "id": identifier}
        if params is not None:
            message["params"] = params
        self._write(message, deadline=deadline)
        with self._condition:
            while identifier not in self._responses:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(f"app-server request timed out: {method}")
                if self._closed:
                    detail = self.process.stderr.read().strip()
                    raise AppServerError(f"app-server closed during {method}: {detail}")
                self._condition.wait(remaining)
            response = self._responses.pop(identifier)
        if "error" in response:
            raise AppServerError(f"{method}: {json.dumps(response['error'], sort_keys=True)}")
        return response["result"]

    def notify(self, method, params=None, timeout=30):
        deadline = _deadline(timeout)
        message = {"method": method}
        if params is not None:
            message["params"] = params
        self._write(message, deadline=deadline)

    def wait_notification(self, predicate, timeout=120):
        deadline = time.monotonic() + timeout
        with self._condition:
            while True:
                for index, message in enumerate(self._notifications):
                    if predicate(message):
                        del self._notifications[index]
                        return message
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("app-server notification timed out")
                if self._closed:
                    detail = self.process.stderr.read().strip()
                    raise AppServerError(f"app-server closed while waiting: {detail}")
                self._condition.wait(remaining)

    def initialize(self, name="agent-interface", version="1"):
        result = self.request("initialize", {
            "clientInfo": {"name": name, "title": "Agent Interface", "version": version},
            "capabilities": {"experimentalApi": False, "requestAttestation": False},
        })
        self.notify("initialized")
        return result

    def start_thread(self, **params):
        return self.request("thread/start", params)

    def start_turn(self, thread_id, inputs, **params):
        payload = {"threadId": thread_id, "input": inputs, **params}
        return self.request("turn/start", payload)

    def interrupt_turn(self, thread_id, turn_id):
        return self.request("turn/interrupt", {"threadId": thread_id, "turnId": turn_id})

    def wait_turn_completed(self, thread_id, turn_id, timeout=120):
        return self.wait_notification(
            lambda row: row.get("method") == "turn/completed" and
            row.get("params", {}).get("threadId") == thread_id and
            row.get("params", {}).get("turn", {}).get("id") == turn_id,
            timeout=timeout)["params"]

    def latest_turn_usage(self, thread_id, turn_id):
        with self._condition:
            matches = [row for row in self._notifications
                       if row.get("method") == "thread/tokenUsage/updated" and
                       row.get("params", {}).get("threadId") == thread_id and
                       row.get("params", {}).get("turnId") == turn_id]
        return None if not matches else matches[-1]["params"]["tokenUsage"]

    def close(self, timeout=5):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=timeout)
        self._reader.join(timeout=timeout)
        if self._journal is not None and not self._journal.closed:
            with self._journal_lock:
                self._journal.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
