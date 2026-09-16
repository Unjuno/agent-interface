from __future__ import annotations
import argparse, sqlite3, time
from pathlib import Path


def apply(db: Path, kind: str, primary: str, collateral: str) -> None:
    c = sqlite3.connect(db)
    c.execute('PRAGMA synchronous=FULL')
    c.execute('BEGIN IMMEDIATE')
    c.execute('UPDATE state SET primary_value=?, collateral_value=? WHERE id=1', (primary, collateral))
    c.execute('INSERT INTO events(kind,primary_value,collateral_value,ns) VALUES(?,?,?,?)',
              (kind, primary, collateral, time.perf_counter_ns()))
    c.commit()
    c.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('db', type=Path)
    ap.add_argument('kind', choices=['effect', 'compensation'])
    ap.add_argument('primary')
    ap.add_argument('collateral')
    a = ap.parse_args()
    apply(a.db, a.kind, a.primary, a.collateral)


if __name__ == '__main__':
    main()
