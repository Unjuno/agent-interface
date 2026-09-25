"""One private SQLite benchmark or contract worker; no GUI/network actions."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import time
from query import query
from sink import Store

ROOT = Path(__file__).resolve().parent
SQL = 'SELECT ordinal,job_id,revision,value,kind FROM commits WHERE job_id=? ORDER BY ordinal'
INDEX_SQL = 'CREATE INDEX commits_by_job ON commits(job_id)'
ARMS = ('PLAIN', 'INDEXED')
CASES = ('applied', 'stale', 'revision_conflict', 'same_value', 'absent',
         'altered_request', 'invalid_epoch', 'duplicate_commit', 'missing_commit', 'unknown_status')

def wire(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()

def sha(data):
    return hashlib.sha256(data).hexdigest()

def request(session, job, revision, value, kind='AUTO'):
    return dict(session=session, document='doc', epoch='epoch-1', job_id=job,
                revision=revision, value=value, kind=kind)

def logical(con):
    h = hashlib.sha256()
    counts = {}
    for table, order in (('document', 'id'), ('commits', 'ordinal'), ('seen', 'job_id')):
        h.update((table + '\n').encode())
        count = 0
        for row in con.execute('SELECT * FROM ' + table + ' ORDER BY ' + order):
            h.update(wire(row) + b'\n')
            count += 1
        counts[table] = count
    return dict(sha256=h.hexdigest(), counts=counts)

def call_timed(fn):
    w0 = time.monotonic_ns()
    c0 = time.process_time_ns()
    value = fn()
    c1 = time.process_time_ns()
    w1 = time.monotonic_ns()
    return dict(wall=[w0,w1], cpu=[c0,c1], result=value)

def indexed(store, arm):
    if arm == 'INDEXED':
        return call_timed(lambda: (store.db.execute(INDEX_SQL), None)[1])
    return None

def source_ids():
    return {name: sha((ROOT / name).read_bytes()) for name in ('query.py', 'sink.py', 'worker.py')}

def seed(store, n):
    """Synthetic input history; NOT measured Store.apply throughput."""
    store.db.execute('BEGIN IMMEDIATE')
    for i in range(1,n+1):
        j = request(store.session, f'bg-{i:08d}', i, f'value-{i:08d}')
        store.db.execute('INSERT INTO commits VALUES(?,?,?,?,?)',
                         (i, j['job_id'], i, j['value'], j['kind']))
        store.db.execute('INSERT INTO seen VALUES(?,?,?)', (j['job_id'], sha(wire(j)), 'APPLIED'))
    store.db.execute('UPDATE document SET revision=?,value=? WHERE id=1', (n, f'value-{n:08d}'))
    store.db.execute('COMMIT')

def performance(directory, n, arm, repetition, phase):
    db = directory / 'workload.sqlite'
    session = f'i6k2-{phase}-{n}'
    store = Store(db, session, 'REVISION_FENCE')
    try:
        seed(store,n)
        seed_state = logical(store.db)
        seed_bytes = db.stat().st_size
        build = indexed(store,arm)
        before = logical(store.db)
        index_bytes = db.stat().st_size
        index_list = store.db.execute('PRAGMA index_list(commits)').fetchall()
        columns = store.db.execute('PRAGMA index_info(commits_by_job)').fetchall()
        ids = (1,n//2,n,n+1)
        requests = [request(session, f'bg-{i:08d}' if i <= n else 'absent-job',
                            i, f'value-{i:08d}') for i in ids]
        plans = [store.db.execute('EXPLAIN QUERY PLAN ' + SQL,(j['job_id'],)).fetchall()
                 for j in requests]
        before_hash = sha(db.read_bytes())
        warmups = []
        for r in range(2):
            for k,j in enumerate(requests):
                warmups.append(dict(round=r, query_class=k, result=query(db,j,session)))
        samples = []
        for r in range(11):
            for x in range(4):
                k = (r+x)%4
                row = call_timed(lambda j=requests[k]: query(db,j,session))
                samples.append(dict(round=r,query_class=k,**row))
        after_hash = sha(db.read_bytes())
        after_query = logical(store.db)
        appends = []
        for i in range(1,22):
            j = request(session,f'append-{i:08d}',n+i,f'append-value-{i:08d}','SUBMIT')
            appends.append(dict(request=j,**call_timed(lambda j=j: store.apply(j))))
        final = logical(store.db)
        final_bytes = db.stat().st_size
        pragmas = {key:store.db.execute('PRAGMA '+key).fetchone()[0]
                   for key in ('journal_mode','synchronous','page_size','page_count','read_uncommitted')}
        return dict(kind='performance',phase=phase,n=n,arm=arm,repetition=repetition,
                    session=session,pid=os.getpid(),affinity=sorted(os.sched_getaffinity(0)),
                    source_ids=source_ids(),seed=seed_state,before=before,after_query=after_query,
                    seed_bytes=seed_bytes,index_bytes=index_bytes,final_bytes=final_bytes,
                    index_build=build,index_list=index_list,index_columns=columns,plans=plans,
                    db_sha_before_queries=before_hash,db_sha_after_queries=after_hash,
                    final_db_sha256=sha(db.read_bytes()),pragmas=pragmas,requests=requests,
                    warmups=warmups,samples=samples,appends=appends,final=final)
    finally:
        store.close()

def contracts(directory, arm, phase):
    rows = []
    for name in CASES:
        db = directory / (name+'.sqlite')
        session = 'contract-'+name
        store = Store(db,session,'REVISION_FENCE')
        try:
            indexed(store,arm)
            j = request(session,'target',2,'aa')
            setup = []
            if name == 'stale':
                setup.append(store.apply(request(session,'other',5,'zz')))
            elif name == 'revision_conflict':
                setup.append(store.apply(request(session,'other',2,'zz')))
            elif name == 'same_value':
                setup.append(store.apply(request(session,'other',2,'aa')))
            if name != 'absent':
                setup.append(store.apply(j))
            intervention = None
            if name == 'altered_request':
                j = {**j,'value':'bb'}
            elif name == 'invalid_epoch':
                j = {**j,'epoch':'other-epoch'}
            elif name == 'duplicate_commit':
                intervention = 'INSERT second matching commit; deliberate inconsistent evidence'
                store.db.execute('INSERT INTO commits(job_id,revision,value,kind) VALUES(?,?,?,?)',
                                 ('target',2,'aa','AUTO'))
            elif name == 'missing_commit':
                intervention = 'DELETE target commit; deliberate inconsistent evidence'
                store.db.execute('DELETE FROM commits')
            elif name == 'unknown_status':
                intervention = 'UPDATE stored status; deliberate inconsistent evidence'
                store.db.execute("UPDATE seen SET status='UNRECOGNIZED'")
            before = db.read_bytes()
            trace = []
            result = query(db,j,session,trace)
            after = db.read_bytes()
            rows.append(dict(name=name,request=j,session=session,setup=setup,intervention=intervention,
                             db_b64=base64.b64encode(before).decode(),db_sha256=sha(before),
                             after_sha256=sha(after),result=result,sql_trace=trace,
                             index_list=store.db.execute('PRAGMA index_list(commits)').fetchall()))
        finally:
            store.close()
    return dict(kind='contracts',phase=phase,arm=arm,pid=os.getpid(),
                source_ids=source_ids(),affinity=sorted(os.sched_getaffinity(0)),cases=rows)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--arm',choices=ARMS,required=True)
    p.add_argument('--n',type=int,default=0)
    p.add_argument('--rep',type=int,default=0)
    p.add_argument('--phase',choices=('construction','formal'),required=True)
    p.add_argument('--contracts',action='store_true')
    a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    if not a.contracts and (a.n < 4 or a.rep not in range(3)):
        p.error('invalid workload')
    result = contracts(a.out,a.arm,a.phase) if a.contracts else performance(a.out,a.n,a.arm,a.rep,a.phase)
    print(wire(result).decode(),flush=True)

if __name__=='__main__':
    main()
