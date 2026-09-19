from __future__ import annotations
import argparse, sqlite3, time
from pathlib import Path


def connect(db: Path):
    c=sqlite3.connect(db)
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('PRAGMA synchronous=FULL')
    c.execute('CREATE TABLE IF NOT EXISTS state(id INTEGER PRIMARY KEY CHECK(id=1), value TEXT NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, value TEXT NOT NULL, ns INTEGER NOT NULL)')
    c.execute("INSERT OR IGNORE INTO state(id,value) VALUES(1,'old')")
    c.commit(); return c

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('db',type=Path); ap.add_argument('kind'); ap.add_argument('value'); a=ap.parse_args()
    c=connect(a.db)
    ns=time.perf_counter_ns()
    c.execute('BEGIN IMMEDIATE')
    c.execute('UPDATE state SET value=? WHERE id=1',(a.value,))
    c.execute('INSERT INTO events(kind,value,ns) VALUES(?,?,?)',(a.kind,a.value,ns))
    c.commit()
    print(f'{a.kind}:{a.value}')
if __name__=='__main__': main()
