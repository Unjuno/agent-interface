"""Private SQLite fixture actors; no production input, network, or replay authority."""
from __future__ import annotations
import argparse
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import time
from vendor531 import Receipt, WatermarkLedger

FIELDS = ('intent_id','intent_seq','from_generation','to_generation',
          'confirmation_content_id','confirmation_revision')

def receipt(seq: int) -> Receipt:
    return Receipt(f'I{seq:08d}',seq,seq,seq+1,
                   hashlib.sha256(f'payload-{seq}'.encode()).hexdigest(),seq)

def view(db: sqlite3.Connection) -> dict:
    g,w = db.execute('SELECT generation, retired FROM meta WHERE id=1').fetchone()
    rows = db.execute('SELECT '+','.join(FIELDS)+' FROM history ORDER BY intent_seq').fetchall()
    return {'generation':g,'retired':w,'history':[dict(zip(FIELDS,r)) for r in rows]}

def load(v: dict) -> WatermarkLedger:
    obj = WatermarkLedger(2)
    obj.generation=v['generation'];obj.retired_through_seq=v['retired']
    obj.history=[Receipt(**r) for r in v['history']]
    return obj

def save(db: sqlite3.Connection, obj: WatermarkLedger) -> None:
    db.execute('UPDATE meta SET generation=?,retired=? WHERE id=1',
               (obj.generation,obj.retired_through_seq))
    db.execute('DELETE FROM history')
    db.executemany('INSERT INTO history VALUES(?,?,?,?,?,?)',
                   [tuple(dataclasses.asdict(r).values()) for r in obj.history])

def main() -> None:
    ap=argparse.ArgumentParser();ap.add_argument('role',choices=['writer','reader'])
    ap.add_argument('db');ap.add_argument('case');args=ap.parse_args()
    path=Path(args.db)
    db=sqlite3.connect(str(path) if args.role=='writer' else path.as_uri()+'?mode=ro',
                       uri=args.role=='reader',isolation_level=None,timeout=0)
    traces=[];db.set_trace_callback(traces.append)
    if args.role=='reader':db.execute('PRAGMA query_only=ON')
    db.execute('PRAGMA busy_timeout=0');db.execute('PRAGMA read_uncommitted=OFF')
    retained=None;mode=None
    def emit(req,begin,payload,trace_at):
        result={'case':args.case,'role':args.role,'pid':os.getpid(),'request':req,
                'begin_ns':begin,'end_ns':time.monotonic_ns(),'sql':traces[trace_at:],
                'in_transaction':db.in_transaction,'total_changes':db.total_changes,
                'authority':'none','input_dispatched':False,**payload}
        print(json.dumps(result,sort_keys=True,separators=(',',':')),flush=True)
    try:
        for line in sys.stdin:
            req=json.loads(line);op=req['op'];begin=time.monotonic_ns();trace_at=len(traces)
            payload={}
            if args.role=='writer' and op=='init':
                db.execute('PRAGMA page_size=4096')
                jm=db.execute('PRAGMA journal_mode=WAL').fetchone()[0]
                db.execute('PRAGMA synchronous=FULL')
                db.execute('PRAGMA wal_autocheckpoint=1')
                db.execute('PRAGMA journal_size_limit=16384')
                db.executescript('CREATE TABLE meta(id INTEGER PRIMARY KEY,generation INTEGER,retired INTEGER);'
                  'INSERT INTO meta VALUES(1,1,0);'
                  'CREATE TABLE history(intent_id TEXT,intent_seq INTEGER PRIMARY KEY,from_generation INTEGER,'
                  'to_generation INTEGER,confirmation_content_id TEXT,confirmation_revision INTEGER);')
                obj=WatermarkLedger(2)
                for seq in range(1,4):
                    if obj.apply(receipt(seq))!='APPLIED':raise RuntimeError('INITIAL_ADMISSION')
                db.execute('BEGIN IMMEDIATE');save(db,obj);db.execute('COMMIT')
                checkpoint=list(db.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone())
                payload={'view':view(db),'checkpoint':checkpoint,'settings':{
                    key:db.execute('PRAGMA '+key).fetchone()[0] for key in
                    ['journal_mode','page_size','synchronous','wal_autocheckpoint','journal_size_limit','busy_timeout','read_uncommitted']}}
            elif args.role=='reader' and op=='start':
                mode=req['mode'];db.execute('BEGIN DEFERRED')
                if mode not in ('HELD_TX','COPY_RELEASE','BEGIN_ONLY'):raise ValueError('BAD_MODE')
                if mode!='BEGIN_ONLY':
                    retained=view(db)
                    if mode=='COPY_RELEASE':db.execute('COMMIT')
                payload={'retained':retained,'mode':mode}
            elif args.role=='writer' and op=='advance':
                writes=[]
                for _ in range(req['count']):
                    db.execute('BEGIN IMMEDIATE');before=view(db);obj=load(before)
                    r=receipt(obj.generation);status=obj.apply(r)
                    if status!='APPLIED':raise RuntimeError('INVALID_FRESH:'+status)
                    save(db,obj);db.execute('COMMIT')
                    writes.append({'request':dataclasses.asdict(r),'status':status,'after':view(db)})
                payload={'writes':writes,'view':view(db),
                    'checkpoint':list(db.execute('PRAGMA wal_checkpoint(PASSIVE)').fetchone())}
            elif args.role=='writer' and op=='truncate':
                payload={'checkpoint':list(db.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()),'view':view(db)}
            elif args.role=='reader' and op=='peek':
                sampled=None
                if mode!='COPY_RELEASE':sampled=view(db)
                payload={'sampled':sampled,'retained':retained,
                    'reported_view':retained if mode=='COPY_RELEASE' else sampled}
            elif args.role=='reader' and op=='release':
                if db.in_transaction:db.execute('COMMIT')
                payload={'retained':retained}
            elif op=='close':
                if db.in_transaction:raise RuntimeError('UNCLOSED_TRANSACTION')
                emit(req,begin,payload,trace_at);break
            else:raise ValueError('INVALID_OPERATION')
            emit(req,begin,payload,trace_at)
    finally:db.close()

if __name__=='__main__':main()
