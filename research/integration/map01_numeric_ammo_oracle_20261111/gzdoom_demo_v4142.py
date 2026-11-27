"""Strict bounded reader for the GZDoom g4.14.2 ZDEM recording subset.

This reader accepts ordinary per-tic user commands and skips the audited
g4.14.2 pitch-limit special command. Other special layouts are rejected rather
than guessed. It is an input-consumption observer, not a wall-clock or
game-effect oracle.
"""

from __future__ import annotations

from dataclasses import dataclass
import struct
import zlib


DEMO_VERSION = 0x221
BT_FORWARD = 1 << 13
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_BODY_BYTES = 64 * 1024 * 1024
MAX_TICS = 1_000_000

_HEADER = b"FORM"
_FORM_TYPE = b"ZDEM"
_BUTTONS = 0x01
_PITCH = 0x02
_YAW = 0x04
_FORWARD = 0x08
_SIDE = 0x10
_UP = 0x20
_ROLL = 0x40
_KNOWN_FLAGS = 0x7F
_DEM_USERCMD = 1
_DEM_EMPTYUSERCMD = 2
_DEM_STOP = 7


class DemoFormatError(ValueError):
    """The demo is malformed, unsupported, or outside configured bounds."""


@dataclass(frozen=True)
class UserCommand:
    tic: int
    buttons: int
    pitch: int
    yaw: int
    forwardmove: int
    sidemove: int
    upmove: int
    roll: int


@dataclass(frozen=True)
class Demo:
    version: int
    min_version: tuple[int, int]
    map_name: str
    rng_seed: int
    console_player: int
    players: tuple[int, ...]
    compressed: bool
    special_command_count: int
    commands: tuple[UserCommand, ...]


def _need(data: bytes, offset: int, count: int, end: int, what: str) -> None:
    if count < 0 or offset < 0 or offset + count > end or offset + count > len(data):
        raise DemoFormatError(f"truncated {what}")


def _cstring(data: bytes, offset: int, end: int, what: str) -> tuple[str, int]:
    nul = data.find(b"\0", offset, end)
    if nul < 0:
        raise DemoFormatError(f"unterminated {what}")
    try:
        value = data[offset:nul].decode("ascii")
    except UnicodeDecodeError as exc:
        raise DemoFormatError(f"non-ASCII {what}") from exc
    return value, nul + 1


def _inflate_bounded(payload: bytes, expected: int, limit: int) -> bytes:
    if expected <= 0 or expected > limit:
        raise DemoFormatError("compressed body size outside limit")
    decoder = zlib.decompressobj()
    try:
        body = decoder.decompress(payload, expected + 1)
        if len(body) > expected or decoder.unconsumed_tail:
            raise DemoFormatError("compressed body exceeds declared size")
        body += decoder.flush(expected + 1 - len(body))
    except zlib.error as exc:
        raise DemoFormatError("invalid compressed body") from exc
    if len(body) != expected or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise DemoFormatError("compressed body length or framing mismatch")
    return body


def _signed_be16(data: bytes, offset: int, end: int, label: str) -> tuple[int, int]:
    _need(data, offset, 2, end, label)
    return struct.unpack_from(">h", data, offset)[0], offset + 2


def _decode_buttons(data: bytes, offset: int, end: int, prior: int) -> tuple[int, int]:
    start = offset
    value = prior
    for index in range(4):
        _need(data, offset, 1, end, "button delta")
        byte = data[offset]
        offset += 1
        if index < 3:
            mask = 0x7F << (index * 7)
            value = (value & ~mask) | ((byte & 0x7F) << (index * 7))
            if not byte & 0x80:
                break
        else:
            mask = 0xFF << 21
            value = (value & ~mask) | (byte << 21)
    changed = value ^ prior
    minimal = 1
    if changed & ~0x7F:
        minimal = 2
    if changed & ~0x3FFF:
        minimal = 3
    if changed & ~0x1FFFFF:
        minimal = 4
    if offset - start != minimal:
        raise DemoFormatError("non-canonical button delta length")
    return value, offset


def _read_commands(body: bytes, max_tics: int) -> tuple[tuple[UserCommand, ...], int]:
    offset = 0
    end = len(body)
    prior = [0, 0, 0, 0, 0, 0, 0]
    commands: list[UserCommand] = []
    special_count = 0
    while offset < end:
        opcode = body[offset]
        offset += 1
        if opcode == _DEM_STOP:
            if offset != end:
                raise DemoFormatError("trailing bytes after DEM_STOP")
            if not commands:
                raise DemoFormatError("demo has no user commands")
            return tuple(commands), special_count
        if opcode not in (_DEM_USERCMD, _DEM_EMPTYUSERCMD):
            if opcode == 63:  # DEM_SETPITCHLIMIT: two one-byte pitch limits.
                _need(body, offset, 2, end, "pitch-limit special command")
                offset += 2
                special_count += 1
                continue
            raise DemoFormatError(f"unsupported demo special opcode {opcode}")
        if opcode == _DEM_EMPTYUSERCMD:
            current = prior.copy()
        elif opcode == _DEM_USERCMD:
            _need(body, offset, 1, end, "user-command flags")
            flags = body[offset]
            offset += 1
            if flags == 0 or flags & ~_KNOWN_FLAGS:
                raise DemoFormatError("invalid user-command flags")
            current = prior.copy()
            if flags & _BUTTONS:
                current[0], offset = _decode_buttons(body, offset, end, prior[0])
            for bit, slot, label in (
                (_PITCH, 1, "pitch"), (_YAW, 2, "yaw"), (_FORWARD, 3, "forwardmove"),
                (_SIDE, 4, "sidemove"), (_UP, 5, "upmove"), (_ROLL, 6, "roll"),
            ):
                if flags & bit:
                    current[slot], offset = _signed_be16(body, offset, end, label)
        if len(commands) >= max_tics:
            raise DemoFormatError("demo tic limit exceeded")
        commands.append(UserCommand(len(commands), *current))
        prior = current
    raise DemoFormatError("missing DEM_STOP")


