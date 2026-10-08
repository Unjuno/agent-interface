"""Research-only immutable snapshot pager, not a live-path or ACK implementation.

Capture is an explicit host decision. Queries are historical byte-snapshot
queries, not current-file observations. Input must be a bounded, trusted bytes
snapshot; acquisition coherence and producer lifetime are external contracts.
"""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from types import MappingProxyType
from typing import Mapping, Any

from upstream.reader import SCHEMA, EMPTY_SHA, _unique_object, _invalid_constant

@dataclass(frozen=True, slots=True)
class FrozenSnapshot:
    data: bytes
    stream_id: str
    max_bytes: int
    prefixes: Mapping[int, tuple[int, str]]
    sha256: str

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
        # All LF boundaries are indexed, including lines a later parser may reject.
        # This retains the original cursor contract rather than certifying history.
        h = hashlib.sha256()
        table = {0: (1, EMPTY_SHA)}
        offset, sequence = 0, 1
        while True:
            end = data.find(b'\n', offset)
            if end < 0:
                break
            h.update(data[offset:end+1])
            offset, sequence = end+1, sequence+1
            table[offset] = (sequence, h.hexdigest())
        h.update(data[offset:])
        return cls(data, stream_id, max_bytes, MappingProxyType(table), h.hexdigest())

    @classmethod
    def capture(cls, path: Path, *, stream_id: str, max_bytes: int = 1048576):
        # Only cooperative local regular-file captures are tested in this study.
        if type(max_bytes) is not int or not 1 <= max_bytes <= 67108864:
            raise ValueError('INVALID_READ_BOUND')
        with Path(path).open('rb') as source:
            data = source.read(max_bytes+1)
        return cls.prepare(data, stream_id=stream_id, max_bytes=max_bytes)

    def metadata(self) -> dict[str, Any]:
        return {'source_role': 'historical_byte_snapshot', 'snapshot_sha256': self.sha256,
                'snapshot_bytes': len(self.data), 'stream_id': self.stream_id,
                'current_file_verified': False, 'producer_lifetime_verified': False,
                'authority': 'none', 'acknowledged': False, 'input_dispatched': False}

    def read(self, *, cursor: dict | None = None, max_records: int = 32) -> dict:
        if type(max_records) is not int or not 1 <= max_records <= 128:
            raise ValueError('INVALID_READ_BOUND')
        if cursor is None:
            cursor = {'schema': SCHEMA, 'stream_id': self.stream_id, 'offset': 0,
                      'prefix_sha256': EMPTY_SHA, 'next_sequence': 1}
        if (not isinstance(cursor, dict) or set(cursor) !=
                {'schema', 'stream_id', 'offset', 'prefix_sha256', 'next_sequence'}
                or cursor['schema'] != SCHEMA or cursor['stream_id'] != self.stream_id
                or type(cursor['offset']) is not int or not 0 <= cursor['offset'] <= self.max_bytes
                or type(cursor['next_sequence']) is not int or not 1 <= cursor['next_sequence'] <= 2**63-1
                or not isinstance(cursor['prefix_sha256'], str)
                or re.fullmatch('[0-9a-f]{64}', cursor['prefix_sha256']) is None):
            raise ValueError('INVALID_CURSOR')
        offset = cursor['offset']
        entry = self.prefixes.get(offset)
        if entry is None or entry[1] != cursor['prefix_sha256']:
            raise ValueError('CURSOR_PREFIX_CHANGED')
        sequence = cursor['next_sequence']
        if sequence != entry[0]:
            raise ValueError('CURSOR_POSITION_MISMATCH')
        records, tail, problem = [], 'end', None
        while offset < len(self.data) and len(records) < max_records:
            end = self.data.find(b'\n', offset)
            if end < 0:
                tail = 'incomplete'
                break
            try:
                record = json.loads(self.data[offset:end].decode('utf-8'),
                                    object_pairs_hook=_unique_object,
                                    parse_constant=_invalid_constant)
            except (ValueError, UnicodeError):
                tail, problem = 'blocked', 'INVALID_JSON_RECORD'
                break
            if (not isinstance(record, dict) or not isinstance(record.get('event'), str)
                    or not record['event'] or record.get('delivery_id') != f'delivery:{sequence}'):
                tail, problem = 'blocked', 'INVALID_RECORD_OR_DELIVERY_SEQUENCE'
                break
            records.append(record)
            offset, sequence = end+1, sequence+1
        if len(records) == max_records and offset < len(self.data):
            tail = 'limit'
        return {'schema': 'agent-interface/experimental-inbox-read-v1',
                'records': records, 'tail_state': tail, 'problem': problem,
                'next_cursor': {'schema': SCHEMA, 'stream_id': self.stream_id, 'offset': offset,
                                'prefix_sha256': self.prefixes[offset][1], 'next_sequence': sequence},
                'authority': 'none', 'acknowledged': False, 'input_dispatched': False}
