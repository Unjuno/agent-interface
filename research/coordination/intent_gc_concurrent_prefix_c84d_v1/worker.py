"""Private SQLite adapter for a finite compaction study; no GUI/network."""
import json
import os
from pathlib import Path
import sqlite3
import sys
import time
from vendor531 import Receipt, WatermarkLedger


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def load(db):
    generation, watermark = db.execute('SELECT generation,watermark FROM meta').fetchone()
    ledger = WatermarkLedger(2)
    ledger.generation = generation
    ledger.retired_through_seq = watermark
    ledger.history = [Receipt(**json.loads(w)) for (w,) in db.execute('SELECT wire FROM receipts ORDER BY seq')]
    return ledger


def save(db, ledger):
    db.execute('UPDATE meta SET generation=?,watermark=?', (ledger.generation, ledger.retired_through_seq))
    db.execute('DELETE FROM receipts')
    db.executemany('INSERT INTO receipts VALUES(?,?)', [(r.intent_seq, encode(r.content())) for r in ledger.history])


def frontier(db):
    return db.execute('SELECT MAX(watermark,COALESCE((SELECT MAX(seq) FROM receipts),0)) FROM meta').fetchone()[0]


def receipt(seq, label=None, generation=None):
    g = seq if generation is None else generation
    return dict(intent_id=label or chr(64+seq), intent_seq=seq, from_generation=g,
                to_generation=g+1, confirmation_content_id='content-'+(label or chr(64+seq)),
                confirmation_revision=1)


def apply(db, wire):
    item = Receipt(**wire)
    ledger = load(db)
    status = ledger.apply(item)
    if status == 'APPLIED':
        save(db, ledger)
        db.execute('INSERT INTO effects VALUES(?,?,?,?)',
                   (item.intent_seq, item.intent_id, item.from_generation, item.to_generation))
    return status


def main():
    path, role = Path(sys.argv[1]), sys.argv[2]
    captured = None
    print(encode({'ready': True, 'pid': os.getpid(), 'role': role}), flush=True)
    for line in sys.stdin:
        request = json.loads(line)
        if request['op'] == 'close':
            print(encode({'id': request['id'], 'closed': True, 'pid': os.getpid()}), flush=True)
            return 0
        sql = []
        started = time.monotonic_ns()
        db = sqlite3.connect(path, timeout=1, isolation_level=None)
        db.set_trace_callback(sql.append)
        db.execute('PRAGMA journal_mode=DELETE')
        db.execute('PRAGMA synchronous=FULL')
        db.execute('PRAGMA read_uncommitted=OFF')
        try:
            op = request['op']
            if op == 'init':
                if role != 'actor':
                    raise ValueError('WRONG_ROLE')
                db.executescript('CREATE TABLE meta(generation INTEGER,watermark INTEGER);'
                                 'INSERT INTO meta VALUES(1,0);'
                                 'CREATE TABLE receipts(seq INTEGER PRIMARY KEY,wire TEXT);'
                                 'CREATE TABLE effects(seq INTEGER,label TEXT,from_g INTEGER,to_g INTEGER);')
                db.execute('BEGIN IMMEDIATE')
                for seq in (1,2,3):
                    if apply(db, receipt(seq)) != 'APPLIED':
                        raise ValueError('INIT_REFUSED')
                db.commit()
                status = 'INITIALIZED'
            elif op == 'apply':
                if role != 'actor':
                    raise ValueError('WRONG_ROLE')
                db.execute('BEGIN IMMEDIATE')
                status = apply(db, request['wire'])
                db.commit()
            elif op == 'capture':
                if role != 'compactor' or captured is not None:
                    raise ValueError('CAPTURE_STATE')
                db.execute('BEGIN')
                captured = frontier(db)
                db.commit()
                status = 'CAPTURED'
            elif op == 'compact':
                if role != 'compactor' or type(captured) is not int:
                    raise ValueError('NO_CAPTURE')
                policy = request['policy']
                if policy not in ('STALE_DELETE_ALL','BOUNDED_PREFIX','REVALIDATE_FRONTIER'):
                    raise ValueError('UNKNOWN_POLICY')
                db.execute('BEGIN IMMEDIATE')
                current = frontier(db)
                if policy == 'REVALIDATE_FRONTIER' and current != captured:
                    db.rollback()
                    status = 'DEFERRED_FRONTIER_CHANGED'
                else:
                    db.execute('UPDATE meta SET watermark=MAX(watermark,?)', (captured,))
                    if policy == 'BOUNDED_PREFIX':
                        db.execute('DELETE FROM receipts WHERE seq<=?', (captured,))
                    else:
                        db.execute('DELETE FROM receipts')
                    db.commit()
                    status = 'COMPACTED'
            else:
                raise ValueError('UNKNOWN_OPERATION')
            print(encode({'id':request['id'], 'op':op, 'status':status,
                          'captured':captured, 'pid':os.getpid(), 'sql':sql,
                          'started_ns':started, 'ended_ns':time.monotonic_ns(),
                          'authority':'none','input_dispatched':False}), flush=True)
        finally:
            db.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
