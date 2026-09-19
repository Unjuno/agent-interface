"""Scripted DOOM adapter readiness; no model-speed or game-success claim."""
import argparse,hashlib,json,queue,subprocess,sys,threading,time
from pathlib import Path

HERE=Path(__file__).resolve().parent

def probe(out,seed,mode):
    p=subprocess.Popen([sys.executable,str(HERE/'session_v5.py'),'--out',str(out),'--seed',str(seed)],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    q=queue.Queue();events=[];sequence=0
    def reader():
        try:
            for line in p.stdout:q.put(json.loads(line))
        finally:q.put(None)
    threading.Thread(target=reader,daemon=True).start()
    def event(kind):
        nonlocal sequence
        while True:
            row=q.get(timeout=30)
            if row is None:raise RuntimeError('runtime exited before '+kind)
            events.append(row)
            if row['event']=='observation':sequence=row['sequence']
            if row['event']==kind:return row
    def send(c):p.stdin.write(json.dumps(c)+'\n');p.stdin.flush()
    try:
        clock=event('clock_probe');rate=(clock['after_tic']-clock['before_tic'])/clock['wall_seconds']
        assert 30<=rate<=40,clock
        event('ready');event('observation')
        send(dict(op='submit',id='stale',expected_sequence=sequence,valid_until_ns=time.perf_counter_ns()-1,
                  steps=[dict(op='hold',key='Left',ms=50)]))
        assert 'expired' in event('rejected')['reason']
        assert not any(r['event'] in ('accepted','input_admission') for r in events)
        validity=200_000_000 if mode=='expiry' else 5_000_000_000
        steps=[dict(op='hold',key='Right',ms=100 if mode=='ordinary' else 1000)]
        if mode!='ordinary':steps.append(dict(op='hold',key='Left',ms=50))
        send(dict(op='submit',id='input',expected_sequence=sequence,
                  valid_until_ns=time.perf_counter_ns()+validity,steps=steps))
        if mode=='cancel':
            event('input_admission');send(dict(op='cancel',id='input'))
        terminal=event('terminal')
        expected={'ordinary':'completed','cancel':'cancelled','expiry':'expired'}[mode]
        assert terminal['status']==expected and terminal['release']['verified'],terminal
        assert terminal['steps_completed']==(1 if mode=='ordinary' else 0)
        assert not any(r['event']=='step_started' and r['step']==1 for r in events)
        # A separate fresh observation is allowed after interruption; it does not
        # authorize any old tail and is not evidence of game task completion.
        send(dict(op='submit',id='observe',expected_sequence=sequence,
                  valid_until_ns=time.perf_counter_ns()+5_000_000_000,steps=[dict(op='observe')]))
        observed=event('terminal')
        assert observed['status']=='completed' and observed['release']['verified'],observed
        send(dict(op='finish'));score=event('post_control_score');p.wait(timeout=15)
        assert p.returncode==0
        raw=[json.loads(x) for x in (out/'events.jsonl').read_text().splitlines()]
        delivered=[json.loads(x) for x in (out/'delivered.jsonl').read_text().splitlines()]
        assert raw==delivered
        owners=json.loads((out/'owner-events.json').read_text())
        assert owners and owners[-1]['event']=='owner_closed',owners[-1:]
        return dict(mode=mode,seed=seed,readiness_pass=True,observed_tics_per_second=rate,
                    terminal_status=terminal['status'],observations=sum(r['event']=='observation' for r in raw),
                    score=score,game_success_claim=False)
    finally:
        if p.poll() is None:
            p.stdin.close()
            try:p.wait(timeout=15)
            except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=5)
        if out.exists():(out/'stderr.txt').write_text(p.stderr.read())

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    cases=[dict(mode=mode,seed=990101+i) for i,mode in enumerate(('ordinary','cancel','expiry'))]
    manifest=dict(cases=cases,scope='scripted adapter readiness; not shared qualification',
        clock_rate_gate=[30,40],nominal_ticrate=35,presentation='full',
        sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),HERE/'session_v5.py')})
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    rows=[]
    for case in cases:
        try:r=probe(a.out/case['mode'],**case)
        except Exception as exc:r=dict(**case,readiness_pass=False,error=repr(exc))
        rows.append(r);(a.out/'summary.json').write_text(json.dumps(rows,indent=2));print(json.dumps(r),flush=True)
    if not all(r['readiness_pass'] for r in rows):raise SystemExit(1)

if __name__=='__main__':main()
