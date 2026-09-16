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
        return {
          'context':[dict(r) for r in db.execute('SELECT * FROM context ORDER BY singleton')],
          'effects':[dict(r) for r in db.execute('SELECT * FROM effects ORDER BY effect_id')],
          'decisions':[dict(r) for r in db.execute('SELECT * FROM decisions ORDER BY scope,command_id')],
          'integrity_check':db.execute('PRAGMA integrity_check').fetchone()[0],
        }
    finally: db.close()
def validate_schedule(schedule):
    seen=set()
    for i,item in enumerate(schedule,1):
        if set(item)!={'case_id','launch_order'}: raise ValueError(f'exact schedule fields required row {i}')
        if item['case_id'] in seen: raise ValueError('duplicate case_id')
        seen.add(item['case_id'])
        if item['launch_order'] not in (['a','b'],['b','a']): raise ValueError('bad launch_order')

def run_case(root: Path, case_id: str, launch_order):
    cdir=root/case_id; cdir.mkdir(parents=True)
    dbp=cdir/'state.sqlite'
    receiver.initialize(dbp, allowed=True)
    req={'scope':receiver.SCOPE,'command_id':f'cmd-{case_id}','context_id':'A','generation':1,'allowed':True,'delta':3}
    (cdir/'request.json').write_text(enc(req)+'\n', encoding='utf-8')
    gate=cdir/'gate'; procs={}
    for label in launch_order:
        cmd=[sys.executable, str(Path(__file__).with_name('worker.py')),
             '--db',str(dbp),'--request',str(cdir/'request.json'),'--gate',str(gate),
             '--ready',str(cdir/f'{label}.ready.json'),'--events',str(cdir/f'{label}.events.jsonl'),
             '--output',str(cdir/f'{label}.out.json'),'--label',label]
        procs[label]=subprocess.Popen(cmd, cwd=Path(__file__).parent, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    wait_paths([cdir/'a.ready.json', cdir/'b.ready.json'])
    gate_created_ns=time.monotonic_ns()
    fd=os.open(gate, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
    os.write(fd, f'{gate_created_ns}\n'.encode()); os.fsync(fd); os.close(fd)
    proc_records={}
    for label in ('a','b'):
        try: stdout,stderr=procs[label].communicate(timeout=10)
        except subprocess.TimeoutExpired:
            procs[label].kill(); stdout,stderr=procs[label].communicate(); raise
        proc_records[label]={'returncode':procs[label].returncode,'stdout':stdout,'stderr':stderr}
    replay=subprocess.run([sys.executable,str(Path(__file__).with_name('receiver.py')),'--db',str(dbp),'--policy','outcome_first'],
                          input=enc(req),text=True,capture_output=True,timeout=10,cwd=Path(__file__).parent)
    replay_record={'returncode':replay.returncode,'stdout':replay.stdout,'stderr':replay.stderr}
    outs={l:read_json(cdir/f'{l}.out.json') if (cdir/f'{l}.out.json').exists() else None for l in ('a','b')}
    events={l:read_events(cdir/f'{l}.events.jsonl') for l in ('a','b')}
    snap=db_snapshot(dbp)
    rec={'case_id':case_id,'launch_order':launch_order,'gate_created_ns':gate_created_ns,
         'workers':outs,'worker_processes':proc_records,'events':events,
         'replay':replay_record,'db':snap,'db_sha256':sha256_path(dbp)}
    (cdir/'case.json').write_text(enc(rec)+'\n',encoding='utf-8')
    return rec

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); ap.add_argument('--schedule',required=True)
    a=ap.parse_args(); root=Path(a.out); sched_path=Path(a.schedule)
    if root.exists(): raise FileExistsError(root)
    schedule=json.loads(sched_path.read_text(encoding='utf-8')); validate_schedule(schedule)
    root.mkdir(parents=True)
    (root/'schedule.json').write_bytes(sched_path.read_bytes())
    rows=[]
    for item in schedule:
        rows.append(run_case(root,item['case_id'],item['launch_order']))
    with (root/'ledger.jsonl').open('w',encoding='utf-8') as f:
        for r in rows: f.write(enc(r)+'\n')
    print(enc({'cases':len(rows),'ledger_sha256':sha256_path(root/'ledger.jsonl'),'schedule_sha256':sha256_path(root/'schedule.json'),'root':str(root)}))
if __name__=='__main__': main()
