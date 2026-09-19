"""Declared common-runtime readiness smoke; not freeze qualification or model timing."""
import argparse,hashlib,json,queue,subprocess,sys,threading,time
from pathlib import Path

HERE=Path(__file__).resolve().parent
LIVE=HERE.parent/'live_control'

def probe(app,seed,stress,out):
    p=subprocess.Popen([sys.executable,str(LIVE/'interactive_v10.py'),'--app',app,'--seed',str(seed),
        '--presentation','full','--out',str(out)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    q=queue.Queue();events=[];sequence=0;counter=0
    def reader():
        try:
            for line in p.stdout:q.put(json.loads(line))
        finally:q.put(None)
    threading.Thread(target=reader,daemon=True).start()
    def event(kind):
        nonlocal sequence
        while True:
            row=q.get(timeout=30)
            if row is None:raise RuntimeError('runtime exited')
            events.append(row)
            if row['event']=='observation':sequence=row['sequence']
            if row['event']==kind:return row
    def send(command):p.stdin.write(json.dumps(command)+'\n');p.stdin.flush()
    def run(steps):
        nonlocal counter
        counter+=1
        send(dict(op='submit',id=f'p{counter}',expected_sequence=sequence,
            valid_until_ns=time.perf_counter_ns()+10_000_000_000,steps=steps))
        result=event('terminal')
        assert result['status']=='completed' and result['release']['verified'],result
    def key(k):return dict(op='key',key=k)
    def text(t):return dict(op='text',text=str(t))
    def chord(k):return dict(op='chord',modifier='Control_L',key=k)
    settle=dict(op='settle',quiet_ms=80,timeout_ms=750)
    try:
        ready=event('ready');event('observation');goal=ready['goal']
        if stress:
            send(dict(op='submit',id='expired',expected_sequence=sequence,valid_until_ns=time.perf_counter_ns()-1,
                steps=[text('bad')]))
            rejected=event('rejected')
            assert 'expired' in rejected['reason']
            assert not any(r['event'] in ('accepted','input_admission') for r in events)
        if app=='xterm':run([text(goal['token']),key('Return'),settle])
        elif app=='chromium':
            run([chord('l'),text(goal['url']),key('Return'),settle])
            context=dict(next(r for r in reversed(events) if r['event']=='observation')['context'])
            assert 'AI FORM READY' in context['windows']
            run([text(goal['token']),key('Return'),settle])
        elif app=='calc':
            run([text(goal['a']),key('Return'),text(goal['b']),key('Return'),chord('s'),settle])
            context=dict(next(r for r in reversed(events) if r['event']=='observation')['context'])
            assert 'Confirm File Format' in context['windows']
            run([key('Return'),settle])
        else:run([key('F1'),chord('a'),key('Right'),chord('s'),settle])
        send(dict(op='finish'));score=event('independent_evaluation');p.wait(timeout=15)
        assert p.returncode==0
        return dict(app=app,seed=seed,stress=stress,task_success=score['success'],actual=score['actual'],
            stale_rejection_verified=stress,accepted_programs=counter,
            observations=sum(r['event']=='observation' for r in events),
            scope='scripted readiness smoke; expected task artifacts scored after control')
    finally:
        if p.poll() is None:
            p.stdin.close()
            try:p.wait(timeout=15)
            except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=5)
        if out.exists():(out/'stderr.txt').write_text(p.stderr.read())

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    reference=json.loads((LIVE/'results/presentation-assistant-01/sources.json').read_text())
    for name,digest in reference.items():assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==digest,name
    cases=[dict(app=app,seed=970101+i,stress=bool(i)) for app in ('xterm','chromium','calc','inkscape') for i in (0,1)]
    manifest=dict(reference_commit='7427bdd',reference_sources=reference,
        harness_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),cases=cases,
        presentation='full',per_intent_validity_seconds=10,quiet_ms=80,timeout_ms=750,
        semantics='same interactive_v10 and transitive runtime in all cases',
        stress='already-expired input submission before normal task',
        graphics='keyboard selection and right nudge, not drag or pointer coverage',
        excluded=['continuous motor','DOOM','transport disconnect','critical-event retention'],
        qualification=False)
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    rows=[]
    try:
        for case in cases:
            folder=args.out/f"{case['app']}-{case['seed']}"
            try:r=probe(**case,out=folder)
            except Exception as exc:r=dict(**case,error=repr(exc),task_success=False)
            rows.append(r);(args.out/'summary.json').write_text(json.dumps(rows,indent=2));print(json.dumps(r),flush=True)
    finally:(args.out/'summary.json').write_text(json.dumps(rows,indent=2))

if __name__=='__main__':main()
