#!/usr/bin/env python3
import argparse, hashlib, json, os, sqlite3, tempfile
from pathlib import Path

POLICIES = ('DELIVERY_GC','ACK_PAGE_GC','ACK_REFCOUNT_GC')
SCENARIOS = ('NO_ACK_DISTINCT','ACK_PAGE1_DISTINCT','ACK_PAGE1_SHARED','ACK_BOTH_SHARED','DUPLICATE_ACK_PAGE1','STALE_EPOCH_ACK','OVER_PREFIX_ACK')

def snap(conn):
    return {
        'meta': conn.execute('select epoch,ack_frontier from meta').fetchone(),
        'pages': conn.execute('select seq,epoch,delivered,acked from pages order by seq').fetchall(),
        'page_blobs': conn.execute('select seq,sha from page_blobs order by seq,sha').fetchall(),
        'blobs': [(r[0], len(r[1]), hashlib.sha256(r[1]).hexdigest()) for r in conn.execute('select sha,data from blobs order by sha')],
    }

def ack_and_gc(conn, policy, epoch, ack_seq):
    journal=[]
    before=snap(conn)
    conn.execute('BEGIN IMMEDIATE')
    row=conn.execute('select epoch,ack_frontier from meta').fetchone()
    store_epoch, frontier=row
    max_seq=conn.execute('select max(seq) from pages').fetchone()[0] or 0
    if epoch != store_epoch:
        status='refused_stale_epoch'
    elif type(ack_seq) is not int or ack_seq < frontier or ack_seq > max_seq:
        status='refused_invalid_prefix'
    elif ack_seq == frontier:
        status='duplicate'
    else:
        conn.execute('update pages set acked=1 where seq>? and seq<=?',(frontier,ack_seq))
        conn.execute('update meta set ack_frontier=?',(ack_seq,))
        status='applied'
    deleted=[]
    if policy == 'DELIVERY_GC':
        # Unsafe comparator: delivery is treated as release permission.
        rows=conn.execute('''select b.sha from blobs b where not exists (
            select 1 from page_blobs pb join pages p on p.seq=pb.seq
            where pb.sha=b.sha and p.delivered=0)''').fetchall()
        deleted=[r[0] for r in rows]
    elif policy == 'ACK_PAGE_GC':
        # Unsafe comparator: a blob touched by any acknowledged page is reclaimed.
        rows=conn.execute('''select distinct b.sha from blobs b join page_blobs pb on pb.sha=b.sha
            join pages p on p.seq=pb.seq where p.acked=1''').fetchall()
        deleted=[r[0] for r in rows]
    else:
        rows=conn.execute('''select b.sha from blobs b where not exists (
            select 1 from page_blobs pb join pages p on p.seq=pb.seq
            where pb.sha=b.sha and p.acked=0)''').fetchall()
        deleted=[r[0] for r in rows]
    for sha in deleted:
        conn.execute('delete from blobs where sha=?',(sha,))
    conn.commit()
    after=snap(conn)
    journal.append({'op':'ack_gc','request':{'epoch':epoch,'ack_seq':ack_seq},'status':status,'deleted':deleted,
                    'authority':'none','acknowledged':status in ('applied','duplicate'),'input_dispatched':False})
    return before, after, journal

def gc_only(conn, policy):
    # Use the same transaction machinery without advancing ACK.
    epoch, frontier = conn.execute('select epoch,ack_frontier from meta').fetchone()
    return ack_and_gc(conn, policy, epoch, frontier)

def resolve_unacked(conn):
    result=[]
    for seq,sha in conn.execute('''select p.seq,pb.sha from pages p join page_blobs pb on pb.seq=p.seq where p.acked=0 order by p.seq'''):
        row=conn.execute('select data from blobs where sha=?',(sha,)).fetchone()
        result.append({'seq':seq,'sha':sha,'available':row is not None,
                       'actual_sha256': hashlib.sha256(row[0]).hexdigest() if row else None})
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--case-id',required=True); ap.add_argument('--policy',choices=POLICIES,required=True); ap.add_argument('--scenario',choices=SCENARIOS,required=True)
    a=ap.parse_args()
    epoch='epoch-ack-gc-v1'
    shared='SHARED' in a.scenario or a.scenario=='ACK_BOTH_SHARED'
    a_bytes=(b'PNG-A:'+a.case_id.encode())*7
    b_bytes=a_bytes if shared else (b'PNG-B:'+a.case_id.encode())*9
    sha_a=hashlib.sha256(a_bytes).hexdigest(); sha_b=hashlib.sha256(b_bytes).hexdigest()
    with tempfile.TemporaryDirectory(prefix='ack-gc-') as td:
        db=Path(td)/'store.db'; conn=sqlite3.connect(db)
        conn.executescript('''
        pragma journal_mode=DELETE; pragma synchronous=FULL;
        create table meta(epoch text not null, ack_frontier integer not null);
        create table pages(seq integer primary key, epoch text not null, delivered integer not null, acked integer not null);
        create table blobs(sha text primary key, data blob not null);
        create table page_blobs(seq integer not null, sha text not null, primary key(seq,sha));
        ''')
        conn.execute('insert into meta values(?,0)',(epoch,))
        conn.execute('insert into blobs values(?,?)',(sha_a,a_bytes))
        if sha_b != sha_a: conn.execute('insert into blobs values(?,?)',(sha_b,b_bytes))
        conn.executemany('insert into pages values(?,?,1,0)',[(1,epoch),(2,epoch)])
        conn.executemany('insert into page_blobs values(?,?)',[(1,sha_a),(2,sha_b)])
        conn.commit()
        initial=snap(conn)
        operations=[]
        if a.scenario=='NO_ACK_DISTINCT':
            b0,b1,j=gc_only(conn,a.policy); operations += j
        elif a.scenario=='ACK_PAGE1_DISTINCT' or a.scenario=='ACK_PAGE1_SHARED':
            b0,b1,j=ack_and_gc(conn,a.policy,epoch,1); operations += j
        elif a.scenario=='ACK_BOTH_SHARED':
            b0,b1,j=ack_and_gc(conn,a.policy,epoch,2); operations += j
        elif a.scenario=='DUPLICATE_ACK_PAGE1':
            b0,b1,j=ack_and_gc(conn,a.policy,epoch,1); operations += j
            b2,b3,j=ack_and_gc(conn,a.policy,epoch,1); operations += j
        elif a.scenario=='STALE_EPOCH_ACK':
            b0,b1,j=ack_and_gc(conn,a.policy,'epoch-old',1); operations += j
        elif a.scenario=='OVER_PREFIX_ACK':
            b0,b1,j=ack_and_gc(conn,a.policy,epoch,3); operations += j
        final=snap(conn); resolution=resolve_unacked(conn)
        out={'schema':'agent-interface/referenced-image-ack-gc-case-v1','case_id':a.case_id,'policy':a.policy,'scenario':a.scenario,
             'epoch':epoch,'shared':shared,'source':{'sha_a':sha_a,'sha_b':sha_b,'bytes_a':len(a_bytes),'bytes_b':len(b_bytes)},
             'initial':initial,'operations':operations,'final':final,'resolution':resolution,'pid':os.getpid()}
        print(json.dumps(out,sort_keys=True,separators=(',',':')))
        conn.close()
if __name__=='__main__': main()
