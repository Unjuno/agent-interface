"""Opt-in historical snapshot index; no live source or input authority."""
from collections.abc import Mapping, Iterator
from dataclasses import dataclass
import hashlib
import struct
from eager_snapshot import FrozenSnapshot

_ENTRY = struct.Struct('<Q32s')
_OFFSET = struct.Struct('<Q')
assert _ENTRY.size == 40 and _OFFSET.size == 8

@dataclass(frozen=True, slots=True)
class PackedPrefixes(Mapping):
    """Internal immutable table. Only prepare constructs it; not an import ABI."""
    table: bytes

    def __len__(self) -> int:
        return len(self.table) // _ENTRY.size

    def __iter__(self) -> Iterator[int]:
        for pos in range(0, len(self.table), _ENTRY.size):
            yield _OFFSET.unpack_from(self.table, pos)[0]

    def __getitem__(self, offset: int) -> tuple[int, str]:
        if type(offset) is not int:
            raise KeyError(offset)
        lo, hi = 0, len(self)
        while lo < hi:
            mid = (lo + hi) // 2
            value = _OFFSET.unpack_from(self.table, mid * _ENTRY.size)[0]
            if value < offset:
                lo = mid + 1
            else:
                hi = mid
        if lo == len(self):
            raise KeyError(offset)
        value, digest = _ENTRY.unpack_from(self.table, lo * _ENTRY.size)
        if value != offset:
            raise KeyError(offset)
        return lo + 1, digest.hex()

class PackedSnapshot(FrozenSnapshot):
    __slots__ = ()

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
        table = bytearray(_ENTRY.size * (data.count(b'\n') + 1))
        h = hashlib.sha256()
        _ENTRY.pack_into(table, 0, 0, h.digest())
        offset, ordinal = 0, 1
        while True:
            end = data.find(b'\n', offset)
            if end < 0:
                break
            h.update(data[offset:end + 1])
            offset = end + 1
            _ENTRY.pack_into(table, ordinal * _ENTRY.size, offset, h.digest())
            ordinal += 1
        h.update(data[offset:])
        return cls(data, stream_id, max_bytes, PackedPrefixes(bytes(table)), h.hexdigest())
