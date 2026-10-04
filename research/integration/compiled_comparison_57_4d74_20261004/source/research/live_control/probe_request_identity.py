"""Concurrent same-action rejection attempts joined by transport request identity."""
import concurrent.futures,hashlib,json,socket,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;out=HERE/'results/request-identity-01';out.mkdir(exist_ok=False);root=out/'runtime';responses=[]
p=subprocess.Popen([sys.executable,'-u',str(HERE/'event_socket_v8.py'),'serve','--','--app','xterm','--seed','991024','--out',str(root),'--presentation','compact'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
address=json.loads(p.stdout.readline())['socket']
def request(after,events,command=None,identifier=None,scoped=False):
    r=dict(after=after,events=events,timeout=5)
    if command is not None:r.update(command=command,request_id=identifier)
    if scoped:r['read_request_id']=identifier
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
        s.settimeout(8);s.connect(address);s.sendall((json.dumps(r)+'\n').encode())
        with s.makefile('rb') as f:reply=json.loads(f.readline())
    responses.append(dict(request=r,reply=reply));return reply
try:
    initial=request(0,['observation']);deadline=time.monotonic()+20
    while initial['status']=='timeout' and p.poll() is None and time.monotonic()<deadline:initial=request(initial['cursor'],['observation'])
    assert initial['status']=='boundary';obs=initial['records'][-1]
    clock=request(initial['cursor'],['clock'],dict(op='clock'),'clock');now=clock['records'][-1]['runtime_ns']
    base=dict(op='submit',id='same-action',expected_sequence=obs['sequence'],valid_until_ns=now+10_000_000_000,
              decision_evidence=dict(delivery_id=obs['delivery_id'],observation_sequence=obs['sequence'],producer='scripted'),steps=[dict(op='key',key='Return')])
    attempts={'expired-attempt':dict(base,valid_until_ns=1),'invalid-attempt':dict(base,steps=[dict(op='unsupported')])}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        jobs={name:pool.submit(request,clock['cursor'],['rejected'],command,name,True) for name,command in attempts.items()}
        replies={name:job.result() for name,job in jobs.items()}
    sequences=[]
    for name,reply in replies.items():
        assert reply['status']=='boundary',reply
        rejected=reply['records'][-1]
        assert rejected['event']=='rejected' and rejected['transport_request_id']==name and rejected['declared_action_id']=='same-action'
        sequences.append(rejected['runtime_request_sequence'])
    assert len(set(sequences))==2
    replay=request(clock['cursor'],['rejected'],attempts['expired-attempt'],'expired-attempt',True)
    assert replay['command_receipt']['replayed'] and replay['records'][-1]==replies['expired-attempt']['records'][-1]
    conflict=request(clock['cursor'],['rejected'],dict(base,valid_until_ns=2),'expired-attempt',True)
    assert conflict['status']=='error' and 'conflict' in conflict['message']
    reserved=request(clock['cursor'],['clock'],dict(op='clock',transport_request_id='forged'),'reserved')
    assert reserved['status']=='error' and 'reserved' in reserved['message']
    after=max(r['cursor'] for r in replies.values())
    clock=request(after,['clock'],dict(op='clock'),'fresh');now=clock['records'][-1]['runtime_ns']
    good=dict(base,id='valid',finish_after=True,valid_until_ns=now+10_000_000_000,steps=[dict(op='text',text='t991024'),dict(op='key',key='Return')])
    final=request(clock['cursor'],['independent_evaluation'],good,'valid');assert final['records'][-1]['success']
    request(final['cursor'],['command'],dict(op='finish'),'finish');p.wait(timeout=10);assert p.returncode==0
    assert (root/'submitted.txt').read_text()=='t991024'
    events=[json.loads(x) for x in (root/'events.jsonl').read_text().splitlines()]
    commands=[r for r in events if r['event']=='command']
    for name in attempts:assert sum(r['transport_request_id']==name for r in commands)==1
    assert not any(r['transport_request_id']=='reserved' for r in commands)
    for reply in replies.values():
        rejected=reply['records'][-1];parsed=next(r for r in commands if r['runtime_request_sequence']==rejected['runtime_request_sequence'])
        assert parsed['transport_request_id']==rejected['transport_request_id']
    summary=dict(rejections={name:dict(sequence=r['records'][-1]['runtime_request_sequence'],reason=r['records'][-1]['reason']) for name,r in replies.items()},
                 same_action_distinct_requests=True,replay_no_resend=True,conflict_and_reserved_rejected=True,subsequent_saved_task=True)
    (out/'results.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
finally:
    if p.poll() is None:
        request(0,['command'],dict(op='finish'),'cleanup');p.wait(timeout=15)
    (out/'responses.json').write_text(json.dumps(responses,indent=2)+'\n');(out/'stderr.txt').write_text(p.stderr.read())
    files=[Path(__file__),HERE/'event_socket_v8.py',HERE/'event_cursor_v3.py',HERE/'request_correlation_v2.py',HERE/'interactive_v25.py']
    (out/'sources.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in files},indent=2)+'\n')
