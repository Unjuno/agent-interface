from __future__ import annotations

import sqlite3
from pathlib import Path

INITIAL_PRIMARY = "old"
INITIAL_COLLATERAL = "preserve"


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=FULL")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS state(
            id INTEGER PRIMARY KEY CHECK(id=1),
            primary_value TEXT NOT NULL,
            collateral_value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS events(
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            primary_value TEXT NOT NULL,
            collateral_value TEXT NOT NULL
        );
        """
    )
    row = conn.execute("SELECT COUNT(*) FROM state").fetchone()[0]
    if row == 0:
        conn.execute(
            "INSERT INTO state(id,primary_value,collateral_value) VALUES(1,?,?)",
            (INITIAL_PRIMARY, INITIAL_COLLATERAL),
        )
        conn.commit()
    return conn


def commit_event(conn: sqlite3.Connection, kind: str, primary: str, collateral: str) -> None:
    if kind not in {"effect", "compensation"}:
        raise ValueError(f"unsupported event kind: {kind}")
    with conn:
        conn.execute(
            "UPDATE state SET primary_value=?, collateral_value=? WHERE id=1",
            (primary, collateral),
        )
        conn.execute(
            "INSERT INTO events(kind,primary_value,collateral_value) VALUES(?,?,?)",
            (kind, primary, collateral),
        )
