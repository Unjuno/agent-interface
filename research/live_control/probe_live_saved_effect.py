"""Scripted real Calc finalization with separate program and effect outcomes."""
import hashlib,json,queue,subprocess,sys,threading,time
from pathlib import Path
from openpyxl import load_workbook
HERE=Path(__file__).resolve().parent;out=HERE/'results/live-saved-effect-01';out.mkdir(exist_ok=False);results=[]
for case in ('save','unsaved'):
    root=out/case;messages=queue.Queue();seen=[]
    process=subprocess.Popen([sys.executable,'-u',str(HERE/'interactive_v22.py'),'--app','calc','--seed','991022','--out',str(root),'--presentation','compact'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
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
            if r['event']=='rejected':raise AssertionError(r)
            if r['event']==kind:return r
            if time.monotonic()>deadline:raise TimeoutError(kind)
    def submit(identifier,steps,final):
        obs=next(r for r in reversed(seen) if r['event']=='observation' or r['event']=='review')
        sequence=obs.get('sequence',obs.get('observation_sequence'))
        send(dict(op='clock'));clock=until('clock')
        send(dict(op='submit',id=identifier,finish_after=final,expected_sequence=sequence,valid_until_ns=clock['runtime_ns']+15_000_000_000,
                  decision_evidence=dict(delivery_id=obs['delivery_id'],observation_sequence=sequence,producer='scripted'),steps=steps))
        return until('terminal')
    try:
        until('observation')
        if case=='save':
            submit('enter_save',[dict(op='text',text='532'),dict(op='key',key='Return'),dict(op='text',text='590'),dict(op='key',key='Return'),dict(op='chord',modifier='Control_L',key='s'),dict(op='settle',quiet_ms=150,max_ms=1500)],False)
        terminal=submit('final',[dict(op='key',key='Return')],True)
        evaluation=until('independent_evaluation');effect=evaluation['effect']
        assert terminal['status']=='completed' and terminal['release']['verified']
        assert effect['status']==('VERIFIED' if case=='save' else 'CONTRADICTED')
        assert evaluation['success']==(case=='save')
        send(dict(op='finish'));process.wait(timeout=15);reader.join(2);assert process.returncode==0
        retained=json.loads((root/'finalization-status.json').read_text())
        assert retained['effect']==effect and retained['admission_closed'] and retained['output_flushed']
        wb=load_workbook(root/'sheet.xlsx');values=[wb.active['A1'].value,wb.active['A2'].value];wb.close()
        assert values==([532,590] if case=='save' else [None,None])
        assert hashlib.sha256((root/'sheet.xlsx').read_bytes()).hexdigest()==effect['artifact_sha256']
        results.append(dict(case=case,terminal=terminal['status'],effect=effect['status'],saved_values=values,
                            terminal_to_effect_finished_ms=(effect['finished_ns']-terminal['terminal_ns'])/1e6,
                            terminal_to_evaluation_emit_ms=(evaluation['emit_started_ns']-terminal['terminal_ns'])/1e6))
    finally:
        if process.poll() is None:
            try:send(dict(op='finish'));process.wait(timeout=15)
            except Exception:process.kill();process.wait()
        reader.join(2)
        (root/'supervisor-visible.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in seen))
        (root/'supervisor-stderr.txt').write_text(process.stderr.read())
(out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
(out/'probe-sources.json').write_text(json.dumps({Path(__file__).name:hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2)+'\n')
print(json.dumps(results,indent=2))
