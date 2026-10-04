"""Drive real private-X11 text tasks; supervisor inspects finalization status."""
import hashlib,json,queue,subprocess,sys,threading,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;out=HERE/'results/live-finalization-faults-01';out.mkdir(exist_ok=False)
results=[]
for fault in ('write','flush','scorer'):
    root=out/fault
    messages=queue.Queue();seen=[]
    process=subprocess.Popen([sys.executable,'-u',str(HERE/'finalization_fault_entry.py'),fault,'--app','xterm','--seed','991024','--out',str(root),'--presentation','compact'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    def read():
        for line in process.stdout:
            try:r=json.loads(line)
            except ValueError:continue
            seen.append(r);messages.put(r)
    reader=threading.Thread(target=read,daemon=True);reader.start()
    def send(r):process.stdin.write(json.dumps(r)+'\n');process.stdin.flush()
    def until(kind):
        deadline=time.monotonic()+30
        while True:
            r=messages.get(timeout=max(.01,deadline-time.monotonic()))
            if r['event']==kind:return r
            if time.monotonic()>deadline:raise TimeoutError(kind)
    try:
        obs=until('observation');send(dict(op='clock'));clock=until('clock')
        send(dict(op='submit',id='final',finish_after=True,expected_sequence=obs['sequence'],valid_until_ns=clock['runtime_ns']+15_000_000_000,
                  decision_evidence=dict(delivery_id=obs['delivery_id'],observation_sequence=obs['sequence'],producer='scripted'),
                  steps=[dict(op='text',text='t991024'),dict(op='key',key='Return')]))
        terminal=until('terminal');assert terminal['status']=='completed' and terminal['release']['verified']
        deadline=time.monotonic()+10;status=None
        while time.monotonic()<deadline:
            try:status=json.loads((root/'finalization-status.json').read_text());break
            except (FileNotFoundError,json.JSONDecodeError):time.sleep(.01)
        assert status is not None and status['status']=='finalization_error'
        assert status['admission_closed'] and not status['output_flushed']
        assert status['failure_stage']==('evaluate' if fault=='scorer' else 'publish')
        if fault=='scorer':assert status['evaluation'] is None
        else:assert status['evaluation']['success'] is True
        send(dict(op='finish'));process.wait(timeout=10);reader.join(2);assert process.returncode==0
        assert (root/'submitted.txt').read_text()=='t991024'
        visible=[r for r in seen if r['event']=='independent_evaluation']
        assert len(visible)==(1 if fault=='flush' else 0)
        receipts=[json.loads(x) for x in (root/'delivery-flush.jsonl').read_text().splitlines()]
        if visible:assert visible[0]['delivery_id'] not in {r['delivery_id'] for r in receipts}
        (root/'supervisor-visible.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in seen))
        results.append(dict(fault=fault,stage=status['failure_stage'],visible_evaluations=len(visible),saved_task_correct=True,output_confirmed=False))
    finally:
        if process.poll() is None:
            try:send(dict(op='finish'));process.wait(timeout=10)
            except Exception:process.kill();process.wait()
(out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
(out/'probe-sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),HERE/'finalization_fault_entry.py')},indent=2)+'\n')
print(json.dumps(results,indent=2))
