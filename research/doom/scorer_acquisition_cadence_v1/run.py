"""One finite real-X11 case per invocation; retain first outcome, never reuse output."""
from __future__ import annotations
import argparse, hashlib, json, os, queue, signal, subprocess, sys, threading, time, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent

def dump(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True)+'\n')

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def run_case(runtime, out, spec):
    fixture = runtime/'research/doom/fixtures/map01-threat-contact-v2/fixture.json'
    out.mkdir(parents=True, exist_ok=False)
    auth=out/'bootstrap.Xauthority';auth.touch()
    env=os.environ.copy();env.update(AI_RUNTIME_ROOT=str(runtime), SCORER_MODE=spec['mode'], XAUTHORITY=str(auth))
    command=[sys.executable,str(HERE/'session.py'),'--out',str(out/'runtime'),
        '--seed',str(spec['seed']),'--timeout-seconds','60','--skill','1',
        '--load-fixture-manifest',str(fixture)]
    dump(out/'launch.json',{'command':command,'spec':spec,'fixture_sha256':sha(fixture),
        'sources':{n:sha(HERE/n) for n in ('acquisition.py','session.py','run.py')}})
    stderr=(out/'stderr.txt').open('w');raw=(out/'stdout.jsonl').open('w')
    p=subprocess.Popen(command, env=env, cwd=runtime/'research/doom', stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=stderr, text=True, bufsize=1, start_new_session=True)
    q=queue.Queue();lock=threading.Lock();stop=threading.Event();sent=[];heartbeat=None
    def reader():
        for line in p.stdout:
            raw.write(line);raw.flush()
            try:q.put(json.loads(line))
            except json.JSONDecodeError:q.put({'event':'invalid_stdout','text':line})
        q.put(None)
    reader_thread=threading.Thread(target=reader,daemon=True);reader_thread.start()
    def wait(pred, timeout=20):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            row=q.get(timeout=max(.001,end-time.monotonic()))
            if row is None:raise RuntimeError('session exited: '+(out/'stderr.txt').read_text()[-1500:])
            if row.get('event')=='invalid_stdout':raise RuntimeError(row['text'])
            if pred(row):return row
        raise TimeoutError('predicate')
    def send(row):
        with lock:
            p.stdin.write(json.dumps(row)+'\n');p.stdin.flush()
    try:
        wait(lambda r:r.get('event')=='ready')
        initial=wait(lambda r:r.get('event')=='observation' and r.get('id')=='initial')
        send({'op':'clock'});clock=wait(lambda r:r.get('event')=='clock')
        program=[{'op':'hold','keys':spec['keys'],'duration_ms':5000}]
        send({'op':'submit','id':spec['id'],'expected_sequence':initial['sequence'],
              'valid_until_ns':clock['runtime_ns']+spec['cutoff_ms']*1_000_000,'steps':program})
        accepted=wait(lambda r:r.get('event')=='accepted' and r.get('id')==spec['id'])
        def write_clocks():
            sequence=0
            while not stop.wait(.05):
                row={'op':'clock','heartbeat':sequence,'sent_ns':time.perf_counter_ns()}
                try:send(row);sent.append(row);sequence+=1
                except (BrokenPipeError,ValueError):return
        heartbeat=threading.Thread(target=write_clocks,daemon=True);heartbeat.start()
        terminal=wait(lambda r:r.get('event')=='terminal' and r.get('id')==spec['id'],12)
        stop.set();heartbeat.join(timeout=2)
        send({'op':'finish'});score=wait(lambda r:r.get('event')=='post_control_score',10)
        p.stdin.close();p.wait(timeout=10)
        if p.returncode!=0:raise RuntimeError('session return code '+str(p.returncode))
        dump(out/'driver.json',{'accepted':accepted,'terminal':terminal,'score':score,'heartbeats_sent':sent})
    except Exception as error:
        dump(out/'failure.json',{'error':repr(error),'traceback':traceback.format_exc()})
        raise
    finally:
        stop.set()
        if heartbeat:heartbeat.join(timeout=2)
        if p.poll() is None:
            try:
                send({'op':'finish'});p.stdin.close();p.wait(timeout=3)
            except Exception:
                os.killpg(p.pid,signal.SIGTERM)
                try:p.wait(timeout=3)
                except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
        reader_thread.join(timeout=2);stderr.close();raw.close()
        dump(out/'exit.json',{'returncode':p.returncode,'heartbeat_count':len(sent)})
    from audit import analyze
    result=analyze(out,runtime,HERE)
    dump(out/'result.json',result)
    if not result['hard_pass']:raise RuntimeError('hard gate failure: '+repr(result['failures']))
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--runtime',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path);ap.add_argument('--plan',required=True,type=Path)
    ap.add_argument('--index',type=int,required=True);a=ap.parse_args()
    plan=json.loads(a.plan.read_text());runtime=a.runtime.resolve()
    for n,h in plan['source_sha256'].items():
        if sha(HERE/n)!=h:raise RuntimeError('frozen source mismatch '+n)
    fixture=runtime/'research/doom/fixtures/map01-threat-contact-v2'
    for n,h in plan['fixture_sha256'].items():
        if sha(fixture/n)!=h:raise RuntimeError('frozen fixture mismatch '+n)
    print(json.dumps(run_case(runtime,a.out.resolve(),plan['cases'][a.index]),sort_keys=True),flush=True)
if __name__=='__main__':main()
