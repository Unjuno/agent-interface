"""Paired local expiry probes, not a model performance comparison."""
import json,queue,subprocess,sys,threading,time,hashlib,argparse
from pathlib import Path
HERE=Path(__file__).resolve().parent


def probe(out,seed,leased):
    script='session_v3.py' if leased else 'session_v2.py'
    p=subprocess.Popen([sys.executable,str(HERE/script),'--app','xterm','--seed',str(seed),'--out',str(out)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    q=queue.Queue();seen=[]
    def reader():
        try:
            for line in p.stdout:q.put(json.loads(line))
        finally:q.put(None)
    threading.Thread(target=reader,daemon=True).start()
    def until(kind):
        while True:
            e=q.get(timeout=15)
            if e is None:raise RuntimeError('child exited')
            seen.append(e)
            if e['event']==kind:return e
    def send(c):p.stdin.write(json.dumps(c)+'\n');p.stdin.flush()
    try:
        ready=until('ready');initial=until('observation')
        deadline=time.perf_counter_ns()+200_000_000
        command=dict(op='submit',id='first',expected_sequence=initial['sequence'],valid_until_ns=deadline,
            steps=[dict(op='hold',keys=['Control_L'],duration_ms=400),dict(op='text',text=ready['goal']['token']),dict(op='key',key='Return')])
        send(command);terminal=until('terminal')
        assert terminal['release']['verified']
        if leased:
            assert terminal['status']=='expired' and terminal['steps_completed']==0
            assert not any(e['event']=='step_started' and e['step']>0 for e in seen)
            latest=[e for e in seen if e['event']=='observation'][-1]
            send(dict(op='submit',id='fresh',expected_sequence=latest['sequence'],valid_until_ns=time.perf_counter_ns()+2_000_000_000,
                steps=[dict(op='text',text=ready['goal']['token']),dict(op='key',key='Return')]))
            assert until('terminal')['status']=='completed'
        else:assert terminal['status']=='completed'
        send(dict(op='finish'));score=until('independent_evaluation');assert score['success']
        p.wait(timeout=10);assert p.returncode==0
        report=dict(seed=seed,leased=leased,deadline_ns=deadline,task_success=True,
            first_terminal=terminal['status'],release_verified=True,
            release_after_deadline_ms=(terminal['release']['verified_ns']-deadline)/1e6,
            tail_started_after_deadline=any(e['event']=='step_started' and e['id']=='first' and e['step']>0 and e['issued_ns']>=deadline for e in seen),
            accepted_programs=sum(e['event']=='accepted' for e in seen),
            post_expiry_down_admissions=sum(e['event']=='input_admission' and e['admitted_ns']>=e['valid_until_ns'] for e in seen) if leased else None,
            scope='local functional pair; server/client same WSL monotonic clock; no LLM comparison')
        (out/'lease-probe.json').write_text(json.dumps(report,indent=2));return report
    finally:
        if p.poll() is None:
            p.stdin.close()
            try:p.wait(timeout=10)
            except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=5)
        if out.exists():(out/'stderr.txt').write_text(p.stderr.read())


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=False);rows=[]
    names=('lease.py','executor_v3.py','session_v3.py','probe_lease.py','test_lease.py')
    (a.out/'freeze.json').write_text(json.dumps({n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in names},indent=2))
    for n in names:(a.out/('source-'+n)).write_bytes((HERE/n).read_bytes())
    try:
        for i,seed in enumerate((900101,900102)):
            for leased in ((False,True) if i==0 else (True,False)):
                try:r=probe(a.out/f'{seed}-{int(leased)}',seed,leased)
                except Exception as exc:r=dict(seed=seed,leased=leased,error=repr(exc))
                rows.append(r);print(json.dumps(r),flush=True)
    finally:(a.out/'summary.json').write_text(json.dumps(rows,indent=2))
