"""Test-only socket relay for exercising the offline X11 parser candidate.

This module accepts only caller-supplied sockets. It never opens a display,
connects to an X server, injects input, or claims physical release. Tests use
socketpair endpoints and a fake upstream.
"""

from __future__ import annotations

import json
import selectors
import socket
import time
from dataclasses import dataclass

from .proxy_candidate import FrameError, X11ProxyConnection


@dataclass(frozen=True)
class TerminalReport:
    retirement_reason: str
    release_state: str = "UNKNOWN"
    task_success: bool | None = None
    replay_enabled: bool = False
    independently_observed: bool = False
    held_reply_bytes: int = 0


class FakeSocketRelay:
    """Bounded relay fixture around an already-established X11 connection."""

    def __init__(self, tracker: X11ProxyConnection, client: socket.socket,
                 upstream: socket.socket, event_reader: socket.socket, *,
                 owner_pid: int, action_id: str, keycode: int,
                 reply_timeout: float = 0.1,
                 max_pending_bytes: int = 64 * 1024) -> None:
        if owner_pid < 1 or not action_id or not 0 <= keycode <= 255:
            raise ValueError("owner and action identities plus keycode are required")
        if reply_timeout <= 0 or max_pending_bytes < 32:
            raise ValueError("relay bounds must be positive and fit one X11 frame")
        self.tracker = tracker
        self.client = client
        self.upstream = upstream
        self.event_reader = event_reader
        self.owner_pid = owner_pid
        self.action_id = action_id
        self.keycode = keycode
        self.reply_timeout = reply_timeout
        self.max_pending_bytes = max_pending_bytes
        self.terminal_report: TerminalReport | None = None
        self._selector: selectors.BaseSelector | None = None
        self._to_upstream = bytearray()
        self._to_client = bytearray()
        self._server_frames = bytearray()
        self._event_bytes = bytearray()
        self._held_reply = bytearray()
        self._held_deadline: float | None = None
        self._independent_event = False
        self._client_parser_enabled = True
        self._server_parser_enabled = True
        self._retired = False

    def run(self) -> None:
        """Pump the three local socket channels until EOF, fault, or deadline."""
        selector = selectors.DefaultSelector()
        self._selector = selector
        for stream in (self.client, self.upstream, self.event_reader):
            stream.setblocking(False)
        selector.register(self.client, selectors.EVENT_READ, "client_read")
        selector.register(self.upstream, selectors.EVENT_READ, "upstream_read")
        selector.register(self.event_reader, selectors.EVENT_READ, "event_read")
        try:
            while not self._retired:
                now = time.monotonic()
                if self._held_deadline is not None and now >= self._held_deadline:
                    self._retire("held_reply_deadline")
                    break
                self._set_write_interest(self.upstream, "upstream_write",
                                         bool(self._to_upstream))
                self._set_write_interest(self.client, "client_write",
                                         bool(self._to_client))
                timeout = 0.05
                if self._held_deadline is not None:
                    timeout = max(0.0, min(timeout, self._held_deadline - now))
                for key, mask in selector.select(timeout):
                    stream = key.fileobj
                    if mask & selectors.EVENT_READ:
                        if stream is self.client:
                            self._read(stream, "client_read")
                        elif stream is self.upstream:
                            self._read(stream, "upstream_read")
                        else:
                            self._read(stream, "event_read")
                    if self._retired:
                        break
                    if mask & selectors.EVENT_WRITE:
                        if stream is self.upstream:
                            self._flush(stream, "upstream_write")
                        elif stream is self.client:
                            self._flush(stream, "client_write")
                    if self._retired:
                        break
        except (OSError, ValueError, KeyError):
            self._retire("relay_io_error")
        finally:
            selector.close()
            self._selector = None
            for stream in (self.client, self.upstream, self.event_reader):
                try:
                    stream.close()
                except OSError:
                    pass

    def _set_write_interest(self, stream: socket.socket, kind: str,
                            enabled: bool) -> None:
        assert self._selector is not None
        try:
            key = self._selector.get_key(stream)
        except KeyError:
            return
        is_write = key.data == kind
        if enabled and not is_write:
            self._selector.modify(stream, selectors.EVENT_READ | selectors.EVENT_WRITE,
                                  kind)
        elif not enabled and is_write:
            read_kind = "client_read" if stream is self.client else "upstream_read"
            self._selector.modify(stream, selectors.EVENT_READ, read_kind)

    def _read(self, stream: socket.socket, kind: str) -> None:
        try:
            data = stream.recv(65536)
        except BlockingIOError:
            return
        if not data:
            if kind == "event_read":
                assert self._selector is not None
                self._selector.unregister(stream)
                return
            self._retire("client_eof" if kind == "client_read" else "upstream_eof")
            return
        if kind == "client_read":
            if self._client_parser_enabled:
                try:
                    self.tracker.feed_client(data)
                except FrameError:
                    # Preserve the byte stream; never drop bytes on parser error.
                    self._client_parser_enabled = False
            self._enqueue(self._to_upstream, data)
        elif kind == "upstream_read":
            self._receive_server(data)
        else:
            self._receive_event(data)

    def _receive_server(self, data: bytes) -> None:
        self._server_frames.extend(data)
        if not self._server_parser_enabled:
            raw = bytes(self._server_frames)
            self._server_frames.clear()
            if self._held_deadline is not None:
                self._hold_frame(raw)
            else:
                self._enqueue(self._to_client, raw)
            return
        try:
            records = self.tracker.feed_server(data)
        except FrameError:
            # Parser failure switches to byte-preserving forwarding.
            self._server_parser_enabled = False
            raw = bytes(self._server_frames)
            self._server_frames.clear()
            if self._held_deadline is not None:
                self._hold_frame(raw)
            else:
                self._enqueue(self._to_client, raw)
            return
        for record in records:
            frame = record.frame
            if not self._server_frames.startswith(frame):
                self._server_parser_enabled = False
                self._enqueue(self._to_client, bytes(self._server_frames))
                self._server_frames.clear()
                return
            del self._server_frames[:len(frame)]
            if self._held_deadline is not None:
                self._hold_frame(frame)
                if self._retired:
                    return
                continue
            withhold = self.tracker.should_withhold(
                frame, action_id=self.action_id, keycode=self.keycode,
                peer_pid=record.peer_pid,
                independently_observed=self._independent_event)
            if withhold:
                self._hold_frame(frame)
                if self._retired:
                    return
            else:
                self._enqueue(self._to_client, frame)
        if len(self._server_frames) > self.max_pending_bytes:
            self._retire("incomplete_frame_limit")

    def _receive_event(self, data: bytes) -> None:
        self._event_bytes.extend(data)
        if len(self._event_bytes) > self.max_pending_bytes:
            self._event_bytes.clear()
            return
        while b"\n" in self._event_bytes:
            line, _, remainder = self._event_bytes.partition(b"\n")
            self._event_bytes = bytearray(remainder)
            try:
                receipt = json.loads(line)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if (isinstance(receipt, dict)
                    and receipt.get("action_id") == self.action_id
                    and receipt.get("event") == "KeyPress"
                    and receipt.get("keycode") == self.keycode):
                self._independent_event = True

    def _enqueue(self, target: bytearray, data: bytes) -> None:
        if target is self._to_upstream:
            self._flush(self.upstream, "upstream_write")
        elif target is self._to_client:
            self._flush(self.client, "client_write")
        if len(target) + len(data) > self.max_pending_bytes:
            self._retire("backpressure_limit")
            return
        target.extend(data)
        if target is self._to_upstream:
            self._flush(self.upstream, "upstream_write")
        elif target is self._to_client:
            self._flush(self.client, "client_write")

    def _hold_frame(self, frame: bytes) -> None:
        self._held_reply.extend(frame)
        if self._held_deadline is None:
            self._held_deadline = time.monotonic() + self.reply_timeout
        if len(self._held_reply) > self.max_pending_bytes:
            self._retire("held_reply_limit")

    def _flush(self, stream: socket.socket, kind: str) -> None:
        queue = self._to_upstream if kind == "upstream_write" else self._to_client
        if not queue:
            return
        try:
            sent = stream.send(queue)
        except BlockingIOError:
            return
        if sent <= 0:
            self._retire("relay_io_error")
            return
        del queue[:sent]

    def _retire(self, reason: str) -> None:
        if self._retired:
            return
        self._retired = True
        self.terminal_report = TerminalReport(
            retirement_reason=reason,
            independently_observed=self._independent_event,
            held_reply_bytes=len(self._held_reply))

