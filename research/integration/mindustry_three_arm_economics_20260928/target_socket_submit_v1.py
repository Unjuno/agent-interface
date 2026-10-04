"""Single-attempt adapter from compiled target requests to stopped_socket_v2.

This adapter returns success only after the socket bridge reports a flushed
command and the matching action's terminal event confirms verified release.
It performs no retry: a transport error leaves the action outcome unknown.
"""

from __future__ import annotations

import json
import socket
from pathlib import Path


class SocketSubmitStop(RuntimeError):
    """Fail-closed socket boundary; the request must not be resent."""


class TargetSocketSubmitter:
    def __init__(self, socket_path: str | Path, *, after: int = 0,
                 timeout_s: float = 5.0):
        self.socket_path = str(socket_path)
        if not self.socket_path:
            raise ValueError("Unix socket path required")
        if type(after) is not int or after < 0:
            raise ValueError("nonnegative event cursor required")
        if type(timeout_s) not in (int, float) or not 0 < timeout_s <= 30:
            raise ValueError("socket wait must be in (0, 30] seconds")
        self.cursor = after
        self.timeout_s = float(timeout_s)
        self.used_action_ids: set[str] = set()

    def __call__(self, command: dict) -> dict:
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
        try:
            response = self._exchange(request)
        except (OSError, TimeoutError, UnicodeError, json.JSONDecodeError) as error:
            raise SocketSubmitStop(
                "socket outcome unknown; action consumed without retry") from error

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
        if type(release) is not dict or release.get("verified") is not True:
            raise SocketSubmitStop("matching terminal must verify input release")
        cursor = response.get("cursor")
        if type(cursor) is not int or cursor <= self.cursor:
            raise SocketSubmitStop("advancing socket event cursor required")
        self.cursor = cursor
        return {"request_id": action_id, "terminal": True, "released": True}

    def _exchange(self, request: dict) -> dict:
        payload = json.dumps(request, separators=(",", ":"),
                             allow_nan=False).encode("utf-8") + b"\n"
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(self.timeout_s + 1.0)
            connection.connect(self.socket_path)
            connection.sendall(payload)
            chunks = bytearray()
            while len(chunks) <= 1_048_576:
                chunk = connection.recv(65536)
                if not chunk:
                    break
                chunks.extend(chunk)
                newline = chunks.find(b"\n")
                if newline >= 0:
                    return json.loads(bytes(chunks[:newline]).decode("utf-8"))
        raise SocketSubmitStop("bounded newline-terminated socket response required")