def parse_demo(
    data: bytes,
    *,
    expected_map: str = "MAP01",
    max_file_bytes: int = MAX_FILE_BYTES,
    max_body_bytes: int = MAX_BODY_BYTES,
    max_tics: int = MAX_TICS,
) -> Demo:
    """Parse a g4.14.2 ZDEM with strict bounds and fail-closed command support."""
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    if not 0 < max_file_bytes <= MAX_FILE_BYTES or not 0 < max_body_bytes <= MAX_BODY_BYTES:
        raise ValueError("limits must be positive and no larger than hard caps")
    if not 0 < max_tics <= MAX_TICS:
        raise ValueError("max_tics must be positive and no larger than hard cap")
    if len(data) > max_file_bytes:
        raise DemoFormatError("demo file exceeds limit")
    if len(data) < 12 or data[:4] != _HEADER or data[8:12] != _FORM_TYPE:
        raise DemoFormatError("not an IFF FORM ZDEM")
    form_size = struct.unpack_from(">I", data, 4)[0]
    form_end = 8 + form_size
    if form_end != len(data) or form_size < 4:
        raise DemoFormatError("FORM length mismatch")

    chunks: dict[bytes, list[bytes]] = {}
    chunk_pads: dict[bytes, list[int | None]] = {}
    offset = 12
    while offset < form_end:
        _need(data, offset, 8, form_end, "IFF chunk header")
        chunk_id = data[offset:offset + 4]
        chunk_size = struct.unpack_from(">I", data, offset + 4)[0]
        payload_start = offset + 8
        payload_end = payload_start + chunk_size
        _need(data, payload_start, chunk_size, form_end, "IFF chunk")
        pad: int | None = None
        if chunk_size & 1:
            _need(data, payload_end, 1, form_end, "IFF odd-byte padding")
            pad = data[payload_end]
            if pad != 0:
                raise DemoFormatError("nonzero IFF padding")
        chunks.setdefault(chunk_id, []).append(data[payload_start:payload_end])
        chunk_pads.setdefault(chunk_id, []).append(pad)
        offset = payload_end + (chunk_size & 1)
        if offset > form_end:
            raise DemoFormatError("missing IFF odd-byte padding")
    for required in (b"ZDHD", b"BODY"):
        if len(chunks.get(required, ())) != 1:
            raise DemoFormatError(f"expected exactly one {required.decode()} chunk")
    if len(chunks.get(b"COMP", ())) > 1:
        raise DemoFormatError("duplicate COMP chunk")

    header = chunks[b"ZDHD"][0]
    if len(header) < 10:
        raise DemoFormatError("short ZDHD header")
    version = struct.unpack_from(">H", header, 0)[0]
    if version != DEMO_VERSION:
        raise DemoFormatError(f"unsupported demo version 0x{version:x}")
    min_version = (header[2], header[3])
    map_name, pos = _cstring(header, 4, len(header), "map name")
    _need(header, pos, 5, len(header), "seed/player header")
    rng_seed = struct.unpack_from(">I", header, pos)[0]
    console_player = header[pos + 4]
    if pos + 5 != len(header):
        raise DemoFormatError("unexpected trailing ZDHD data")
    if map_name != expected_map:
        raise DemoFormatError(f"unexpected map {map_name!r}")

    players: list[int] = []
    for info, pad in zip(chunks.get(b"UINF", []), chunk_pads.get(b"UINF", [])):
        if not info:
            raise DemoFormatError("empty UINF chunk")
        player = info[0]
        userinfo = info[1:]
        if userinfo.endswith(b"\0"):
            userinfo = userinfo[:-1]
        elif pad != 0:
            raise DemoFormatError("unterminated userinfo")
        if b"\0" in userinfo or player in players:
            raise DemoFormatError("malformed or duplicate UINF")
        players.append(player)
    if not players or console_player not in players or len(players) != 1:
        raise DemoFormatError("expected one UINF for the console player")

    body = chunks[b"BODY"][0]
    compressed = False
    comp_chunks = chunks.get(b"COMP", [])
    if comp_chunks:
        comp = comp_chunks[0]
        if len(comp) != 4:
            raise DemoFormatError("COMP chunk must contain one uint32")
        declared = struct.unpack(">I", comp)[0]
        if declared:
            if len(body) > max_file_bytes:
                raise DemoFormatError("compressed payload exceeds file limit")
            body = _inflate_bounded(body, declared, max_body_bytes)
            compressed = True
    if len(body) > max_body_bytes:
        raise DemoFormatError("demo body exceeds limit")
    commands, special_count = _read_commands(body, max_tics)
    return Demo(version, min_version, map_name, rng_seed, console_player, tuple(players), compressed, special_count, commands)
