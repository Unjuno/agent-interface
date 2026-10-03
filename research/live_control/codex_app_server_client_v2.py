"""Journaled synchronous client for the Codex app-server JSONL protocol."""
from collections import deque
import json
import subprocess
import threading
import time


class AppServerError(RuntimeError):
    pass


class CodexAppServerClient:
    def __init__(self, command, cwd=None, process_factory=subprocess.Popen, journal_path=None):
        self._journal = None if journal_path is None else open(journal_path, "x", encoding="utf-8")
        self._journal_lock = threading.Lock()
        try:
            self.process = process_factory(
                command, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, bufsize=1, encoding="utf-8", errors="strict")
        except BaseException as startup_error:
            try:
                if self._journal is not None:
                    self._journal.close()
            except BaseException as cleanup_error:
                raise startup_error from cleanup_error
            raise
        self._condition = threading.Condition()
        self._write_lock = threading.Lock()
        self._responses = {}
        self._pending = set()
        self._notifications = deque()
        self._next_id = 1
        self._closed = False
        self._stderr_lock = threading.Lock()
        self._stderr_tail = b""
        self._stderr_bytes = 0
        self._stderr_error = None
        self._stderr_complete = False
        # Each independently blocking reader owns its full resource interval.
        access = [threading.Lock(), threading.Lock()]
        cancelled = [False, False]

        def guarded_read(index, action):
            with access[index]:
                if not cancelled[index]:
                    action()

        try:
            self._reader = threading.Thread(
                target=lambda: guarded_read(0, self._read), daemon=True)
            self._reader.start()
            self._stderr_reader = threading.Thread(
                target=lambda: guarded_read(1, self._read_stderr), daemon=True)
            self._stderr_reader.start()
        except BaseException as startup_error:
            def cleanup(action):
                try:
                    action()
                    return True
                except BaseException as cleanup_error:
                    try:
                        BaseException.add_note(startup_error,
                            "reader startup cleanup failed: " + type(cleanup_error).__name__)
                    except BaseException:
                        pass
                    return False

            def stop_process():
                if self.process.poll() is None:
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                        self.process.wait(timeout=1)

            def cancel_access(index):
                if not access[index].acquire(timeout=1):
                    raise TimeoutError("app-server startup reader access did not finish")
                try:
                    # Pending native bootstrap may continue, but skips resource access.
                    cancelled[index] = True
                finally:
                    access[index].release()

            cleanup(stop_process)
            safe = True
            for index in range(2):
                if not cleanup(lambda i=index: cancel_access(i)):
                    safe = False
            if safe:
                for name in ("stdin", "stdout", "stderr"):
                    cleanup(lambda n=name: getattr(self.process, n).close())
                if self._journal is not None:
                    cleanup(self._journal.close)
            raise

    def _read_stderr(self):
        # Drain raw diagnostic bytes independently of protocol/journal locks.
        stream = getattr(self.process.stderr, "buffer", self.process.stderr)
        read = getattr(stream, "read1", stream.read)
        try:
            while True:
                chunk = read(4096)
                if not chunk:
                    with self._stderr_lock:
                        self._stderr_complete = True
                    return
                if isinstance(chunk, str):
                    chunk = chunk.encode("utf-8")
                with self._stderr_lock:
                    self._stderr_bytes += len(chunk)
                    self._stderr_tail = (self._stderr_tail + chunk)[-65536:]
        except Exception as error:
            with self._stderr_lock:
                self._stderr_error = (type(error).__name__ + ": " + str(error))[:1024]

    def stderr_snapshot(self):
        """Return a bounded raw tail; EOF and read failure remain distinct."""
        with self._stderr_lock:
            return {"tail": self._stderr_tail, "bytes_received": self._stderr_bytes,
                    "complete": self._stderr_complete, "error": self._stderr_error}

    def _read(self):
        try:
            for line in self.process.stdout:
                message = json.loads(line)
                self._record("received", message)
                with self._condition:
                    if ("id" in message and "method" not in message and
                            type(message["id"]) is int and message["id"] in self._pending):
                        self._responses[message["id"]] = message
                    else:
                        self._notifications.append(message)
                    self._condition.notify_all()
        finally:
            with self._condition:
                self._closed = True
                self._condition.notify_all()

    def _write(self, message):
        with self._write_lock:
            self._record("sent", message)
            self.process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
            self.process.stdin.flush()

    def _record(self, direction, message):
        if self._journal is None:
            return
        row = {"direction": direction, "observed_ns": time.perf_counter_ns(),
               "message": message}
        with self._journal_lock:
            self._journal.write(json.dumps(row, separators=(",", ":")) + "\n")
            self._journal.flush()

    def request(self, method, params=None, timeout=30):
        with self._condition:
            identifier = self._next_id
            self._next_id += 1
        message = {"method": method, "id": identifier}
        if params is not None:
            message["params"] = params
        with self._condition:
            self._pending.add(identifier)
        try:
            self._write(message)
            deadline = time.monotonic() + timeout
            with self._condition:
                while identifier not in self._responses:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError(f"app-server request timed out: {method}")
                    if self._closed:
                        raise AppServerError(f"app-server closed during {method}: stderr diagnostics captured separately")
                    self._condition.wait(remaining)
                response = self._responses.pop(identifier)
            if "error" in response:
                raise AppServerError(f"{method}: {json.dumps(response['error'], sort_keys=True)}")
            return response["result"]
        finally:
            with self._condition:
                self._pending.discard(identifier)
                self._responses.pop(identifier, None)

    def notify(self, method, params=None):
        message = {"method": method}
        if params is not None:
            message["params"] = params
        self._write(message)

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
                    raise AppServerError("app-server closed while waiting: stderr diagnostics captured separately")
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
        if self._reader.is_alive():
            raise TimeoutError("app-server reader close timed out")
        self._stderr_reader.join(timeout=timeout)
        if self._stderr_reader.is_alive():
            raise TimeoutError("app-server stderr close timed out")
        # Sequential close owns these Popen streams after both readers retire.
        first_error = None

        def cleanup(action):
            nonlocal first_error
            try:
                action()
            except BaseException as error:
                if first_error is None:
                    first_error = error
                else:
                    try:
                        BaseException.add_note(first_error,
                            "additional client close failure: " + type(error).__name__)
                    except BaseException:
                        pass

        def close_journal():
            if self._journal is not None and not self._journal.closed:
                if not self._journal_lock.acquire(timeout=-1 if timeout is None else timeout):
                    raise TimeoutError("app-server journal close timed out")
                try:
                    cleanup(self._journal.close)
                finally:
                    cleanup(self._journal_lock.release)

        cleanup(close_journal)
        for stream_name in ("stdin", "stdout", "stderr"):
            cleanup(lambda name=stream_name: getattr(self.process, name).close())
        if first_error is not None:
            raise first_error

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
