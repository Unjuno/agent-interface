#!/usr/bin/env python3
import argparse, hashlib, json, os, sqlite3
from pathlib import Path

def snap(c):
    return {
      'pages': c.execute('select seq,acked from pages order by seq').fetchall(),
      'refs': c.execute('select seq,sha from page_blobs order by seq,sha').fetchall(),
      'blobs': [(r[0],len(r[1]),hashlib.sha256(r[1]).hexdigest()) for r in c.execute('select sha,data from blobs order by sha')],
    }

def producer(db, data, sha):
    c=sqlite3.connect(db,timeout=3); before=snap(c); c.execute('begin immediate')
    row=c.execute('select data from blobs where sha=?',(sha,)).fetchone()
    if row is None: c.execute('insert into blobs values(?,?)',(sha,data))
    elif hashlib.sha256(row[0]).hexdigest()!=sha: raise RuntimeError('blob digest mismatch')
    c.execute('insert into pages values(2,0)'); c.execute('insert into page_blobs values(2,?)',(sha,)); c.commit()
    after=snap(c); c.close(); return {'op':'producer','before':before,'after':after}

def scan(db):
    c=sqlite3.connect(db,timeout=3)
    rows=c.execute('''select b.sha from blobs b where not exists(
      select 1 from page_blobs pb join pages p on p.seq=pb.seq
      where pb.sha=b.sha and p.acked=0) order by b.sha''').fetchall(); before=snap(c); c.close()
    return {'op':'gc_scan','candidates':[r[0] for r in rows],'snapshot':before}

def delete(db, policy, candidates):
    c=sqlite3.connect(db,timeout=3); before=snap(c); c.execute('begin immediate')
    if policy=='STALE_SCAN_DELETE': deleted=list(candidates)
    else:
      rows=c.execute('''select b.sha from blobs b where not exists(
        select 1 from page_blobs pb join pages p on p.seq=pb.seq
        where pb.sha=b.sha and p.acked=0) order by b.sha''').fetchall(); deleted=[r[0] for r in rows]
    for sha in deleted: c.execute('delete from blobs where sha=?',(sha,))
    c.commit(); after=snap(c); c.close(); return {'op':'gc_delete','policy':policy,'input_candidates':candidates,'deleted':deleted,'before':before,'after':after}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('op',choices=['producer','scan','delete']); ap.add_argument('--db',required=True); ap.add_argument('--data-hex'); ap.add_argument('--sha'); ap.add_argument('--policy'); ap.add_argument('--candidates',default='[]'); a=ap.parse_args()
    if a.op=='producer': out=producer(a.db,bytes.fromhex(a.data_hex),a.sha)
    elif a.op=='scan': out=scan(a.db)
    else: out=delete(a.db,a.policy,json.loads(a.candidates))
    out['pid']=os.getpid(); print(json.dumps(out,sort_keys=True,separators=(',',':')))
if __name__=='__main__': main()
