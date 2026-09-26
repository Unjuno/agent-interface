"""Single-owner memoized prefixes over immutable bytes; historical reads only."""
import hashlib
from collections.abc import Mapping
from snapshot import FrozenSnapshot
from upstream.reader import EMPTY_SHA


class DemandPrefixes(Mapping):
    """Memoize requested LF boundaries, not all lines. Not thread-safe.

    Increasing requests extend one hash state; uncached backward requests
    recompute from byte zero. Cached values contain no parsed event objects.
    """
    def __init__(self, data: bytes):
        self.data = data
        self.cache = {0: (1, EMPTY_SHA)}
        self.frontier = 0
        self.sequence = 1
        self.hasher = hashlib.sha256()

    def __getitem__(self, offset):
        if offset in self.cache:
            return self.cache[offset]
        if (type(offset) is not int or not 0 < offset <= len(self.data)
                or self.data[offset-1:offset] != b'\n'):
            raise KeyError(offset)
        if offset > self.frontier:
            chunk = self.data[self.frontier:offset]
            self.hasher.update(chunk)
            self.sequence += chunk.count(b'\n')
            self.frontier = offset
            value = (self.sequence, self.hasher.hexdigest())
        else:
            prefix = self.data[:offset]
            value = (prefix.count(b'\n')+1, hashlib.sha256(prefix).hexdigest())
        self.cache[offset] = value
        return value

    def __iter__(self):
        # Iteration enumerates memoized boundaries only, not an index API.
        return iter(self.cache)

    def __len__(self):
        return len(self.cache)


class DemandSnapshot(FrozenSnapshot):
    @classmethod
    def prepare(cls, data: bytes, *, stream_id: str, max_bytes: int = 1048576):
        if type(data) is not bytes:
            raise ValueError('IMMUTABLE_BYTES_REQUIRED')
        if not isinstance(stream_id, str) or not 1 <= len(stream_id) <= 128:
            raise ValueError('INVALID_STREAM_ID')
        if type(max_bytes) is not int or not 1 <= max_bytes <= 67108864:
            raise ValueError('INVALID_READ_BOUND')
        if len(data) > max_bytes:
            raise ValueError('STREAM_READ_BOUND_EXCEEDED')
        return cls(data, stream_id, max_bytes, DemandPrefixes(data),
                   hashlib.sha256(data).hexdigest())
