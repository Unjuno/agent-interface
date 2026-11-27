"""Experimental single-writer JSONL receipt journal with fail-closed scans.

This module is a research prototype, not wired into the guarded X11 runtime.
It provides process-level flush and tamper/torn-tail detection, not fsync-backed
durability or multi-process locking.
"""
import copy
import hashlib
import json
import threading
from pathlib import Path


SCHEMA = "agent-interface/receipt-journal-prototype-v1"
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


class ReceiptJournal:
    """Append ordered, hash-linked receipts and resolve references by name."""

    def __init__(self, path):
        self.path = Path(path)
        self._lock = threading.RLock()
        self._index = {}
        self._last_sha256 = None
        self._size = 0
        self._uncertain = False
        self._load()

    def _load(self):
        if not self.path.exists():
            return
        try:
            raw = self.path.read_bytes()
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
            self._index = rows
            self._last_sha256 = previous
            self._size = len(raw)
        except OSError as error:
            raise JournalError("journal read failed") from error

    def append(self, reference, kind, payload):
        """Flush one receipt before returning its caller-visible reference."""
        with self._lock:
            if self._uncertain:
                raise JournalError("journal state is uncertain; reopen and audit")
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
                self.path.parent.mkdir(parents=True, exist_ok=True)
                actual_size = self.path.stat().st_size if self.path.exists() else 0
                if actual_size != self._size:
                    self._uncertain = True
                    raise JournalError("journal changed outside this writer")
                with self.path.open("ab") as stream:
                    written = stream.write(encoded)
                    if written != len(encoded):
                        self._uncertain = True
                        raise JournalError("short journal append")
                    stream.flush()
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
        """Return a detached receipt only while the whole journal is trusted."""
        with self._lock:
            if self._uncertain:
                raise JournalError("journal state is uncertain; reopen and audit")
            row = self._index.get(reference)
            if row is None:
                raise KeyError(reference)
            return copy.deepcopy(row["payload"])

    def references(self):
        with self._lock:
            if self._uncertain:
                raise JournalError("journal state is uncertain; reopen and audit")
            return tuple(self._index)
