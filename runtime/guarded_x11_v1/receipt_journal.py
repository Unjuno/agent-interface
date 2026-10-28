"""Append-only, hash-linked receipt storage for the guarded X11 bridge."""
import copy
import hashlib
import json
import os
import threading
from pathlib import Path


SCHEMA = 'agent-interface/x11-receipt-journal-v1'
_FIELDS = {'schema', 'sequence', 'reference', 'kind', 'payload',
           'payload_sha256', 'previous_sha256', 'record_sha256'}


class ReceiptJournalError(RuntimeError):
    """The receipt journal is invalid, uncertain, or unavailable."""


def _canonical(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(',', ':'),
                          ensure_ascii=False, allow_nan=False).encode('utf-8')
    except (TypeError, ValueError) as error:
        raise ReceiptJournalError('receipt is not canonical JSON') from error


def _hash(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _decode_record(line, expected_sequence, previous):
    try:
        row = json.loads(line.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReceiptJournalError('invalid journal JSON record') from error
    if type(row) is not dict or set(row) != _FIELDS or row.get('schema') != SCHEMA:
        raise ReceiptJournalError('invalid journal record schema')
    if type(row.get('sequence')) is not int or row['sequence'] != expected_sequence:
        raise ReceiptJournalError('journal sequence mismatch')
    reference, kind = row.get('reference'), row.get('kind')
    if (type(reference) is not str or not 1 <= len(reference) <= 128 or
            type(kind) is not str or not 1 <= len(kind) <= 64):
        raise ReceiptJournalError('invalid journal reference or kind')
    if row.get('previous_sha256') != previous:
        raise ReceiptJournalError('journal hash chain mismatch')
    if row.get('payload_sha256') != _hash(row['payload']):
        raise ReceiptJournalError('journal payload hash mismatch')
    body = {key: value for key, value in row.items() if key != 'record_sha256'}
    digest = _hash(body)
    if row.get('record_sha256') != digest:
        raise ReceiptJournalError('journal record hash mismatch')
    return row, digest


def _scan(raw):
    index = {}
    previous = None
    offset = 0
    lines = raw.splitlines(keepends=True)
    for sequence, line in enumerate(lines, 1):
        if not line.endswith(b'\n'):
            raise ReceiptJournalError('torn journal record')
        row, digest = _decode_record(line[:-1], sequence, previous)
        reference = row['reference']
        if reference in index:
            raise ReceiptJournalError('duplicate journal reference')
        index[reference] = (offset, len(line), sequence, digest)
        previous = digest
        offset += len(line)
    return index, previous, offset


def _lock_file(stream):
    descriptor = stream.fileno()
    if os.name == 'nt':
        import msvcrt
        os.lseek(descriptor, 0, os.SEEK_SET)
        try:
            msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
        except OSError as error:
            raise ReceiptJournalError('another journal writer holds the lock') from error
        return
    import fcntl
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as error:
        raise ReceiptJournalError('another journal writer holds the lock') from error


def _unlock_file(stream):
    descriptor = stream.fileno()
    try:
        if os.name == 'nt':
            import msvcrt
            os.lseek(descriptor, 0, os.SEEK_SET)
            msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(descriptor, fcntl.LOCK_UN)
    except OSError:
        pass


class ReceiptJournal:
    """Serialize a single writer and resolve references from verified records."""

    def __init__(self, path):
        self.path = Path(path)
        self._mutex = threading.RLock()
        self._stream = None
        self._index = {}
        self._hashes_by_sequence = []
        self._last_hash = None
        self._size = 0
        self._uncertain = False
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._stream = self.path.open('a+b')
            _lock_file(self._stream)
            self._stream.seek(0)
            raw = self._stream.read()
            self._index, self._last_hash, self._size = _scan(raw)
            self._hashes_by_sequence = [None] + [
                row[3] for row in sorted(self._index.values(), key=lambda row: row[2])]
            self._stream.seek(0, os.SEEK_END)
        except ReceiptJournalError:
            self._release()
            raise
        except OSError as error:
            self._release()
            raise ReceiptJournalError('journal open or scan failed') from error

    def _require_open(self):
        if self._uncertain:
            raise ReceiptJournalError('journal state is uncertain')
        if self._stream is None:
            raise ReceiptJournalError('journal is closed')

    def _release(self):
        stream, self._stream = self._stream, None
        if stream is not None:
            _unlock_file(stream)
            try:
                stream.close()
            except OSError:
                pass

    def append(self, reference, kind, payload):
        with self._mutex:
            self._require_open()
            if (type(reference) is not str or not 1 <= len(reference) <= 128 or
                    type(kind) is not str or not 1 <= len(kind) <= 64):
                raise ReceiptJournalError('invalid journal reference or kind')
            if reference in self._index:
                raise ReceiptJournalError('duplicate journal reference')
            detached = json.loads(_canonical(payload).decode('utf-8'))
            body = {
                'schema': SCHEMA,
                'sequence': len(self._index) + 1,
                'reference': reference,
                'kind': kind,
                'payload': detached,
                'payload_sha256': _hash(detached),
                'previous_sha256': self._last_hash,
            }
            digest = _hash(body)
            encoded = _canonical(dict(body, record_sha256=digest)) + b'\n'
            try:
                current_size = os.fstat(self._stream.fileno()).st_size
                if current_size != self._size:
                    self._uncertain = True
                    raise ReceiptJournalError('journal changed outside locked writer')
                self._stream.seek(0, os.SEEK_END)
                written = self._stream.write(encoded)
                if written != len(encoded):
                    self._uncertain = True
                    raise ReceiptJournalError('short journal append')
                self._stream.flush()
                os.fsync(self._stream.fileno())
            except ReceiptJournalError:
                raise
            except OSError as error:
                self._uncertain = True
                raise ReceiptJournalError('journal append or fsync failed') from error
            offset = self._size
            self._size += len(encoded)
            self._last_hash = digest
            self._index[reference] = (offset, len(encoded), body['sequence'], digest)
            self._hashes_by_sequence.append(digest)
            return reference

    def lookup(self, reference):
        with self._mutex:
            self._require_open()
            record = self._index.get(reference)
            if record is None:
                raise KeyError(reference)
            offset, length, sequence, digest = record
            try:
                self._stream.seek(offset)
                line = self._stream.read(length)
            except OSError as error:
                self._uncertain = True
                raise ReceiptJournalError('journal lookup failed') from error
            if len(line) != length or not line.endswith(b'\n'):
                self._uncertain = True
                raise ReceiptJournalError('journal record changed during lookup')
            row, actual_digest = _decode_record(line[:-1], sequence,
                self._previous_hash(sequence))
            if row['reference'] != reference or actual_digest != digest:
                self._uncertain = True
                raise ReceiptJournalError('journal record changed during lookup')
            return copy.deepcopy(row['payload'])

    def _previous_hash(self, sequence):
        if sequence == 1:
            return None
        if sequence - 1 >= len(self._hashes_by_sequence):
            self._uncertain = True
            raise ReceiptJournalError('journal index is incomplete')
        return self._hashes_by_sequence[sequence - 1]

    @classmethod
    def read(cls, path, reference):
        with cls(path) as journal:
            return journal.lookup(reference)

    def references(self):
        with self._mutex:
            self._require_open()
            return tuple(self._index)

    def close(self):
        with self._mutex:
            if self._stream is None:
                return
            self._release()

    def __enter__(self):
        self._require_open()
        return self

    def __exit__(self, error_type, error, traceback):
        self.close()
        return False
