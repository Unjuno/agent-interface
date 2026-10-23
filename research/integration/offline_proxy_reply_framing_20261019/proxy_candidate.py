"""Incremental X11 stream parser for an offline-only reply-gate candidate.

This module opens no sockets. A caller can feed bytes read from its existing
proxy relay and decide whether to forward a parsed reply. It fails open when
the relevant request/receipt relationship is unknown.
"""

from __future__ import annotations

from dataclasses import dataclass

from .reply_gate import FrameError, decode_reply_frame


MAX_FRAME_BYTES = 16 * 1024 * 1024
MAX_PENDING_XTEST_QUERIES = 64


@dataclass(frozen=True)
class RequestRecord:
    connection_id: str
    peer_pid: int
    sequence: int
    major_opcode: int
    minor_opcode: int
    role: str
    extension_name: bytes | None = None
    action_id: str | None = None
    keycode: int | None = None


@dataclass(frozen=True)
class ServerRecord:
    connection_id: str
    peer_pid: int
    frame: bytes
    response_type: int
    sequence: int | None


def _units(frame: bytes, byte_order: str, offset: int, size: int) -> int:
    return int.from_bytes(frame[offset:offset + size], byte_order)


def _frame_length(buffer: bytearray, byte_order: str) -> int | None:
    if len(buffer) < 4:
        return None
    units = _units(buffer, byte_order, 2, 2)
    header_size = 4
    if units == 0:
        if len(buffer) < 8:
            return None
        units = _units(buffer, byte_order, 4, 4)
        header_size = 8
    if units == 0:
        raise FrameError("zero-length X11 frame")
    length = units * 4
    if length < header_size or length > MAX_FRAME_BYTES:
        raise FrameError("X11 frame length outside supported bound")
    return length


