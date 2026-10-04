"""Single-attempt adapter from compiled target requests to stopped_socket_v2.

This adapter returns success only after the socket bridge reports a flushed
command and the matching action's terminal event confirms verified release.
It performs no retry: a transport error leaves the action outcome unknown.
"""

from __future__ import annotations

import json
import socket
import copy
from pathlib import Path
import os
import threading
from typing import Callable


_MAX_SOCKET_RESPONSE_BYTES = 1_048_576


class SocketSubmitStop(RuntimeError):
    """Fail-closed socket boundary; the request must not be resent."""


class JsonlTraceSink:
    """Exclusive append-only trace file, fsynced after every JSONL record.

    The parent directory must already exist. Existing files are never appended
    to or replaced, so each benchmark invocation needs a fresh output path.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        flags |= getattr(os, "O_NOFOLLOW", 0)
        self.fd = os.open(self.path, flags, 0o600)
        self.closed = False
        self.lock = threading.Lock()

    def __call__(self, record: dict) -> None:
        payload = json.dumps(record, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False).encode("utf-8") + b"\n"
        with self.lock:
            if self.closed:
                raise ValueError("trace sink is closed")
            remaining = memoryview(payload)
            while remaining:
                written = os.write(self.fd, remaining)
                if written <= 0:
                    raise OSError("trace write made no progress")
                remaining = remaining[written:]
            os.fsync(self.fd)

    def close(self) -> None:
        with self.lock:
            if self.closed:
                return
            try:
                os.fsync(self.fd)
            finally:
                os.close(self.fd)
                self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


class TargetSocketSubmitter:
    def __init__(self, socket_path: str | Path, *, after: int = 0,
                 timeout_s: float = 5.0,
                 trace_sink: Callable[[dict], None]):
        self.socket_path = str(socket_path)
        if not self.socket_path:
            raise ValueError("Unix socket path required")
        if type(after) is not int or after < 0:
            raise ValueError("nonnegative event cursor required")
        if type(timeout_s) not in (int, float) or not 0 < timeout_s <= 30:
            raise ValueError("socket wait must be in (0, 30] seconds")
        if not callable(trace_sink):
            raise ValueError("pre-send trace sink required")
        self.cursor = after
        self.timeout_s = float(timeout_s)
        self.used_action_ids: set[str] = set()
        self.trace_sink = trace_sink
        self.trace_events: list[dict] = []
        self._submit_lock = threading.Lock()

    def __call__(self, command: dict) -> dict:
        # A socket cursor is shared by this submitter instance. Serialize the
        # full exchange so concurrent callers cannot race action consumption,
        # observe the same cursor, or interleave input actions.
        with self._submit_lock:
            return self._submit_once(command)

    def _submit_once(self, command: dict) -> dict:
        if (type(command) is not dict or command.get("op") != "submit"
                or type(command.get("id")) is not str or not command["id"]):
            raise SocketSubmitStop("one identified submit command required")
        action_id = command["id"]
        if action_id in self.used_action_ids:
            raise SocketSubmitStop("socket action already consumed; no retry")

        # Consume before connect/send. A timeout or broken connection may have
        # happened after the bridge forwarded the command.
        self.used_action_ids.add(action_id)
        request = {
            "after": self.cursor,
            "events": ["terminal", "rejected"],
            "timeout": self.timeout_s,
            "action_id": action_id,
            "request_id": action_id,
            "command": command,
        }
        self._journal("submit_prepared", {
            "action_id": action_id,
            "request_id": action_id,
            "cursor_before": self.cursor,
            "request": request,
        })
        try:
            response = self._exchange(request)
        except Exception as error:
            self._journal("transport_outcome_unknown", {
                "action_id": action_id,
                "error_type": type(error).__name__,
            })
            if isinstance(error, SocketSubmitStop):
                raise
            raise SocketSubmitStop(
                "socket outcome unknown; action consumed without retry") from error

        # Preserve the complete response before interpreting it. A downstream
        # rejection therefore cannot erase the evidence that the bridge returned.
        self._journal("socket_response", {
            "action_id": action_id,
            "request_id": action_id,
            "response": response,
        })

        if type(response) is not dict:
            raise SocketSubmitStop("socket response object required")
        if (response.get("authority") != "none"
                or response.get("acknowledgement") != "not implied"):
            raise SocketSubmitStop("socket event response must remain non-authorizing")
        receipt = response.get("command_receipt")
        if (type(receipt) is not dict
                or receipt.get("request_id") != action_id
                or receipt.get("state") != "stdin_flushed"
                or receipt.get("replayed") is not False):
            raise SocketSubmitStop("fresh matching stdin-flush receipt required")
        records = response.get("records")
        if type(records) is not list:
            raise SocketSubmitStop("socket event record list required")
        terminals = [record for record in records
                     if type(record) is dict
                     and record.get("event") == "terminal"
                     and record.get("id") == action_id]
        if response.get("status") != "boundary" or len(terminals) != 1:
            raise SocketSubmitStop("matching terminal action boundary required")
        terminal = terminals[0]
        release = terminal.get("release")
        if (type(release) is not dict
                or set(release) != {"verified", "keys_down", "buttons_down"}
                or release.get("verified") is not True
                or type(release.get("keys_down")) is not list
                or type(release.get("buttons_down")) is not list
                or release["keys_down"] != []
                or release["buttons_down"] != []):
            raise SocketSubmitStop(
                "matching terminal must verify empty held-input sets")
        cursor = response.get("cursor")
        if type(cursor) is not int or cursor <= self.cursor:
            raise SocketSubmitStop("advancing socket event cursor required")
        self.cursor = cursor
        return {"request_id": action_id, "terminal": True, "released": True}

    def _journal(self, event: str, fields: dict) -> None:
        record = {"schema": "target-socket-submit-trace-v1",
                  "event": event, **copy.deepcopy(fields)}
        self.trace_events.append(record)
        try:
            self.trace_sink(copy.deepcopy(record))
        except Exception as error:
            raise SocketSubmitStop(
                "socket trace sink failed; action consumed without retry") from error

    def _exchange(self, request: dict) -> dict:
        payload = json.dumps(request, separators=(",", ":"),
                             allow_nan=False).encode("utf-8") + b"\n"
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(self.timeout_s + 1.0)
            connection.connect(self.socket_path)
            connection.sendall(payload)
            chunks = bytearray()
            while len(chunks) <= _MAX_SOCKET_RESPONSE_BYTES:
                chunk = connection.recv(min(
                    65536, _MAX_SOCKET_RESPONSE_BYTES + 1 - len(chunks)))
                if not chunk:
                    break
                chunks.extend(chunk)
                if len(chunks) > _MAX_SOCKET_RESPONSE_BYTES:
                    raise SocketSubmitStop("socket response size limit exceeded")
                newline = chunks.find(b"\n")
                if newline >= 0:
                    return json.loads(bytes(chunks[:newline]).decode("utf-8"))
        raise SocketSubmitStop("bounded newline-terminated socket response required")
