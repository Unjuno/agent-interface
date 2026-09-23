"""Bounded, observation-only datagrams. FRAME_FRESH is never action authority."""
import hashlib
import json
import struct

KEYS = {'case_id', 'seq', 'capture_start_ns', 'capture_end_ns', 'python_return_ns',
        'serialize_start_ns', 'pixel_sha256'}
MAX_AGE_NS = 20_000_000

def encode(meta: dict, pixels: bytes) -> bytes:
    h = json.dumps(meta, separators=(',', ':'), sort_keys=True).encode()
    return struct.pack('!I', len(h)) + h + pixels

def pixel_digest(pixels: bytes, chunked: bool = False) -> str:
    if not chunked:
        return hashlib.sha256(pixels).hexdigest()
    h = hashlib.sha256()
    for start in range(0, len(pixels), 1024):
        h.update(pixels[start:start+1024])
    return h.hexdigest()

def inspect(packet: bytes, received_ns: int, case_id: str, last_seq: int, chunked_hash: bool = False):
    try:
        if type(received_ns) is not int or received_ns < 0 or len(packet) > 8192 or len(packet) < 4:
            return 'YIELD_INVALID', None
        n, = struct.unpack('!I', packet[:4])
        if n > 1024 or len(packet) != 4 + n + 4096:
            return 'YIELD_INVALID', None
        m = json.loads(packet[4:4+n])
        pixels = packet[4+n:]
        if type(m) is not dict or set(m) != KEYS or m['case_id'] != case_id:
            return 'YIELD_INVALID', None
        ints = ['seq', 'capture_start_ns', 'capture_end_ns', 'python_return_ns', 'serialize_start_ns']
        if any(type(m[k]) is not int or m[k] < 0 for k in ints):
            return 'YIELD_INVALID', None
        if m['seq'] <= last_seq or not (m['capture_start_ns'] <= m['capture_end_ns'] <= m['python_return_ns'] <= m['serialize_start_ns'] <= received_ns):
            return 'YIELD_INVALID', None
        if m['pixel_sha256'] != pixel_digest(pixels, chunked_hash):
            return 'YIELD_INVALID', None
        status = 'FRAME_FRESH' if received_ns - m['capture_start_ns'] <= MAX_AGE_NS else 'YIELD_STALE'
        return status, m
    except (ValueError, KeyError, TypeError, struct.error, UnicodeError):
        return 'YIELD_INVALID', None
