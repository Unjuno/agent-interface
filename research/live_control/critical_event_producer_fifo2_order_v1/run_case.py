import argparse, json, pathlib, sqlite3, subprocess, sys, time
from model import init_db, digest, ack_digest, ack_through, pending_retry, snap
p=argparse.ArgumentParser(); p.add_argument('--arm',choices=['seq_order_arrival','reverse_arrival'],required=True); p.add_argument('--case-id',required=True); p.add_argument('--out',required=True); a=p.parse_args()
out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=False); db=out/'state.db'; init_db(db)
root=pathlib.Path(__file__).parent
procs={}
for seq in (4,5):
    procs[seq]=subprocess.Popen([sys.executable,str(root/'worker.py'),str(db),str(seq),str(out/f'go{seq}'),str(out/f'worker{seq}.json')],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
order=(4,5) if a.arm=='seq_order_arrival' else (5,4)
for seq in order:
    (out/f'go{seq}').write_text('go\n')
    deadline=time.time()+5
    while not (out/f'worker{seq}.json').exists():
        if time.time()>deadline: raise TimeoutError(seq)
        time.sleep(0.005)
workers={}
for seq,p0 in procs.items():
    stdout,stderr=p0.communicate(timeout=5)
    workers[str(seq)]={'result':json.loads((out/f'worker{seq}.json').read_text()),'returncode':p0.returncode,'stdout':stdout,'stderr':stderr}
pending_before=snap(db)['pending']
c=sqlite3.connect(db,isolation_level=None); c.execute('BEGIN IMMEDIATE'); ad=ack_digest(c,2); ack1=ack_through(c,2,ad); c.execute('COMMIT'); c.close()
c=sqlite3.connect(db,isolation_level=None); c.execute('BEGIN IMMEDIATE'); ack2=ack_through(c,2,ad); c.execute('COMMIT'); c.close()
drain=[]
for _ in range(3):
    s=snap(db)
    if not s['pending']: break
    eid=s['pending'][0]; seq=int(eid[1:])
    c=sqlite3.connect(db,isolation_level=None); c.execute('BEGIN IMMEDIATE'); st=pending_retry(c,seq,eid,digest(f'p{seq}')); c.execute('COMMIT'); c.close()
    drain.append({'event_id':eid,'status':st})
    if st!='EVENT_ACCEPTED': break
result={'case_id':a.case_id,'arm':a.arm,'arrival_order':list(order),'workers':workers,'pending_before_ack':pending_before,'ack_first':ack1,'ack_replay':ack2,'drain':drain,'final':snap(db)}
(out/'result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
