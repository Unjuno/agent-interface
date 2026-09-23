from __future__ import annotations
import argparse, json, sqlite3, time
from pathlib import Path


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--db',type=Path,required=True)
    ap.add_argument('--effect-id',required=True)
    ap.add_argument('--requested',required=True)
    ap.add_argument('--behavior',choices=['correct','wrong'],required=True)
    a=ap.parse_args()
    con=sqlite3.connect(a.db)
    try:
        con.execute('PRAGMA journal_mode=WAL')
        con.execute('PRAGMA synchronous=FULL')
        con.execute('CREATE TABLE IF NOT EXISTS effects(effect_id TEXT PRIMARY KEY, value TEXT NOT NULL, applied_ns INTEGER NOT NULL)')
        applied = a.requested if a.behavior=='correct' else 'wrong'
        ns=time.perf_counter_ns()
        con.execute('BEGIN IMMEDIATE')
        con.execute('INSERT INTO effects(effect_id,value,applied_ns) VALUES(?,?,?)',(a.effect_id,applied,ns))
        con.commit()
        print(json.dumps({'accepted':True,'effect_id':a.effect_id,'stored':applied,'applied_ns':ns},sort_keys=True))
    finally:
        con.close()

if __name__=='__main__': main()