class X11ProxyConnection:
    """Track one accepted X11 connection and one expected action."""

    def __init__(self, connection_id: str, peer_pid: int, *, owner_pid: int,
                 action_id: str) -> None:
        if not connection_id or peer_pid < 1 or owner_pid < 1 or not action_id:
            raise ValueError("connection, peer, owner and action identities are required")
        self.connection_id = connection_id
        self.peer_pid = peer_pid
        self.owner_pid = owner_pid
        self.action_id = action_id
        self.byte_order: str | None = None
        self._client = bytearray()
        self._server = bytearray()
        self._client_setup_complete = False
        self._server_setup_complete = False
        self._server_setup_failed = False
        self._next_sequence = 0
        self._xtest_query_sequences: dict[int, int] = {}
        self._query_mapping_ambiguous = False
        self.xtest_major_opcode: int | None = None
        self._pending_press: tuple[str, int] | None = None
        self.target: RequestRecord | None = None

    def feed_client(self, data: bytes) -> tuple[RequestRecord, ...]:
        self._client.extend(data)
        records: list[RequestRecord] = []
        if not self._client_setup_complete:
            if len(self._client) < 12:
                return ()
            marker = self._client[0]
            if marker == ord("l"):
                self.byte_order = "little"
            elif marker == ord("B"):
                self.byte_order = "big"
            else:
                raise FrameError("invalid X11 byte-order marker")
            byte_order = self.byte_order
            name_length = _units(self._client, byte_order, 6, 2)
            data_length = _units(self._client, byte_order, 8, 2)
            auth_length = 12 + ((name_length + 3) & ~3) + ((data_length + 3) & ~3)
            if auth_length > MAX_FRAME_BYTES:
                raise FrameError("X11 setup authentication exceeds supported bound")
            if len(self._client) < auth_length:
                return ()
            del self._client[:auth_length]
            self._client_setup_complete = True
        assert self.byte_order is not None
        while self._client:
            length = _frame_length(self._client, self.byte_order)
            if length is None or len(self._client) < length:
                break
            frame = bytes(self._client[:length])
            del self._client[:length]
            records.append(self._record_request(frame))
        return tuple(records)

    def _record_request(self, frame: bytes) -> RequestRecord:
        assert self.byte_order is not None
        if not self._server_setup_complete:
            raise FrameError("client request arrived before X11 setup response")
        major, minor = frame[0], frame[1]
        role = "other"
        extension_name = None
        action_id = None
        keycode = None
        if major == 98 and len(frame) >= 8:
            name_length = _units(frame, self.byte_order, 4, 2)
            padded_end = 8 + ((name_length + 3) & ~3)
            if padded_end == len(frame):
                extension_name = frame[8:8 + name_length]
                role = "query_extension"
        elif (self.xtest_major_opcode is not None
              and major == self.xtest_major_opcode and minor == 2
              and len(frame) == 36 and frame[4] in (2, 3)):
            keycode = frame[5]
            if frame[4] == 2:
                role = "xtest_key_press"
                action_id = self.action_id
            else:
                role = "xtest_key_release"
                pending = self._pending_press
                if pending is None or pending[1] != keycode:
                    self._pending_press = None
                # A matching release completes the same chord; keep the press
                # association until its immediate synchronization request.
        elif major == 106 and len(frame) == 4:
            role = "get_pointer_control"
            if self._pending_press is not None:
                action_id, keycode = self._pending_press
                self.target = None
                self._pending_press = None
        else:
            self._pending_press = None

        self._next_sequence += 1
        if self._next_sequence > 0xFFFFFFFF:
            raise FrameError("X11 request sequence exceeds supported epoch")
        record = RequestRecord(
            self.connection_id, self.peer_pid, self._next_sequence, major, minor,
            role, extension_name, action_id, keycode)
        if record.sequence > 0xFFFF:
            # A 16-bit reply serial can now alias an earlier request. Do not
            # keep a stale target eligible after crossing the first epoch.
            self.target = None
        wire_sequence = record.sequence & 0xFFFF
        if role == "query_extension" and extension_name == b"XTEST":
            if (wire_sequence in self._xtest_query_sequences
                    or len(self._xtest_query_sequences) >= MAX_PENDING_XTEST_QUERIES):
                self._query_mapping_ambiguous = True
                self._xtest_query_sequences.clear()
            elif not self._query_mapping_ambiguous:
                self._xtest_query_sequences[wire_sequence] = record.sequence
        if role == "xtest_key_press":
            self._pending_press = (self.action_id, keycode or 0)
        if role == "get_pointer_control" and action_id is not None:
            self.target = record
        return record

    def feed_server(self, data: bytes) -> tuple[ServerRecord, ...]:
        self._server.extend(data)
        if not self._server_setup_complete and not self._server_setup_failed:
            if len(self._server) < 8:
                return ()
            status = self._server[0]
            if status not in (0, 1, 2):
                raise FrameError("invalid X11 setup response status")
            byte_order = self.byte_order
            if byte_order is None:
                raise FrameError("server setup arrived before client byte order")
            length = 8 + _units(self._server, byte_order, 6, 2) * 4
            if length > MAX_FRAME_BYTES:
                raise FrameError("X11 server setup exceeds supported bound")
            if len(self._server) < length:
                return ()
            del self._server[:length]
            if status == 1:
                self._server_setup_complete = True
            else:
                self._server_setup_failed = True
                return ()
        if self._server_setup_failed:
            return ()
        assert self.byte_order is not None
        records: list[ServerRecord] = []
        while self._server:
            if len(self._server) < 32:
                break
            response_type = self._server[0] & 0x7F
            if response_type in (1, 35):
                length = 32 + _units(self._server, self.byte_order, 4, 4) * 4
            else:
                length = 32
            if length > MAX_FRAME_BYTES:
                raise FrameError("X11 server frame exceeds supported bound")
            if len(self._server) < length:
                break
            frame = bytes(self._server[:length])
            del self._server[:length]
            sequence = int.from_bytes(frame[2:4], self.byte_order)
            record = ServerRecord(self.connection_id, self.peer_pid, frame,
                                  response_type, sequence)
            records.append(record)
            self._observe_reply(record)
        return tuple(records)

    def _observe_reply(self, server: ServerRecord) -> None:
        if server.response_type != 1 or server.sequence is None:
            return
        if self._query_mapping_ambiguous:
            return
        full_sequence = self._xtest_query_sequences.get(server.sequence)
        if full_sequence is None:
            return
        frame = server.frame
        if len(frame) < 32:
            return
        del self._xtest_query_sequences[server.sequence]
        if frame[8] == 1:
            self.xtest_major_opcode = frame[9]

    def should_withhold(self, frame: bytes, *, action_id: str, keycode: int,
                        peer_pid: int, independently_observed: bool) -> bool:
        if self.byte_order is None or self.target is None:
            return False
        try:
            response_type, sequence = decode_reply_frame(frame, self.byte_order)
        except FrameError:
            return False
        target = self.target
        return (
            independently_observed
            and response_type == 1
            and peer_pid == self.owner_pid == self.peer_pid
            and target.connection_id == self.connection_id
            and target.peer_pid == peer_pid
            and target.sequence <= 0xFFFF
            and sequence == target.sequence
            and target.role == "get_pointer_control"
            and target.action_id == action_id
            and target.keycode == keycode
        )
