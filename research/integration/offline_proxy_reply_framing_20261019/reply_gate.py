"""Offline X11 reply-gate model; it never opens sockets or sends input."""

from __future__ import annotations

from dataclasses import dataclass


class FrameError(ValueError):
    pass


@dataclass(frozen=True)
class Request:
    connection: str
    peer_pid: int
    sequence: int
    role: str
    action_id: str | None
    keycode: int | None


@dataclass(frozen=True)
class Reply:
    connection: str
    peer_pid: int
    sequence: int
    response_type: int


@dataclass(frozen=True)
class KeyPressReceipt:
    action_id: str
    keycode: int


def decode_request_frame(frame: bytes, byte_order: str) -> int:
    """Validate one core request frame and return its byte length."""
    if byte_order not in ("little", "big"):
        raise FrameError("unknown X11 byte order")
    if len(frame) < 4:
        raise FrameError("truncated request header")
    units = int.from_bytes(frame[2:4], byte_order)
    if units == 0:
        if len(frame) < 8:
            raise FrameError("truncated extended request header")
        units = int.from_bytes(frame[4:8], byte_order)
        header_size = 8
    else:
        header_size = 4
    if units == 0:
        raise FrameError("zero-length request")
    expected = units * 4
    if expected < header_size or expected != len(frame):
        raise FrameError("request frame length mismatch")
    return expected


def classify_request_role(frame: bytes, byte_order: str, *,
                          xtest_major_opcode: int | None = None) -> str:
    """Classify only the two request forms used by the frozen caller path."""
    decode_request_frame(frame, byte_order)
    major_opcode = frame[0]
    if major_opcode == 106:
        return "get_pointer_control"
    if (xtest_major_opcode is not None
            and major_opcode == xtest_major_opcode
            and frame[1] == 2
            and len(frame) >= 8
            and frame[4] == 2):
        return "xtest_key_press"
    return "other"


def decode_reply_frame(frame: bytes, byte_order: str) -> tuple[int, int]:
    """Return (response_type, 16-bit sequence) for one complete X11 reply."""
    if byte_order not in ("little", "big"):
        raise FrameError("unknown X11 byte order")
    if len(frame) < 32:
        raise FrameError("truncated reply header")
    response_type = frame[0] & 0x7F
    if response_type != 1:
        raise FrameError("frame is not an X11 reply")
    sequence = int.from_bytes(frame[2:4], byte_order)
    extra_words = int.from_bytes(frame[4:8], byte_order)
    expected = 32 + extra_words * 4
    if len(frame) != expected:
        raise FrameError("reply frame length mismatch")
    return response_type, sequence


class RequestLedger:
    """Assign request sequence numbers independently for each X connection."""

    def __init__(self) -> None:
        self._next: dict[str, int] = {}
        self._requests: dict[tuple[str, int], Request] = {}
        self._pending_input: dict[str, tuple[str, int]] = {}

    def record(self, connection: str, peer_pid: int, frame: bytes, *,
               byte_order: str, role: str | None = None,
               action_id: str | None = None,
               xtest_major_opcode: int | None = None) -> Request:
        decode_request_frame(frame, byte_order)
        role = role or classify_request_role(
            frame, byte_order, xtest_major_opcode=xtest_major_opcode)
        keycode = None
        if role == "xtest_key_press":
            if action_id is None:
                raise FrameError("XTEST key press needs an action identity")
            keycode = frame[5]
            self._pending_input[connection] = (action_id, keycode)
        elif role == "get_pointer_control":
            pending = self._pending_input.pop(connection, None)
            if pending is not None:
                pending_action, pending_keycode = pending
                if action_id is not None and action_id != pending_action:
                    raise FrameError("sync action does not match preceding XTEST press")
                action_id = pending_action
                keycode = pending_keycode
        else:
            self._pending_input.pop(connection, None)
        sequence = self._next.get(connection, 0) + 1
        if sequence > 0xFFFF:
            raise FrameError("sequence wrap requires a separately qualified epoch")
        request = Request(connection, peer_pid, sequence, role, action_id, keycode)
        key = (connection, sequence)
        if key in self._requests:
            raise FrameError("duplicate connection-scoped request sequence")
        self._next[connection] = sequence
        self._requests[key] = request
        return request

    def lookup_reply(self, connection: str, peer_pid: int, frame: bytes,
                     byte_order: str) -> tuple[Reply, Request | None]:
        response_type, sequence = decode_reply_frame(frame, byte_order)
        request = self._requests.get((connection, sequence))
        if request is not None and request.peer_pid != peer_pid:
            request = None
        return Reply(connection, peer_pid, sequence, response_type), request


class ExactReplyGate:
    """Withhold only the action's GetPointerControl reply after its KeyPress."""

    def __init__(self, *, owner_pid: int, target_request: Request) -> None:
        if target_request.peer_pid != owner_pid:
            raise ValueError("target request is not owned by the designated process")
        if (target_request.role != "get_pointer_control"
                or not target_request.action_id or target_request.keycode is None):
            raise ValueError("target must be an action-bound GetPointerControl request")
        self.owner_pid = owner_pid
        self.target = target_request

    def should_withhold(self, reply: Reply, request: Request | None,
                        keypress: KeyPressReceipt | None) -> bool:
        if request is None or keypress is None:
            return False
        return (
            reply.response_type == 1
            and reply.peer_pid == self.owner_pid
            and reply.connection == self.target.connection
            and reply.sequence == self.target.sequence
            and request == self.target
            and keypress.action_id == self.target.action_id
            and keypress.keycode == self.target.keycode
        )
