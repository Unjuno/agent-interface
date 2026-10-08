"""Journaled synchronous client for the Codex app-server JSONL protocol."""
from collections import deque
import json
import math
import os
import select
import signal
import subprocess
import sys
import threading
import time


class AppServerError(RuntimeError):
    pass


class AppServerUnsupportedRuntime(AppServerError):
    """The interpreter cannot provide the required bounded pipe-send API."""


def _require_pipe_runtime():
    if os.name == "nt" and sys.version_info[:2] < (3, 12):
        raise AppServerUnsupportedRuntime(
            "app-server bounded pipe sends require Python 3.12 or later on Windows")
    if not callable(getattr(os, "set_blocking", None)):
        raise AppServerUnsupportedRuntime(
            "app-server bounded pipe sends require callable os.set_blocking")


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
        _require_pipe_runtime()
        self._journal = None if journal_path is None else open(journal_path, "x", encoding="utf-8")
        self._journal_lock = threading.Lock()
        self._owns_process_group = os.name == "posix" and process_factory is subprocess.Popen
        process_options = {
            "cwd": cwd, "stdin": subprocess.PIPE, "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE, "text": True, "encoding": "utf-8",
            "errors": "strict", "bufsize": 1,
        }
        if self._owns_process_group:
            process_options["start_new_session"] = True
        try:
            self.process = process_factory(command, **process_options)
        except BaseException as startup_error:
            try:
                if self._journal is not None:
                    self._journal.close()
            except BaseException as cleanup_error:
                raise startup_error from cleanup_error
            raise
        self._condition = threading.Condition()
        self._write_lock = threading.Lock()
        self._journal_order_lock = threading.Lock()
        self._send_uncertain = False
        self._stdin_fd = None
        self._closing = False
        self._responses = {}
        self._pending = set()
        self._notifications = deque()
        self._next_id = 1
        self._closed = False
        self._reader = threading.Thread(target=self._read, daemon=True)
        self._reader.start()

    def _read(self):
        try:
            for line in self.process.stdout:
                message = json.loads(line)
                with self._journal_order_lock:
                    self._record("received", message)
                with self._condition:
                    if ("id" in message and "method" not in message and
                            type(message["id"]) in (int, float) and
                            message["id"] in self._pending and
                            message["id"] not in self._responses):
                        self._responses[message["id"]] = message
                    else:
                        self._notifications.append(message)
                    self._condition.notify_all()
        finally:
            with self._condition:
                self._closed = True
                self._condition.notify_all()

    def _write(self, message, *, deadline=None, request_id=None):
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
            with self._condition:
                if self._closed or self._closing:
                    raise AppServerError("app-server closed before send: stderr not drained")
            if self._stdin_fd is None:
                try:
                    fd = self.process.stdin.fileno()
                except (AttributeError, OSError) as error:
                    raise AppServerUnsupportedRuntime(
                        "app-server stdin must expose a nonblocking-capable pipe descriptor") from error
                # Unsupported pipe modes fail before journaling or sending.
                # Windows pipe support requires Python 3.12 or later.
                os.set_blocking(fd, False)
                self._stdin_fd = fd
            snapshot = json.loads(data)
            # The durable preparation row gates admission and the pipe write,
            # but does not claim bytes reached the peer.
            self._record("send_prepared", snapshot)
            if deadline <= time.monotonic():
                raise TimeoutError("app-server send budget expired; no send attempted")
            if request_id is not None:
                # Preserve reply ownership only after serialized send preparation.
                with self._condition:
                    self._pending.add(request_id)
            sent = 0
            write_attempted = False
            view = memoryview(data)
            journal_order_locked = False
            try:
                while sent < len(data):
                    if self._closing:
                        raise AppServerError("app-server closed during pipe send")
                    if deadline <= time.monotonic():
                        raise TimeoutError("app-server pipe send timed out")
                    end = min(sent + 65536, len(data))
                    final_chunk = end == len(data)
                    if final_chunk:
                        remaining = deadline - time.monotonic()
                        if remaining <= 0 or not self._journal_order_lock.acquire(timeout=max(0, remaining)):
                            raise TimeoutError("app-server journal ordering lock timed out; no final send attempted")
                        journal_order_locked = True
                        if deadline <= time.monotonic():
                            self._journal_order_lock.release()
                            journal_order_locked = False
                            raise TimeoutError("app-server send budget expired; no final send attempted")
                    try:
                        # Bound each syscall, not the size of the JSON record.
                        write_attempted = True
                        count = os.write(self._stdin_fd, view[sent:end])
                        if count <= 0:
                            raise OSError("app-server pipe write made no progress")
                        sent += count
                    except BlockingIOError:
                        if journal_order_locked:
                            self._journal_order_lock.release()
                            journal_order_locked = False
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            raise TimeoutError("app-server pipe send timed out")
                        if os.name == "nt":
                            # Windows select accepts sockets, not pipe handles.
                            time.sleep(min(.01, remaining))
                        else:
                            # poll has no select FD_SETSIZE descriptor limit.
                            # Cap each millisecond wait to avoid poll integer
                            # overflow for otherwise valid large timeouts.
                            waiter = select.poll()
                            waiter.register(self._stdin_fd, select.POLLOUT)
                            waiter.poll(min(remaining, 1) * 1000)
                    if sent == len(data):
                        # Hold ordering from the final write attempt through its
                        # durable completion row so a fast reply cannot overtake it.
                        self._record("sent", snapshot)
                    elif journal_order_locked:
                        # A partial final-chunk write cannot have completed a
                        # newline-terminated message. Let the reader drain while
                        # waiting for the remaining bytes.
                        self._journal_order_lock.release()
                        journal_order_locked = False
            except BaseException as error:
                if write_attempted:
                    self._send_uncertain = True
                    try:
                        if journal_order_locked:
                            self._record("send_uncertain", {
                                "message": snapshot, "sent_bytes": sent,
                                "total_bytes": len(data), "reason": type(error).__name__,
                            })
                        else:
                            # A failed bounded order-lock acquisition must not
                            # turn uncertainty reporting into an unbounded wait.
                            # _record still serializes journal bytes itself.
                            self._record("send_uncertain", {
                                "message": snapshot, "sent_bytes": sent,
                                "total_bytes": len(data), "reason": type(error).__name__,
                            })
                    except Exception:
                        pass
                if not isinstance(error, Exception):
                    raise
                if not write_attempted:
                    raise
                raise AppServerWriteUncertain(sent, len(data), type(error).__name__) from error
            finally:
                if journal_order_locked:
                    self._journal_order_lock.release()
        finally:
            self._write_lock.release()

    def _record(self, direction, message):
        if self._journal is None:
            return
        with self._journal_lock:
            row = {"direction": direction, "observed_ns": time.perf_counter_ns(),
                   "message": message}
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
        try:
            self._write(message, deadline=deadline, request_id=identifier)
            with self._condition:
                while identifier not in self._responses:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError(f"app-server request timed out: {method}")
                    if self._closed:
                        raise AppServerError(f"app-server closed during {method}: stderr not drained")
                    self._condition.wait(remaining)
                response = self._responses.pop(identifier)
                self._pending.discard(identifier)
            if "error" in response:
                raise AppServerError(f"{method}: {json.dumps(response['error'], sort_keys=True)}")
            return response["result"]
        finally:
            with self._condition:
                self._pending.discard(identifier)
                self._responses.pop(identifier, None)

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
                    raise AppServerError("app-server closed while waiting: stderr not drained")
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

    def _signal_owned_group(self, signum):
        if not getattr(self, "_owns_process_group", False):
            return
        # Reap an exited leader before signaling: Darwin may return EPERM for
        # its unreaped, otherwise empty group. Still signal surviving children.
        self.process.poll()
        try:
            os.killpg(self.process.pid, signum)
        except ProcessLookupError:
            pass
        except PermissionError:
            # The leader can exit between poll and killpg. Reap that race and
            # retry once; a live leader or persistent denial remains an error.
            if self.process.poll() is None:
                raise
            try:
                os.killpg(self.process.pid, signum)
            except ProcessLookupError:
                pass

    def _wait_owned_group(self, timeout):
        if not getattr(self, "_owns_process_group", False):
            return True
        deadline = None if timeout is None else time.monotonic() + max(0, timeout)
        while True:
            try:
                os.killpg(self.process.pid, 0)
            except ProcessLookupError:
                return True
            remaining = None if deadline is None else deadline - time.monotonic()
            if remaining is not None and remaining <= 0:
                return False
            time.sleep(0.01 if remaining is None else min(0.01, remaining))

    def close(self, timeout=5):
        self._closing = True
        deadline = None if timeout is None else time.monotonic() + max(0, timeout)
        owns_process_group = getattr(self, "_owns_process_group", False)
        if owns_process_group:
            # The leader may have exited while descendants still own its pipes.
            self._signal_owned_group(signal.SIGTERM)
            if self.process.poll() is None:
                try:
                    self.process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    self._signal_owned_group(signal.SIGKILL)
                    self.process.wait(timeout=timeout)
            if not self._wait_owned_group(timeout):
                self._signal_owned_group(signal.SIGKILL)
        elif self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=timeout)
        self._reader.join(timeout=timeout)
        if self._reader.is_alive():
            if owns_process_group:
                self._signal_owned_group(signal.SIGKILL)
                self._reader.join(timeout=timeout)
            if self._reader.is_alive():
                raise TimeoutError("app-server reader close timed out")
        # Custom process factories own their stream wrappers and may provide
        # lightweight proxies without the IOBase ``closed``/``close`` API.
        if owns_process_group:
            # Terminate first so a backpressured writer can finish. Never close
            # or recycle its raw descriptor while that writer still owns it.
            write_lock = self._write_lock
            remaining = -1 if deadline is None else max(0, deadline - time.monotonic())
            if not write_lock.acquire(timeout=remaining):
                raise TimeoutError("app-server writer close timed out")
            try:
                for stream_name in ("stdin", "stdout", "stderr"):
                    stream = getattr(self.process, stream_name, None)
                    if stream is not None and not stream.closed:
                        stream.close()
                self._stdin_fd = None
            finally:
                write_lock.release()
        if self._journal is not None and not self._journal.closed:
            if not self._journal_lock.acquire(timeout=-1 if timeout is None else timeout):
                raise TimeoutError("app-server journal close timed out")
            try:
                self._journal.close()
            finally:
                self._journal_lock.release()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
