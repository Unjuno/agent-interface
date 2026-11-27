"""Persistent-handle JSONL receipt journal experiment for Linux/X11.

This research prototype is not imported by the production runtime. It uses an
advisory single-writer flock and flushes each receipt, without fsync.
"""
import copy
import fcntl
import hashlib
import json
import threading
from pathlib import Path


SCHEMA = "agent-interface/receipt-journal-prototype-v2"
_FIELDS = {
    "schema", "sequence", "reference", "kind", "payload_sha256",
    "previous_sha256", "payload", "record_sha256",
}


class JournalError(RuntimeError):
    """The journal cannot safely provide or accept a receipt."""


def _canonical(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise JournalError("receipt is not canonical JSON") from error


def _digest(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _scan(raw):
    rows = {}
    previous = None
    expected_sequence = 1
    for line_number, line in enumerate(raw.splitlines(keepends=True), 1):
        if not line.endswith(b"\n"):
            raise JournalError(f"torn journal line {line_number}")
        try:
            row = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise JournalError(f"invalid journal line {line_number}") from error
        if type(row) is not dict or set(row) != _FIELDS:
            raise JournalError(f"invalid fields on journal line {line_number}")
        if row["schema"] != SCHEMA:
            raise JournalError(f"unsupported schema on journal line {line_number}")
        if type(row["sequence"]) is not int or row["sequence"] != expected_sequence:
            raise JournalError(f"sequence gap on journal line {line_number}")
        ref, kind = row["reference"], row["kind"]
        if (type(ref) is not str or not ref or len(ref) > 64 or
                type(kind) is not str or not kind or len(kind) > 64):
            raise JournalError(f"invalid identity on journal line {line_number}")
        if ref in rows:
            raise JournalError(f"duplicate reference on journal line {line_number}")
        if row["previous_sha256"] != previous:
            raise JournalError(f"broken hash chain on journal line {line_number}")
        if row["payload_sha256"] != _digest(row["payload"]):
            raise JournalError(f"payload hash mismatch on journal line {line_number}")
        body = {key: row[key] for key in row if key != "record_sha256"}
        record_hash = _digest(body)
        if row["record_sha256"] != record_hash:
            raise JournalError(f"record hash mismatch on journal line {line_number}")
        rows[ref] = row
        previous = record_hash
        expected_sequence += 1
    return rows, previous, len(raw)


class ReceiptJournal:
    """Hold one advisory-locked append handle and resolve refs from a scan."""

    def __init__(self, path, *, stream_opener=None):
        self.path = Path(path)
        self._lock = threading.RLock()
        self._index = {}
        self._last_sha256 = None
        self._size = 0
        self._uncertain = False
        self._stream = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            opener = stream_opener or self.path.open
            self._stream = opener("a+b")
            try:
                fcntl.flock(self._stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise JournalError("another journal writer holds the lock") from error
            self._stream.seek(0)
            raw = self._stream.read()
            self._index, self._last_sha256, self._size = _scan(raw)
            self._stream.seek(0, 2)
        except JournalError:
            self._release_stream()
            raise
        except OSError as error:
            self._release_stream()
            raise JournalError("journal open or scan failed") from error

    def _release_stream(self):
        stream, self._stream = self._stream, None
        if stream is None:
            return
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        try:
            stream.close()
        except OSError:
            pass

    def append(self, reference, kind, payload):
        """Flush one ordered receipt before returning its reference."""
        with self._lock:
            if self._uncertain or self._stream is None:
                raise JournalError("journal state is uncertain or closed")
            if (type(reference) is not str or not reference or len(reference) > 64 or
                    type(kind) is not str or not kind or len(kind) > 64):
                raise JournalError("invalid receipt identity")
            if reference in self._index:
                raise JournalError("duplicate receipt reference")
            detached = json.loads(_canonical(payload).decode("utf-8"))
            body = {
                "schema": SCHEMA,
                "sequence": len(self._index) + 1,
                "reference": reference,
                "kind": kind,
                "payload_sha256": _digest(detached),
                "previous_sha256": self._last_sha256,
                "payload": detached,
            }
            record_hash = _digest(body)
            row = dict(body, record_sha256=record_hash)
            encoded = _canonical(row) + b"\n"
            try:
                end = self._stream.seek(0, 2)
                if end != self._size:
                    self._uncertain = True
                    raise JournalError("journal changed outside locked writer")
                written = self._stream.write(encoded)
                if written != len(encoded):
                    self._uncertain = True
                    raise JournalError("short journal append")
                self._stream.flush()
            except JournalError:
                raise
            except OSError as error:
                self._uncertain = True
                raise JournalError("journal append or flush failed") from error
            self._index[reference] = row
            self._last_sha256 = record_hash
            self._size += len(encoded)
            return reference

    def lookup(self, reference):
        with self._lock:
            if self._uncertain or self._stream is None:
                raise JournalError("journal state is uncertain or closed")
            row = self._index.get(reference)
            if row is None:
                raise KeyError(reference)
            return copy.deepcopy(row["payload"])

    def references(self):
        with self._lock:
            if self._uncertain or self._stream is None:
                raise JournalError("journal state is uncertain or closed")
            return tuple(self._index)

    def close(self):
        with self._lock:
            if self._stream is None:
                return
            stream = self._stream
            failure = None
            if not self._uncertain:
                try:
                    stream.flush()
                except OSError as error:
                    self._uncertain = True
                    failure = error
            self._release_stream()
            if failure is not None:
                raise JournalError("journal close flush failed") from failure

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        try:
            self.close()
        except JournalError:
            if exc is None:
                raise
        return False
