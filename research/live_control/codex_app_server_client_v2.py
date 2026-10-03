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
                stderr=subprocess.PIPE, text=True, bufsize=1)
        except BaseException as startup_error:
            if self._journal is not None:
                try:
                    self._journal.close()
                except BaseException as cleanup_error:
                    try:
                        BaseException.add_note(
                            startup_error,
                            "journal cleanup failed: " + type(cleanup_error).__name__)
                    except BaseException:
                        pass
            raise
        self._condition = threading.Condition()
        self._write_lock = threading.Lock()
        self._responses = {}
        self._notifications = deque()
        self._next_id = 1
        self._closed = False
        # Own the complete reader access interval, including pending bootstrap.
        reader_access = threading.Lock()
        reader_cancelled = False

        def read_unless_cancelled():
            with reader_access:
                if not reader_cancelled:
                    self._read()

        self._reader = threading.Thread(target=read_unless_cancelled, daemon=True)
        try:
            self._reader.start()
        except BaseException as startup_error:
            def cleanup(action):
                try:
                    action()
                    return True
                except BaseException as cleanup_error:
                    try:
                        BaseException.add_note(startup_error,
                            "thread startup cleanup failed: " + type(cleanup_error).__name__)
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

            def cancel_reader_access():
                nonlocal reader_cancelled
                if not reader_access.acquire(timeout=1):
                    raise TimeoutError("app-server startup reader access did not finish")
                try:
                    # A pending reader may still run, but cannot access resources.
                    reader_cancelled = True
                finally:
                    reader_access.release()

            cleanup(stop_process)
            if cleanup(cancel_reader_access):
                for stream_name in ("stdin", "stdout", "stderr"):
                    cleanup(lambda name=stream_name: getattr(self.process, name).close())
                if self._journal is not None:
                    cleanup(lambda: self._journal.close())
            raise

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
        self._write(message)
        deadline = time.monotonic() + timeout
        with self._condition:
            while identifier not in self._responses:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(f"app-server request timed out: {method}")
                if self._closed:
                    raise AppServerError(f"app-server closed during {method}: stderr not drained")
                self._condition.wait(remaining)
            response = self._responses.pop(identifier)
        if "error" in response:
            raise AppServerError(f"{method}: {json.dumps(response['error'], sort_keys=True)}")
        return response["result"]

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
