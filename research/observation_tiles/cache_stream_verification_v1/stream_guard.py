"""Research-only byte-pin validation for quiescent, cooperative artifact storage.

A known encoded length bounds total work. The streaming arm additionally bounds
its data buffer. Neither equality nor this receipt establishes image freshness.
"""
from __future__ import annotations
import hashlib
import os
import stat
from pathlib import Path
from vendor.image_artifact import ImageArtifactSink

CHUNK_BYTES = 65536
MAX_ENCODED_BYTES = 4 * 1024 * 1024
MODES = ('FULL_PIN', 'STREAM_PIN')


def inspect_bytes(path: Path, expected_length: int, expected_digest: str | None,
                  mode: str, *, trace: bool = False) -> dict:
    if mode not in MODES:
        raise ValueError('unknown mode')
    if type(expected_length) is not int or not 0 < expected_length <= MAX_ENCODED_BYTES:
        return {'status': 'UNSUPPORTED_SIZE', 'read_bytes': 0, 'hash_bytes': 0,
                'read_calls': 0, 'max_request_bytes': 0, 'digest': None, 'segments': []}
    result = {'status': 'UNAVAILABLE', 'read_bytes': 0, 'hash_bytes': 0,
              'read_calls': 0, 'max_request_bytes': 0, 'digest': None, 'segments': []}

    def record(requested: int, received: int) -> None:
        result['read_bytes'] += received
        result['read_calls'] += 1
        result['max_request_bytes'] = max(result['max_request_bytes'], requested)
        if trace:
            result['segments'].append([requested, received])

    try:
        # Regular cooperative files only; no claim of concurrent-mutation safety.
        with Path(path).open('rb', buffering=0) as source:
            st = os.fstat(source.fileno())
            if not stat.S_ISREG(st.st_mode):
                result['status'] = 'UNSUPPORTED_KIND'
                return result
            if st.st_size != expected_length:
                result['status'] = 'LENGTH_MISMATCH'
                return result
            digest = hashlib.sha256()
            if mode == 'FULL_PIN':
                raw = source.read(expected_length + 1)
                record(expected_length + 1, len(raw))
                if len(raw) != expected_length:
                    result['status'] = 'LENGTH_MISMATCH'
                    return result
                digest.update(raw)
                result['hash_bytes'] = len(raw)
            else:
                buf = bytearray(min(CHUNK_BYTES, expected_length))
                view = memoryview(buf)
                remaining = expected_length
                while remaining:
                    requested = min(len(buf), remaining)
                    received = source.readinto(view[:requested])
                    if received is None:
                        raise OSError('unexpected nonblocking result')
                    record(requested, received)
                    if received == 0:
                        result['status'] = 'LENGTH_MISMATCH'
                        return result
                    digest.update(view[:received])
                    result['hash_bytes'] += received
                    remaining -= received
                extra = source.read(1)
                record(1, len(extra))
                if extra:
                    result['status'] = 'LENGTH_MISMATCH'
                    return result
            result['digest'] = digest.hexdigest()
            result['status'] = ('MATCH' if expected_digest is None or
                                result['digest'] == expected_digest else 'DIGEST_MISMATCH')
    except (OSError, ValueError) as exc:
        result['status'] = 'UNAVAILABLE'
        result['error_type'] = type(exc).__name__
    return result


class GuardedSink:
    """Own one unchanged upstream sink; retain length+digest only after publication."""
    def __init__(self, directory: Path, mode: str):
        if mode not in MODES:
            raise ValueError('unknown mode')
        self.mode = mode
        self.sink = ImageArtifactSink(directory)
        self.length: int | None = None
        self.digest: str | None = None

    def inspect_cache(self, *, trace: bool = False) -> dict:
        if self.length is None or self.digest is None or self.sink.path is None:
            raise ValueError('cache not registered')
        return inspect_bytes(self.sink.path, self.length, self.digest, self.mode, trace=trace)

    def publish(self, frame) -> dict:
        guard = {'status': 'NOT_NEEDED'}
        if self.sink.previous is not None and frame == self.sink.previous:
            guard = self.inspect_cache()
            if guard['status'] != 'MATCH':
                self.sink.previous = None
        receipt = self.sink.publish(frame)
        registration = None
        if not receipt['image_reused']:
            size = self.sink.path.stat().st_size
            registration = inspect_bytes(self.sink.path, size, None, self.mode)
            if registration['status'] != 'MATCH':
                self.sink.previous = None
                self.length = self.digest = None
                raise ValueError('new artifact outside verification support')
            self.length, self.digest = size, registration['digest']
        return {'receipt': receipt, 'guard': guard, 'registration': registration,
                'authority': 'none', 'model_calls': 0, 'input_dispatched': False}
