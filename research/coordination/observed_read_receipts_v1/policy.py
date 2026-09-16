from __future__ import annotations
from dataclasses import dataclass
import sqlite3

@dataclass(frozen=True)
class Receipt:
    key: str
    revision: int

class ReadTracker:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.receipts: list[Receipt] = []
    def read(self, key: str) -> str:
        row = self.conn.execute('select value, revision from kv where key=?', (key,)).fetchone()
        if row is None:
            raise KeyError(key)
        value, revision = row
        self.receipts.append(Receipt(key, int(revision)))
        return str(value)

def decide(conn: sqlite3.Connection, policy: str) -> tuple[str, list[Receipt]]:
    if policy == 'observed':
        tracker = ReadTracker(conn)
        a = tracker.read('A')
        b = tracker.read('B')
        return a + '|' + b, tracker.receipts
    if policy == 'broad':
        a, ar = conn.execute("select value, revision from kv where key='A'").fetchone()
        b, br = conn.execute("select value, revision from kv where key='B'").fetchone()
        _, ur = conn.execute("select value, revision from kv where key='U'").fetchone()
        return str(a) + '|' + str(b), [Receipt('A', int(ar)), Receipt('B', int(br)), Receipt('U', int(ur))]
    raise ValueError('unknown policy')
