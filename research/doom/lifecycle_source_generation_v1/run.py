"""Run one fresh source-generation lifecycle MAP01 case."""
from __future__ import annotations
import argparse,hashlib,json,os,queue,signal,subprocess,sys,threading,time,traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent

def dump(path,obj):Path(path).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def run_case(runtime,out,spec):
    out.mkdir(parents=True,exist_ok=False);auth=out/'bootstrap.Xauthority';auth.touch()
    env=os.environ.copy();env.update(AI_RUNTIME_ROOT=str(runtime),XAUTHORITY=str(auth),
      LIFECYCLE_DELIVERY_FRESHNESS_MS=str(spec['delivery_freshness_ms']),
      LIFECYCLE_SOURCE_PROGRESS_MS=str(spec['source_progress_freshness_ms']),LIFECYCLE_FAULT=spec['fault'])
    fixture=runtime/'research/doom/fixtures/map01-threat-contact-v2/fixture.json'
    cmd=[sys.executable,str(HERE/'session.py'),'--out',str(out/'runtime'),'--seed',str(spec['seed']),
         '--timeout-seconds',str(spec['timeout_seconds']),'--skill','1','--load-fixture-manifest',str(fixture)]
    dump(out/'launch.json',dict(spec=spec,command=cmd,fixture_sha256=sha(fixture),sources={p.name:sha(p) for p in HERE.glob('*.py')}))
    sent=[];raw=(out/'stdout.jsonl').open('w');err=(out/'stderr.txt').open('w');q=queue.Queue();latest=None
    p=subprocess.Popen(cmd,env=env,cwd=runtime/'research/doom',stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,bufsize=1,start_new_session=True)
    def reader():
        for line in p.stdout:
            raw.write(line);raw.flush()
            try:q.put(json.loads(line))
            except json.JSONDecodeError:q.put({'event':'invalid_stdout','text':line})
        q.put(None)
    th=threading.Thread(target=reader,daemon=True);th.start()
    def wait(pred,timeout=20):
        nonlocal latest
        end=time.monotonic()+timeout
        while True:
            row=q.get(timeout=max(.001,end-time.monotonic()))
            if row is None:raise RuntimeError('early exit: '+(out/'stderr.txt').read_text()[-3000:])
            if row.get('event')=='invalid_stdout':raise ValueError(row['text'])
            if row.get('event')=='observation':latest=row
            if pred(row):return row
            if time.monotonic()>=end:raise TimeoutError('event predicate')
    def send(row):
        row=dict(row);row['driver_sent_ns']=time.perf_counter_ns();sent.append(row);p.stdin.write(json.dumps(row)+'\n');p.stdin.flush()
    try:
        wait(lambda r:r.get('event')=='ready');initial=wait(lambda r:r.get('event')=='observation' and r.get('id')=='initial');time.sleep(.13)
        send({'op':'clock'});clock=wait(lambda r:r.get('event')=='clock');deadline=clock['runtime_ns']+spec['cutoff_ms']*1_000_000
        send({'op':'submit','id':'primary','steps':[{'op':'hold','keys':['a','d'],'duration_ms':5000}],
              'expected_sequence':latest['sequence'],'valid_until_ns':deadline})
        terminal=wait(lambda r:r.get('event')=='terminal' and r.get('id')=='primary',12)
        pause=deadline+150_000_000-time.perf_counter_ns()
        if pause>0:time.sleep(pause/1e9)
        send({'op':'clock'});clock2=wait(lambda r:r.get('event')=='clock')
        send({'op':'submit','id':'late','steps':[{'op':'hold','keys':['a','d'],'duration_ms':50}],
              'expected_sequence':latest['sequence'],'valid_until_ns':clock2['runtime_ns']+1_000_000_000})
        late=wait(lambda r:r.get('event')=='rejected' or (r.get('event')=='terminal' and r.get('id')=='late'),5)
        send({'op':'finish'});score=wait(lambda r:r.get('event')=='post_control_score',10);p.stdin.close();p.wait(timeout=10)
        if p.returncode:raise RuntimeError('session returncode '+str(p.returncode))
        dump(out/'driver.json',dict(sent=sent,initial=initial,terminal=terminal,late=late,score=score))
    except Exception as e:dump(out/'failure.json',dict(error=repr(e),traceback=traceback.format_exc(),sent=sent));raise
    finally:
        if p.poll() is None:
            try:send({'op':'finish'});p.stdin.close();p.wait(timeout=3)
            except Exception:
                os.killpg(p.pid,signal.SIGTERM)
                try:p.wait(timeout=3)
                except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
        th.join(timeout=2);raw.close();err.close();dump(out/'exit.json',dict(returncode=p.returncode))
    from audit import analyze
    result=analyze(out,runtime,HERE);dump(out/'result.json',result)
    if not result['integrity_pass']:raise RuntimeError(result['failures'])
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--runtime',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--plan',type=Path,required=True);ap.add_argument('--index',type=int,required=True);a=ap.parse_args()
    plan=json.loads(a.plan.read_text())
    for n,h in plan['sources'].items():
        if sha(HERE/n)!=h:raise RuntimeError('source pin mismatch: '+n)
    for n,h in plan['fixture'].items():
        if sha(a.runtime/'research/doom/fixtures/map01-threat-contact-v2'/n)!=h:raise RuntimeError('fixture pin mismatch: '+n)
    print(json.dumps(run_case(a.runtime.resolve(),a.out.resolve(),plan['cases'][a.index]),sort_keys=True),flush=True)
