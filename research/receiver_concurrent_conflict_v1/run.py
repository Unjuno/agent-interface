from __future__ import annotations
import argparse, hashlib, json, os, sqlite3, subprocess, sys, time
from pathlib import Path
import receiver

def enc(x): return json.dumps(x, sort_keys=True, separators=(",", ":"), allow_nan=False)
def sha256_path(p: Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20), b''): h.update(b)
    return h.hexdigest()
def wait_paths(paths, deadline_s=5.0):
    end=time.monotonic()+deadline_s
    while time.monotonic()<end:
        if all(p.exists() for p in paths): return
        time.sleep(0.001)
    raise TimeoutError(f'missing readiness: {[str(p) for p in paths if not p.exists()]}')
def read_json(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def read_events(p):
    if not Path(p).exists(): return []
    return [json.loads(x) for x in Path(p).read_text(encoding='utf-8').splitlines() if x.strip()]
def db_snapshot(path):
    db=sqlite3.connect(path); db.row_factory=sqlite3.Row
    try:
        return {'context':[dict(r) for r in db.execute('SELECT * FROM context ORDER BY singleton')],
                'effects':[dict(r) for r in db.execute('SELECT * FROM effects ORDER BY effect_id')],
                'decisions':[dict(r) for r in db.execute('SELECT * FROM decisions ORDER BY scope,command_id')],
                'integrity_check':db.execute('PRAGMA integrity_check').fetchone()[0]}
    finally: db.close()
def validate_schedule(schedule):
    seen=set()
    for i,x in enumerate(schedule,1):
        if set(x)!={'case_id','launch_order','a_delta'}: raise ValueError(f'exact schedule fields row {i}')
        if x['case_id'] in seen: raise ValueError('duplicate case id')
        seen.add(x['case_id'])
        if x['launch_order'] not in (['a','b'],['b','a']): raise ValueError('bad launch order')
        if x['a_delta'] not in (3,4): raise ValueError('bad a_delta')

def run_replay(dbp, req):
    p=subprocess.run([sys.executable,str(Path(__file__).with_name('receiver.py')),'--db',str(dbp),'--policy','outcome_first'],
                     input=enc(req),text=True,capture_output=True,timeout=10,cwd=Path(__file__).parent)
    return {'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}

def run_case(root:Path,item):
    cid=item['case_id']; cdir=root/cid; cdir.mkdir(parents=True); dbp=cdir/'state.sqlite'; receiver.initialize(dbp,allowed=True)
    ad=item['a_delta']; bd=7-ad
    reqs={l:{'scope':receiver.SCOPE,'command_id':f'cmd-{cid}','context_id':'A','generation':1,'allowed':True,'delta':d} for l,d in [('a',ad),('b',bd)]}
    for l in ('a','b'): (cdir/f'request_{l}.json').write_text(enc(reqs[l])+'\n',encoding='utf-8')
    gate=cdir/'gate'; procs={}
    for label in item['launch_order']:
        cmd=[sys.executable,str(Path(__file__).with_name('worker.py')),'--db',str(dbp),'--request',str(cdir/f'request_{label}.json'),'--gate',str(gate),
             '--ready',str(cdir/f'{label}.ready.json'),'--events',str(cdir/f'{label}.events.jsonl'),'--output',str(cdir/f'{label}.out.json'),'--label',label]
        procs[label]=subprocess.Popen(cmd,cwd=Path(__file__).parent,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    wait_paths([cdir/'a.ready.json',cdir/'b.ready.json'])
    gate_ns=time.monotonic_ns(); fd=os.open(gate,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600); os.write(fd,f'{gate_ns}\n'.encode()); os.fsync(fd); os.close(fd)
    prec={}
    for l in ('a','b'):
        try: so,se=procs[l].communicate(timeout=10)
        except subprocess.TimeoutExpired: procs[l].kill(); so,se=procs[l].communicate(); raise
        prec[l]={'returncode':procs[l].returncode,'stdout':so,'stderr':se}
    outs={l:read_json(cdir/f'{l}.out.json') if (cdir/f'{l}.out.json').exists() else None for l in ('a','b')}
    events={l:read_events(cdir/f'{l}.events.jsonl') for l in ('a','b')}
    rec={'case_id':cid,'launch_order':item['launch_order'],'a_delta':ad,'requests':reqs,'gate_created_ns':gate_ns,'workers':outs,'worker_processes':prec,'events':events,
         'replays':{l:run_replay(dbp,reqs[l]) for l in ('a','b')},'db':db_snapshot(dbp),'db_sha256':sha256_path(dbp)}
    (cdir/'case.json').write_text(enc(rec)+'\n',encoding='utf-8'); return rec

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); ap.add_argument('--schedule',required=True); a=ap.parse_args()
    root=Path(a.out); sp=Path(a.schedule)
    if root.exists(): raise FileExistsError(root)
    schedule=json.loads(sp.read_text()); validate_schedule(schedule); root.mkdir(parents=True); (root/'schedule.json').write_bytes(sp.read_bytes())
    rows=[run_case(root,x) for x in schedule]
    with (root/'ledger.jsonl').open('w') as f:
        for r in rows: f.write(enc(r)+'\n')
    print(enc({'cases':len(rows),'ledger_sha256':sha256_path(root/'ledger.jsonl'),'schedule_sha256':sha256_path(root/'schedule.json')}))
if __name__=='__main__': main()
