"""SQLite fixtures and read-only observation helpers for Issue #8300."""

import json
import sqlite3
import subprocess
import sys
from pathlib import Path


def connect(path, readonly=False):
    if readonly:
        return sqlite3.connect(f"file:{Path(path).resolve()}?mode=ro", uri=True)
    return sqlite3.connect(path)


def initialize(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as db:
        db.executescript("""
            CREATE TABLE artifact(object_id TEXT PRIMARY KEY, revision INTEGER NOT NULL, x INTEGER NOT NULL, y INTEGER NOT NULL);
            CREATE TABLE journal(seq INTEGER PRIMARY KEY, rev_before INTEGER NOT NULL, rev_after INTEGER NOT NULL,
                field TEXT NOT NULL, old_value INTEGER NOT NULL, new_value INTEGER NOT NULL,
                actor TEXT NOT NULL, txid TEXT NOT NULL);
            INSERT INTO artifact VALUES ('doc', 1, 1, 0);
        """)


def observe(path):
    with connect(path, readonly=True) as db:
        state = db.execute("SELECT object_id, revision, x, y FROM artifact").fetchone()
        events = db.execute("SELECT seq, rev_before, rev_after, field, old_value, new_value, actor, txid FROM journal ORDER BY seq").fetchall()
    return {"state": dict(zip(("object_id", "revision", "x", "y"), state)),
            "journal": [dict(zip(("seq", "rev_before", "rev_after", "field", "old_value", "new_value", "actor", "txid"), e)) for e in events]}


def write_external(path, mode):
    with connect(path) as db:
        if mode == "none":
            return
        field, old, new, next_rev = ("x", 1, 9, 2) if mode == "same_x" else ("y", 0, 7, 2)
        db.execute(f"UPDATE artifact SET {field}=?, revision=? WHERE object_id='doc' AND revision=1", (new, next_rev))
        if mode != "missing_row":
            seq = 1
            db.execute("INSERT INTO journal VALUES (?,1,2,?,?,?,'external','external-1')", (seq, field, old, new))
        if mode == "sequence_gap":
            db.execute("UPDATE artifact SET y=8, revision=3 WHERE object_id='doc' AND revision=2")
            db.execute("INSERT INTO journal VALUES (3,2,3,'y',7,8,'external','external-2')")
        if mode == "tampered_value":
            db.execute("UPDATE journal SET new_value=6 WHERE seq=1")


def writer_process(path, mode):
    subprocess.run([sys.executable, str(Path(__file__).with_name("writer.py")), str(path), mode], check=True)


def observer_process(path):
    result = subprocess.run([sys.executable, str(Path(__file__).with_name("observer.py")), str(path)],
                            check=True, capture_output=True, text=True)
    return json.loads(result.stdout)
