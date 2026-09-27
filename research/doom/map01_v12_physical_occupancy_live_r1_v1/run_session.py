from __future__ import annotations
import json,os,queue,subprocess,sys,threading,time
from pathlib import Path
HERE=Path(__file__).resolve().parent

def run_one(source,v12,out,seed,program_id):
    source=Path(source).resolve();v12=Path(v12).resolve();out=Path(out);out.mkdir(parents=True,exist_ok=False);runtime=out/'runtime'
    env=dict(os.environ);env['MAP01_SOURCE_ROOT']=str(source);env['MAP01_V12_ROOT']=str(v12)
    cmd=[sys.executable,str(HERE/'session_entry.py'),'--out',str(runtime),'--seed',str(seed),'--timeout-seconds','60','--skill','1','--load-fixture-manifest',str(source/'research/doom/fixtures/map01-threat-contact-v2/fixture.json')]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1,env=env)
    q=queue.Queue();seen=[];latest=None
    def reader():
        try:
            for line in p.stdout:
                try:q.put(json.loads(line))
                except json.JSONDecodeError:q.put({'event':'nonjson_stdout','line':line.rstrip()})
        finally:q.put(None)
    t=threading.Thread(target=reader,daemon=True);t.start()
    def wait(pred,timeout=35):
        nonlocal latest
        end=time.monotonic()+timeout
        while True:
            remain=end-time.monotonic()
            if remain<=0:raise TimeoutError('event timeout')
            row=q.get(timeout=remain)
            if row is None:raise RuntimeError('stdout closed: '+p.stderr.read())
            seen.append(row)
            if row.get('event')=='observation':latest=row
            if pred(row):return row
    def send(row):p.stdin.write(json.dumps(row)+'\n');p.stdin.flush()
    failure=None
    try:
        wait(lambda r:r.get('event')=='ready');wait(lambda r:r.get('event')=='observation' and r.get('id')=='initial')
        send({'op':'clock'});clock=wait(lambda r:r.get('event')=='clock')
        send({'op':'submit','id':program_id,'expected_sequence':latest['sequence'],'valid_until_ns':clock['runtime_ns']+5_000_000_000,'steps':[{'op':'hold','keys':['a','d'],'duration_ms':250},{'op':'observe'}]})
        terminal=wait(lambda r:r.get('event')=='terminal' and r.get('id')==program_id)
        if terminal.get('status')!='completed':raise RuntimeError('program not completed: '+repr(terminal))
        time.sleep(.12);send({'op':'finish'});wait(lambda r:r.get('event')=='post_control_score');p.stdin.close();rc=p.wait(timeout=15)
        if rc:raise RuntimeError('session rc='+str(rc)+' stderr='+p.stderr.read())
    except BaseException as exc:
        failure=repr(exc);raise
    finally:
        if p.poll() is None:p.kill();p.wait()
        t.join(timeout=2)
        (out/'controller_events.json').write_text(json.dumps(seen,indent=2)+'\n')
        (out/'launch.json').write_text(json.dumps({'cmd':cmd,'seed':seed,'program_id':program_id,'failure':failure},indent=2)+'\n')
    return runtime
