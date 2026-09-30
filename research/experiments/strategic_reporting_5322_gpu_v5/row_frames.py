"""Small, terminal-safe frames for durable per-call capture; no inference here."""
import base64
import hashlib

CHUNK_BYTES = 24
MAX_PAYLOAD_BYTES = 128 * 1024


def encode_call(call_index: int, payload: bytes) -> list[str]:
    if not 1 <= call_index <= 6:
        raise ValueError("call index outside frozen six-call allocation")
    if not isinstance(payload, bytes) or not payload or len(payload) > MAX_PAYLOAD_BYTES:
        raise ValueError("invalid payload length")
    chunks = [payload[i:i + CHUNK_BYTES] for i in range(0, len(payload), CHUNK_BYTES)]
    lines = [f"H1:{call_index}:{len(chunks)}:{len(payload)}",
             f"S1:{call_index}:{hashlib.sha256(payload).hexdigest()}"]
    lines.extend(f"D1:{call_index}:{seq:03d}/{len(chunks):03d}:{base64.b64encode(chunk).decode('ascii')}"
                 for seq, chunk in enumerate(chunks))
    if any(len(line) > 78 or not line.isascii() for line in lines):
        raise AssertionError("frame exceeds terminal-safe line bound")
    return lines


def decode_call(lines: list[str], expected_call: int) -> bytes:
    if len(lines) < 3:
        raise ValueError("truncated frame set")
    try:
        h = lines[0].split(":")
        s = lines[1].split(":")
        if len(h) != 4 or h[:2] != ["H1", str(expected_call)]:
            raise ValueError("bad header")
        count, size = int(h[2]), int(h[3])
        if not 1 <= count <= (MAX_PAYLOAD_BYTES + CHUNK_BYTES - 1) // CHUNK_BYTES:
            raise ValueError("bad frame count")
        if not 1 <= size <= MAX_PAYLOAD_BYTES or len(s) != 3 or s[:2] != ["S1", str(expected_call)]:
            raise ValueError("bad size or checksum frame")
        digest = s[2]
        if len(digest) != 64:
            raise ValueError("bad checksum")
        if len(lines) != count + 2:
            raise ValueError("missing or extra frames")
        parts = []
        for expected_seq, line in enumerate(lines[2:]):
            fields = line.split(":")
            if len(fields) != 4 or fields[0] != "D1" or fields[1] != str(expected_call):
                raise ValueError("bad data frame")
            seq, total = fields[2].split("/")
            if int(seq) != expected_seq or int(total) != count:
                raise ValueError("duplicate, reordered, or mismatched frame")
            parts.append(base64.b64decode(fields[3], validate=True))
        payload = b"".join(parts)
        if len(payload) != size or hashlib.sha256(payload).hexdigest() != digest:
            raise ValueError("length or checksum mismatch")
        return payload
    except (IndexError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid call frame: {exc}") from exc
