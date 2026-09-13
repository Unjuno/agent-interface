"""Live invalid-command cases followed by a valid task; no stale-line attribution."""
import hashlib,json,queue,subprocess,sys,threading,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;out=HERE/'results/rejection-correlation-02';out.mkdir(exist_ok=False);root=out/'runtime'
p=subprocess.Popen([sys.executable,'-u',str(HERE/'interactive_v24.py'),'--app','xterm','--seed','991024','--out',str(root),'--presentation','compact'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
messages=queue.Queue();seen=[];rows=[]
def read():
    for line in p.stdout:
        r=json.loads(line);seen.append(r);messages.put(r)
t=threading.Thread(target=read,daemon=True);t.start()
def send(command):p.stdin.write((command if isinstance(command,str) else json.dumps(command))+'\n');p.stdin.flush()
def until(kind):
    deadline=time.monotonic()+30
    while time.monotonic()<deadline:
        r=messages.get(timeout=max(.01,deadline-time.monotonic()))
        if r['event']==kind:return r
    raise TimeoutError(kind)
try:
    obs=until('observation');send(dict(op='clock'));clock=until('clock')
    base=dict(op='submit',id='invalid',expected_sequence=obs['sequence'],valid_until_ns=clock['runtime_ns']+15_000_000_000,
              decision_evidence=dict(delivery_id=obs['delivery_id'],observation_sequence=obs['sequence'],producer='scripted'),steps=[dict(op='key',key='Return')])
    old_base=dict(base)
    send(dict(base,id='advance',steps=[dict(op='settle',quiet_ms=100,timeout_ms=500)]));until('terminal')
    latest=next(r for r in reversed(seen) if r['event']=='observation')
    base.update(expected_sequence=latest['sequence'],decision_evidence=dict(delivery_id=latest['delivery_id'],observation_sequence=latest['sequence'],producer='scripted'))
    cases=[('stale',dict(old_base,id='stale')),('expired',dict(base,id='expired',valid_until_ns=1)),
           ('malformed_steps',dict(base,id='malformed_steps',steps=[dict(op='unsupported')])),('bad_json','{'),('non_object','[]')]
    for index,(name,command) in enumerate(cases,3):
        send(command);r=until('rejected')
        assert r['runtime_request_sequence']==index
        assert r['declared_action_id']==(name if isinstance(command,dict) else None)
        rows.append(dict(case=name,rejection=r))
    # Valid input after all failures demonstrates that parsing failures are contained.
    send(dict(op='clock'));fresh=until('clock')
    good=dict(base,id='valid',valid_until_ns=fresh['runtime_ns']+10_000_000_000,finish_after=True,
              steps=[dict(op='text',text='t991024'),dict(op='key',key='Return')])
    send(good);terminal=until('terminal');evaluation=until('independent_evaluation')
    assert terminal['status']=='completed' and terminal['release']['verified'] and evaluation['success']
    send(dict(op='finish'));p.wait(timeout=10);t.join(2);assert p.returncode==0
    assert (root/'submitted.txt').read_text()=='t991024'
    events=[json.loads(x) for x in (root/'events.jsonl').read_text().splitlines()]
    assert [r['id'] for r in events if r['event']=='accepted']==['advance','valid']
    commands={r['runtime_request_sequence']:r for r in events if r['event']=='command'}
    for row in rows:
        r=row['rejection'];q=r['runtime_request_sequence']
        if row['case']=='bad_json':assert q not in commands
        else:assert commands[q]['declared_action_id']==r['declared_action_id']
    (out/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps([dict(case=r['case'],sequence=r['rejection']['runtime_request_sequence'],action=r['rejection']['declared_action_id'],reason=r['rejection']['reason']) for r in rows],indent=2))
finally:
    if p.poll() is None:
        send(dict(op='finish'));p.wait(timeout=15)
    (out/'stderr.txt').write_text(p.stderr.read())
    (out/'sources.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (Path(__file__),HERE/'interactive_v24.py',HERE/'request_correlation.py')},indent=2)+'\n')
