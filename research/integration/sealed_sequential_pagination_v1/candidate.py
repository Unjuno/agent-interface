"""Research-only sequential snapshot session; no ACK, input, or live-log reuse."""
import copy
import fcntl
import hashlib
import json
import os
import stat

SCHEMA = 'agent-interface/experimental-read-cursor-v1'
FULL = fcntl.F_SEAL_WRITE | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_GROW | fcntl.F_SEAL_SEAL


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('duplicate key')
        result[key] = value
    return result


def constant(_):
    raise ValueError('nonfinite')


class SequentialSnapshot:
    """Single-owner, single-snapshot, current-issued-cursor-only session.

    The caller owns fd. This object retains a private immutable bytes copy,
    never a mutable producer path. Methods are not a thread-safe host commit.
    """
    def __init__(self, fd, stream_id, max_bytes=1048576, meter=None):
        if not isinstance(stream_id, str) or not 1 <= len(stream_id) <= 128:
            raise ValueError('INVALID_STREAM_ID')
        if type(max_bytes) is not int or not 1 <= max_bytes <= 67108864:
            raise ValueError('INVALID_READ_BOUND')
        seals = fcntl.fcntl(fd, fcntl.F_GET_SEALS)
        if seals & FULL != FULL:
            raise ValueError('UNSEALED_SNAPSHOT')
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError('NOT_REGULAR_SNAPSHOT')
        if info.st_size > max_bytes:
            raise ValueError('STREAM_READ_BOUND_EXCEEDED')
        data = bytearray()
        while len(data) < info.st_size:
            block = os.pread(fd, min(1048576, info.st_size-len(data)), len(data))
            if not block:
                raise ValueError('INCOMPLETE_SNAPSHOT')
            data.extend(block)
            if meter is not None:
                meter['read_bytes'] += len(block)
        self._data = bytes(data)
        self._hash = hashlib.sha256()
        self._offset = 0
        self._sequence = 1
        self._stream = stream_id
        self._meter = meter
        self._last = self._cursor()

    def _cursor(self):
        return {'schema': SCHEMA, 'stream_id': self._stream,
                'offset': self._offset, 'prefix_sha256': self._hash.hexdigest(),
                'next_sequence': self._sequence}

    def read(self, cursor=None, max_records=32):
        if type(max_records) is not int or not 1 <= max_records <= 128:
            raise ValueError('INVALID_READ_BOUND')
        if cursor is None:
            valid = self._offset == 0 and self._sequence == 1
        else:
            valid = (isinstance(cursor, dict) and set(cursor) == set(self._last)
                     and type(cursor.get('offset')) is int
                     and type(cursor.get('next_sequence')) is int
                     and cursor == self._last)
        if not valid:
            raise ValueError('STATE_CURSOR_MISMATCH')
        records = []
        tail, problem = 'end', None
        while self._offset < len(self._data) and len(records) < max_records:
            end = self._data.find(b'\n', self._offset)
            if end < 0:
                tail = 'incomplete'
                break
            line = self._data[self._offset:end]
            try:
                record = json.loads(line.decode('utf-8'), object_pairs_hook=pairs,
                                    parse_constant=constant)
            except (ValueError, UnicodeError):
                tail, problem = 'blocked', 'INVALID_JSON_RECORD'
                break
            if (not isinstance(record, dict) or not isinstance(record.get('event'), str)
                    or not record['event']
                    or record.get('delivery_id') != 'delivery:' + str(self._sequence)):
                tail, problem = 'blocked', 'INVALID_RECORD_OR_DELIVERY_SEQUENCE'
                break
            block = self._data[self._offset:end+1]
            self._hash.update(block)
            if self._meter is not None:
                self._meter['hash_bytes'] += len(block)
            self._offset = end+1
            self._sequence += 1
            records.append(record)
        if len(records) == max_records and self._offset < len(self._data):
            tail = 'limit'
        self._last = self._cursor()
        return {'schema': 'agent-interface/experimental-inbox-read-v1',
                'records': records, 'tail_state': tail, 'problem': problem,
                'next_cursor': copy.copy(self._last), 'authority': 'none',
                'acknowledged': False, 'input_dispatched': False}
