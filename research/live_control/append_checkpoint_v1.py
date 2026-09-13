"""Bounded full-state append checkpoints, caller must hold its cooperating flock.

Torn/corrupt tails are uncertainty, never silently rolled back. No compaction.
Hashes detect damage, not authenticated identity or whole-file rollback.
"""
import hashlib, json, os
from pathlib import Path
MAX_BYTES = 16 * 1024 * 1024
MAX_RECORD = 1024 * 1024
MAX_RECORDS = 256


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def inspect(path):
    with Path(path).open('rb') as stream: raw = stream.read(MAX_BYTES + 1)
    if not raw or len(raw) > MAX_BYTES or not raw.endswith(b'\n'):
        raise ValueError('empty, oversized or torn journal; uncertainty retained')
    lines = raw.splitlines(); previous = None; state = None
    if len(lines) > MAX_RECORDS: raise ValueError('journal record limit')
    for index, line in enumerate(lines, 1):
        if len(line) > MAX_RECORD: raise ValueError('journal frame limit')
        record = json.loads(line)
        if set(record) != {'version', 'index', 'previous', 'state', 'sha256'}:
            raise ValueError('invalid journal frame')
        checksum = record.pop('sha256')
        if (record['version'] != 'append-checkpoint-v1' or type(record['index']) is not int
                or record['index'] != index or record['previous'] != previous
                or type(record['state']) is not dict
                or hashlib.sha256(encoded(record)).hexdigest() != checksum):
            raise ValueError('journal chain mismatch')
        previous = checksum; state = record['state']
    return state, len(lines), previous, len(raw)


def load(path): return inspect(path)[0]


def store(path, state):
    path = Path(path); exists = path.exists()
    _, count, previous, size = inspect(path) if exists else (None, 0, None, 0)
    record = {'version': 'append-checkpoint-v1', 'index': count+1, 'previous': previous, 'state': state}
    record['sha256'] = hashlib.sha256(encoded(record)).hexdigest()
    frame = encoded(record) + b'\n'
    if len(frame)-1 > MAX_RECORD or count >= MAX_RECORDS or size+len(frame) > MAX_BYTES:
        raise ValueError('journal capacity exhausted; no automatic reset')
    # One file sync per commit; directory sync only when first creating the file.
    with path.open('ab' if exists else 'xb') as stream:
        stream.write(frame); stream.flush(); os.fsync(stream.fileno())
    if not exists:
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(fd)
        finally: os.close(fd)
