"""Passive reader for one append-only DeliveryLedger JSONL stream; no ACK/input."""
import hashlib
import json
from pathlib import Path
import re

SCHEMA = 'agent-interface/experimental-read-cursor-v1'
EMPTY_SHA = hashlib.sha256(b'').hexdigest()


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError('non-finite JSON constant')


def _integer(value, minimum, maximum):
    return type(value) is int and minimum <= value <= maximum


def read_pending(path, *, stream_id, cursor=None, max_records=32, max_bytes=1048576):
    """Read a bounded snapshot. Caller owns the stream epoch and read cursor."""
    if not isinstance(stream_id, str) or not 1 <= len(stream_id) <= 128:
        raise ValueError('INVALID_STREAM_ID')
    if not _integer(max_records, 1, 128) or not _integer(max_bytes, 1, 67108864):
        raise ValueError('INVALID_READ_BOUND')
    if cursor is None:
        cursor = {'schema': SCHEMA, 'stream_id': stream_id, 'offset': 0,
                  'prefix_sha256': EMPTY_SHA, 'next_sequence': 1}
    if (not isinstance(cursor, dict) or set(cursor) !=
            {'schema', 'stream_id', 'offset', 'prefix_sha256', 'next_sequence'}
            or cursor['schema'] != SCHEMA or cursor['stream_id'] != stream_id
            or not _integer(cursor['offset'], 0, max_bytes)
            or not _integer(cursor['next_sequence'], 1, 2**63-1)
            or not isinstance(cursor['prefix_sha256'], str)
            or re.fullmatch('[0-9a-f]{64}', cursor['prefix_sha256']) is None):
        raise ValueError('INVALID_CURSOR')
    with Path(path).open('rb') as source:
        data = source.read(max_bytes+1)
    if len(data) > max_bytes:
        raise ValueError('STREAM_READ_BOUND_EXCEEDED')
    offset = cursor['offset']
    if len(data) < offset or (offset and data[offset-1:offset] != b'\n'):
        raise ValueError('CURSOR_PREFIX_CHANGED')
    # Reuse only this invocation's freshly verified hash state.
    prefix_hash = hashlib.sha256(memoryview(data)[:offset])
    if prefix_hash.hexdigest() != cursor['prefix_sha256']:
        raise ValueError('CURSOR_PREFIX_CHANGED')
    sequence = cursor['next_sequence']
    if sequence != data[:offset].count(b'\n')+1:
        raise ValueError('CURSOR_POSITION_MISMATCH')
    records = []
    tail = 'end'
    problem = None
    while offset < len(data) and len(records) < max_records:
        end = data.find(b'\n', offset)
        if end == -1:
            tail = 'incomplete'
            break
        try:
            record = json.loads(data[offset:end].decode('utf-8'),
                                object_pairs_hook=_unique_object, parse_constant=_invalid_constant)
        except (ValueError, UnicodeError):
            tail, problem = 'blocked', 'INVALID_JSON_RECORD'
            break
        if (not isinstance(record, dict) or not isinstance(record.get('event'), str)
                or not record['event'] or record.get('delivery_id') != f'delivery:{sequence}'):
            tail, problem = 'blocked', 'INVALID_RECORD_OR_DELIVERY_SEQUENCE'
            break
        records.append(record)
        offset = end+1
        sequence += 1
    if len(records) == max_records and offset < len(data):
        tail = 'limit'
    prefix_hash.update(memoryview(data)[cursor['offset']:offset])
    return {'schema': 'agent-interface/experimental-inbox-read-v1',
            'records': records, 'tail_state': tail, 'problem': problem,
            'next_cursor': {'schema': SCHEMA, 'stream_id': stream_id, 'offset': offset,
                            'prefix_sha256': prefix_hash.hexdigest(),
                            'next_sequence': sequence},
            'authority': 'none', 'acknowledged': False, 'input_dispatched': False}
