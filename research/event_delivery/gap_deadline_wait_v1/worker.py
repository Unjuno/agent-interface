"""Finite notification-only event loop over a private pipe and SQLite fixture."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import selectors
import sqlite3
import sys
import time
from pathlib import Path
import contiguous_model as model
from gap_policy import GapPolicy, BUDGET_NS

POLICIES = ('RELATIVE_WAIT', 'DEADLINE_WAIT')

def remaining_ns(policy: str, first_ns: int, now_ns: int) -> int:
    if policy not in POLICIES:
        raise ValueError('unsupported wait policy')
    if any(type(x) is not int or x < 0 for x in (first_ns, now_ns)) or now_ns < first_ns:
        raise ValueError('invalid monotonic clock sample')
    return BUDGET_NS if policy == 'RELATIVE_WAIT' else max(0, first_ns + BUDGET_NS - now_ns)

def snapshot(con: sqlite3.Connection) -> dict:
    return {'consumer':[list(x) for x in con.execute('SELECT * FROM consumer ORDER BY seq')],
            'pending':[list(x) for x in con.execute('SELECT * FROM pending ORDER BY pos')],
            'ack':[list(x) for x in con.execute('SELECT * FROM ack')]}

def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument('--db',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--policy',choices=POLICIES,required=True)
    ap.add_argument('--case',required=True)
    a=ap.parse_args()
    con=sqlite3.connect(a.db,timeout=1)
    gate=GapPolicy('ELAPSED_80MS')
    sel=selectors.DefaultSelector()
    os.set_blocking(sys.stdin.fileno(),False)
    sel.register(sys.stdin.fileno(),selectors.EVENT_READ)
    raw=(a.out/'worker.jsonl').open('x',encoding='utf-8')
    line_no=0
    def record(kind: str, **kw) -> None:
        nonlocal line_no
        line_no+=1
        row={'line':line_no,'event_ns':time.monotonic_ns(),'kind':kind,'case':a.case,'pid':os.getpid(),**kw}
        raw.write(json.dumps(row,sort_keys=True,separators=(',',':'))+'\n')
        raw.flush()
    def check(reason: str) -> dict:
        before=snapshot(con)
        head=con.execute('SELECT seq,event_id,payload_sha FROM pending ORDER BY pos LIMIT 1').fetchone()
        mx=con.execute('SELECT COALESCE(MAX(seq),0) FROM consumer').fetchone()[0]
        stamp=time.monotonic_ns()
        key=[mx+1,head[0],head[1]] if head and head[0]>mx+1 else None
        if key is None:
            gate.clear(); result={'status':'NO_GAP','state':None}
        else:
            result=gate.observe(key,stamp)
        record('check',reason=reason,observed_ns=stamp,key=key,result=result,before=before,after=snapshot(con))
        return result
    try:
        result=check('initial')
        first=result['state']['first_ns']
        ready={'ready':True,'case':a.case,'pid':os.getpid(),'first_ns':first,
               'policy':a.policy,'selector':type(sel).__name__,'authority':False}
        record('ready',receipt=ready)
        print(json.dumps(ready),flush=True)
        buf=b''; stopped=False; messages=0
        while not stopped:
            if messages>64 or time.monotonic_ns()-first>2_000_000_000:
                raise RuntimeError('finite worker budget exceeded')
            s=gate.state
            clock_sample=time.monotonic_ns()
            timeout_ns=(remaining_ns(a.policy,s['first_ns'],clock_sample)
                        if s is not None and s['receipt'] is None else None)
            # Deadline eligibility is checked even if the pipe is perpetually readable.
            if timeout_ns == 0 and a.policy == 'DEADLINE_WAIT':
                check('deadline_due'); continue
            begin=time.monotonic_ns()
            events=sel.select(None if timeout_ns is None else timeout_ns/1_000_000_000)
            end=time.monotonic_ns()
            record('wait',clock_sample_ns=clock_sample,begin_ns=begin,end_ns=end,
                   timeout_ns=timeout_ns,ready=bool(events),first_ns=s['first_ns'] if s else None,
                   notified=bool(s and s['receipt']))
            if not events:
                check('select_timeout'); continue
            chunk=os.read(sys.stdin.fileno(),8192)
            if not chunk: raise EOFError('producer closed without stop')
            buf+=chunk
            if len(buf)>16384: raise ValueError('bounded pipe frame exceeded')
            while b'\n' in buf and not stopped:
                frame,buf=buf.split(b'\n',1)
                req=json.loads(frame); messages+=1
                before=snapshot(con); start=time.monotonic_ns(); detail={}
                if req['op']=='tail':
                    with con:
                        detail['status']=model.producer_offer(con,2,6,'E6',model.digest('p6'),'sequence_pos')
                elif req['op']=='predecessor':
                    with con:
                        detail['offer']=model.producer_offer(con,2,4,'E4',model.digest('p4'),'sequence_pos')
                        detail['accepts']=[model.pending_retry(con,i,f'E{i}',model.digest(f'p{i}')) for i in (4,5)]
                    gate.clear()
                elif req['op']=='block':
                    if req.get('duration_ns') != 150_000_000: raise ValueError('wrong frozen block')
                    time.sleep(0.150)
                elif req['op']=='poll':
                    pass
                elif req['op']=='stop':
                    stopped=True
                else: raise ValueError('unknown operation')
                record('message',request=req,raw_frame_hex=frame.hex(),begin_ns=start,
                       end_ns=time.monotonic_ns(),before=before,after=snapshot(con),detail=detail)
                if req['op']=='poll': check('explicit_poll')
        record('terminal',state=snapshot(con),authority=False,input_dispatched=False,acknowledged=False)
        print(json.dumps({'done':True,'case':a.case,'pid':os.getpid(),'messages':messages}),flush=True)
    except BaseException as exc:
        record('failure',error=repr(exc))
        raise
    finally:
        sel.close();con.close();raw.close()

if __name__=='__main__': main()
