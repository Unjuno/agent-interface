"""Frozen-shape no-model/no-retry MAP01 v13 measurement integration probe."""
import argparse,json,queue,subprocess,sys,threading,time
from pathlib import Path
from audit_map01_measurement_integration_v1 import audit
HERE=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--seed',type=int,default=990613);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False);runtime=a.out/'runtime'
    p=subprocess.Popen([sys.executable,str(HERE/'session_map01_v13.py'),'--out',str(runtime),'--seed',str(a.seed),'--timeout-seconds','60','--skill','1'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    q=queue.Queue();seen=[];latest=None
    def reader():
        try:
            for line in p.stdout:q.put(json.loads(line))
        finally:q.put(None)
    t=threading.Thread(target=reader,daemon=True);t.start()
    def wait(pred,timeout=25):
        nonlocal latest
        end=time.monotonic()+timeout
        while True:
            remain=end-time.monotonic()
            if remain<=0:raise TimeoutError('probe event timeout')
            try:row=q.get(timeout=remain)
            except queue.Empty:raise TimeoutError('probe event timeout')
            if row is None:raise RuntimeError('session stdout closed; stderr='+p.stderr.read())
            seen.append(row)
            if row.get('event')=='observation':latest=row
            if pred(row):return row
    def send(row):p.stdin.write(json.dumps(row)+'\n');p.stdin.flush()
    try:
        wait(lambda r:r.get('event')=='ready');wait(lambda r:r.get('event')=='observation' and r.get('id')=='initial')
        send({'op':'clock'});clock=wait(lambda r:r.get('event')=='clock')
        send({'op':'submit','id':'telemetry-normal-hold','expected_sequence':latest['sequence'],'valid_until_ns':clock['runtime_ns']+5_000_000_000,'steps':[{'op':'hold','keys':['a','d'],'duration_ms':250},{'op':'observe'}]})
        terminal=wait(lambda r:r.get('event')=='terminal' and r.get('id')=='telemetry-normal-hold')
        if terminal.get('status')!='completed':raise RuntimeError('normal telemetry hold did not complete: '+repr(terminal))
        time.sleep(.12);send({'op':'finish'});wait(lambda r:r.get('event')=='post_control_score');p.stdin.close();rc=p.wait(timeout=10)
        if rc:raise RuntimeError('session failed rc='+str(rc)+' stderr='+p.stderr.read())
    finally:
        if p.poll() is None:p.kill();p.wait()
    t.join(timeout=2);(a.out/'controller-events.json').write_text(json.dumps(seen,indent=2)+'\n',encoding='utf-8')
    result=audit(runtime,HERE.parent);(a.out/'audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    if not result['pass']:raise SystemExit(1)
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
