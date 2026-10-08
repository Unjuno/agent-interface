"""Cooperative SQLite effect owner with durable manifest-bound execution receipts."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3


class OwnerError(RuntimeError):
    pass


class OwnerConflict(OwnerError):
    pass


class OwnerIntegrityError(OwnerError):
    pass


@dataclass(frozen=True, slots=True)
class ExecutionReceipt:
    command_id: str
    invariant_manifest_id: str
    effect_seq: int
    effect_value: str
    replay: bool


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=FULL")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS state(
            id INTEGER PRIMARY KEY CHECK(id=1),
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS commands(
            command_id TEXT PRIMARY KEY,
            invariant_manifest_id TEXT NOT NULL,
            intended_value TEXT NOT NULL,
            actual_value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS events(
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            command_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS receipts(
            command_id TEXT PRIMARY KEY,
            invariant_manifest_id TEXT NOT NULL,
            effect_seq INTEGER NOT NULL,
            effect_value TEXT NOT NULL
        );
        """
    )
    if conn.execute("SELECT COUNT(*) FROM state").fetchone()[0] == 0:
        conn.execute("INSERT INTO state(id,value) VALUES(1,'old')")
        conn.commit()
    return conn


def _require_text(value: str, label: str) -> str:
    if type(value) is not str or not value:
        raise OwnerError(f"{label} must be nonempty")
    return value


def apply_effect(
    path: Path,
    *,
    command_id: str,
    invariant_manifest_id: str,
    intended_value: str,
    actual_value: str,
) -> ExecutionReceipt:
    """Apply once; exact same-content replay is read-only."""
    for label, value in (
        ("command_id", command_id),
        ("invariant_manifest_id", invariant_manifest_id),
        ("intended_value", intended_value),
        ("actual_value", actual_value),
    ):
        _require_text(value, label)
    conn = connect(path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        existing = conn.execute(
            "SELECT invariant_manifest_id,intended_value,actual_value FROM commands WHERE command_id=?",
            (command_id,),
        ).fetchone()
        if existing is not None:
            if existing != (invariant_manifest_id, intended_value, actual_value):
                conn.rollback()
                raise OwnerConflict("same command_id with different content")
            conn.commit()
            receipt = read_execution_receipt(path, command_id)
            return ExecutionReceipt(
                receipt.command_id,
                receipt.invariant_manifest_id,
                receipt.effect_seq,
                receipt.effect_value,
                True,
            )

        conn.execute(
            "INSERT INTO commands(command_id,invariant_manifest_id,intended_value,actual_value) VALUES(?,?,?,?)",
            (command_id, invariant_manifest_id, intended_value, actual_value),
        )
        conn.execute("UPDATE state SET value=? WHERE id=1", (actual_value,))
        cur = conn.execute(
            "INSERT INTO events(command_id,kind,value) VALUES(?,?,?)",
            (command_id, "effect", actual_value),
        )
        effect_seq = int(cur.lastrowid)
        conn.execute(
            "INSERT INTO receipts(command_id,invariant_manifest_id,effect_seq,effect_value) VALUES(?,?,?,?)",
            (command_id, invariant_manifest_id, effect_seq, actual_value),
        )
        conn.commit()
        return ExecutionReceipt(command_id, invariant_manifest_id, effect_seq, actual_value, False)
    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise
    finally:
        conn.close()


def apply_compensation(path: Path, *, command_id: str, value: str) -> None:
    _require_text(command_id, "command_id")
    _require_text(value, "value")
    conn = connect(path)
    try:
        with conn:
            if conn.execute("SELECT 1 FROM commands WHERE command_id=?", (command_id,)).fetchone() is None:
                raise OwnerIntegrityError("compensation requires an existing command")
            if conn.execute(
                "SELECT 1 FROM events WHERE command_id=? AND kind='compensation'", (command_id,)
            ).fetchone() is not None:
                raise OwnerConflict("only one compensation is supported")
            conn.execute("UPDATE state SET value=? WHERE id=1", (value,))
            conn.execute(
                "INSERT INTO events(command_id,kind,value) VALUES(?,?,?)",
                (command_id, "compensation", value),
            )
    finally:
        conn.close()


def read_execution_receipt(path: Path, command_id: str) -> ExecutionReceipt:
    _require_text(command_id, "command_id")
    conn = connect(path)
    try:
        row = conn.execute(
            """
            SELECT r.invariant_manifest_id,r.effect_seq,r.effect_value,
                   c.invariant_manifest_id,e.command_id,e.kind,e.value
              FROM receipts r
              JOIN commands c ON c.command_id=r.command_id
              JOIN events e ON e.seq=r.effect_seq
             WHERE r.command_id=?
            """,
            (command_id,),
        ).fetchone()
        if row is None:
            raise OwnerIntegrityError("missing execution receipt")
        receipt_manifest, effect_seq, effect_value, command_manifest, event_command, kind, event_value = row
        if receipt_manifest != command_manifest:
            raise OwnerIntegrityError("receipt manifest disagrees with command record")
        if event_command != command_id or kind != "effect" or event_value != effect_value:
            raise OwnerIntegrityError("receipt disagrees with authoritative effect event")
        return ExecutionReceipt(command_id, receipt_manifest, int(effect_seq), effect_value, False)
    finally:
        conn.close()


def read_state_and_history(path: Path, command_id: str) -> tuple[str, list[tuple[int, str, str]]]:
    conn = connect(path)
    try:
        state = conn.execute("SELECT value FROM state WHERE id=1").fetchone()[0]
        rows = conn.execute(
            "SELECT seq,kind,value FROM events WHERE command_id=? ORDER BY seq", (command_id,)
        ).fetchall()
        if not rows:
            raise OwnerIntegrityError("missing effect history")
        return state, [(int(seq), kind, value) for seq, kind, value in rows]
    finally:
        conn.close()


def effect_count(path: Path) -> int:
    conn = connect(path)
    try:
        return int(conn.execute("SELECT COUNT(*) FROM events WHERE kind='effect'").fetchone()[0])
    finally:
        conn.close()
