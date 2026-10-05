from pathlib import Path
import subprocess,sys,json,threading,queue,time,os
out=Path('/out')
results=[]
for index,arm in enumerate(['coast']):
    cell=out/f'{index:02d}-{arm}';cell.mkdir(exist_ok=False)
    q=queue.Queue();rows=[]
    stderr=(cell/'stderr.txt').open('wb')
    env=dict(os.environ,ACTION_SAMPLE_PATH=str(cell/'scorer-last-action.jsonl'))
    child=subprocess.Popen([sys.executable,'/study/sample_pair_entry_03.py','--out',str(cell/'runtime'),'--seed','40126','--skill','1','--timeout-seconds','60','--load-fixture-manifest','/study/fixture-input/fixture.json'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr,text=True,env=env)
    def reader():
        with (cell/'events.jsonl').open('w') as raw:
            for line in child.stdout:
                raw.write(line);raw.flush();row=json.loads(line);rows.append(row);q.put(row)
    t=threading.Thread(target=reader,daemon=True);t.start()
    def wait(event,identifier=None,timeout=15):
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            try:r=q.get(timeout=.1)
            except queue.Empty:
                if child.poll() is not None:raise RuntimeError('child exited before '+event)
                continue
            if r.get('event')==event and (identifier is None or r.get('id')==identifier):return r
            if r.get('event')=='rejected':raise RuntimeError(r)
        raise TimeoutError(event)
    def send(command):child.stdin.write(json.dumps(command)+'\n');child.stdin.flush()
    rescue=False
    try:
        wait('ready');obs=wait('observation')
        send({'op':'clock'});clock=wait('clock')
        steps=[{'op':'coast','duration_ms':5000,'sample_ms':50}] if arm=='coast' else sum(([{'op':'hold','keys':['d'],'duration_ms':50},{'op':'coast','duration_ms':70,'sample_ms':50}] for _ in range(5)),[])
        send({'op':'submit','id':'window','expected_sequence':obs['sequence'],'valid_until_ns':clock['runtime_ns']+5_000_000_000,'steps':steps})
        accepted=wait('accepted','window');terminal=wait('terminal','window')
        assert terminal['status'] in ('completed','expired'),terminal
        send({'op':'finish'});score=wait('post_control_score');code=child.wait(timeout=5);t.join(timeout=3)
        result={'window_start_ns':clock['runtime_ns'],'window_end_ns':clock['runtime_ns']+5_000_000_000,'arm':arm,'accepted':accepted,'terminal':terminal,'score':score,'child_exit':code,'reader_alive':t.is_alive(),'scope':'absolute clock response runtime_ns through +5000ms; lease deadline equals scoring window end; no model or useful efficacy claim'}
        (cell/'RESULT.json').write_text(json.dumps(result,indent=2));results.append(result)
        assert code==0 and not t.is_alive()
    finally:
        if child.poll() is None:rescue=True;child.kill();child.wait(timeout=3)
        t.join(timeout=3);stderr.close()
        (cell/'FINAL.json').write_text(json.dumps({'child_exit':child.poll(),'external_rescue':rescue,'reader_alive':t.is_alive()}))
(out/'RESULTS.json').write_text(json.dumps(results,indent=2))
