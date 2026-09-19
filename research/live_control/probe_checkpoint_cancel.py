"""Cancel a real held-input program while an artifact verifier remains gated."""
import hashlib,json,socket,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;out=HERE/'results/checkpoint-cancel-01';out.mkdir(exist_ok=False)
root=out/'runtime';gate=out/'release.gate';responses=[]
proc=subprocess.Popen([sys.executable,'-u',str(HERE/'gated_checkpoint_socket_entry.py'),str(gate),
    'serve','--','--app','chromium','--seed','991029','--out',str(root),'--presentation','compact'],
    stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
addresses=json.loads(proc.stdout.readline());address=addresses['socket']
def request(spec,cancel=False):
    started=time.perf_counter_ns()
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as c:
        c.settimeout(10);c.connect(addresses['cancel_socket'] if cancel else address)
        c.sendall((json.dumps(spec)+'\n').encode())
        with c.makefile('rb') as stream:reply=json.loads(stream.readline())
    responses.append(dict(request=spec,reply=reply,started_ns=started,finished_ns=time.perf_counter_ns(),cancel_lane=cancel))
    return reply
try:
    initial=request(dict(after=0,events=['clock'],timeout=5,command=dict(op='clock'),request_id='clock'))
    assert initial['status']=='boundary'
    obs=next(r for r in initial['records'] if r['event']=='observation');clock=initial['records'][-1]
    spec=dict(after=initial['cursor'],events=['effect_checkpoint'],timeout=0,
        command=dict(op='effect_checkpoint',contract=dict(kind='saved_form_value',expected='t991029')),
        request_id='blocked-query',read_request_id='blocked-query')
    pending=request(spec);assert pending['status']=='timeout'
    limit=time.monotonic()+5
    while not gate.with_suffix('.waiting').exists():
        assert proc.poll() is None and time.monotonic()<limit;time.sleep(.005)
    busy=request(dict(spec,after=pending['cursor'],timeout=1,request_id='busy-query',read_request_id='busy-query'))
    assert busy['status']=='boundary' and busy['records'][-1]['reason']=='verifier_busy'
    hold=dict(op='submit',id='held',expected_sequence=obs['sequence'],valid_until_ns=clock['runtime_ns']+10_000_000_000,
        decision_evidence=dict(delivery_id=obs['delivery_id'],observation_sequence=obs['sequence'],producer='scripted'),
        steps=[dict(op='hold',keys=['Right'],duration_ms=4000)])
    accepted=request(dict(after=busy['cursor'],events=['accepted'],timeout=3,command=hold,request_id='hold'))
    assert accepted['status']=='boundary'
    # Confirm executor entered the hold step, rather than cancelling an unstarted queued command.
    limit=time.monotonic()+3
    while True:
        raw=[json.loads(s) for s in (root/'events.jsonl').read_text().splitlines()]
        if any(r['event']=='step_started' and r.get('id')=='held' for r in raw):break
        assert time.monotonic()<limit;time.sleep(.005)
    time.sleep(.1)
    cancelled=request(dict(after=accepted['cursor'],events=['cancel_requested'],timeout=1,
        command=dict(op='cancel',id='held'),request_id='cancel'),cancel=True)
    assert cancelled['status']=='boundary' and cancelled['records'][-1]['matched'] is True
    terminal=request(dict(after=cancelled['cursor'],events=['terminal'],timeout=3))
    end=terminal['records'][-1];assert end['status']=='cancelled' and end['release']['verified']
    assert not gate.exists() and proc.poll() is None
    raw=[json.loads(s) for s in (root/'events.jsonl').read_text().splitlines()]
    assert not any(r['event']=='effect_checkpoint' and r.get('transport_request_id')=='blocked-query' for r in raw)
    released=time.perf_counter_ns();gate.write_text('release only after cancellation terminal received')
    late=request(dict(after=terminal['cursor'],events=['effect_checkpoint'],timeout=3,read_request_id='blocked-query'))
    assert late['status']=='boundary' and late['records'][-1]['evidence']['status']=='UNKNOWN'
    assert late['records'][-1]['task_success'] is None
    request(dict(after=late['cursor'],events=['command'],timeout=3,command=dict(op='finish'),request_id='finish'))
    proc.wait(timeout=10);assert proc.returncode==0
    owners=json.loads((root/'owner-events.json').read_text())
    assert any(r['reason']=='cancelled' and r['verified'] and r['verified_ns']<released for r in owners)
    cancel_call=next(r for r in responses if r['cancel_lane'])
    result=dict(cancel_roundtrip_ms=(cancel_call['finished_ns']-cancel_call['started_ns'])/1e6,
        cancel_start_to_verified_terminal_ms=(end['terminal_ns']-cancel_call['started_ns'])/1e6,
        cancelled_before_gate_release=True,release_verified=True,busy_query_unknown=True,
        late_query_unknown=True,scope='scripted Chromium hold with sleeping verifier gate; no CPU/GIL, blocked stdout or hard deadline claim')
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
finally:
    gate.touch(exist_ok=True)
    if proc.poll() is None:
        request(dict(after=0,events=['command'],timeout=0,command=dict(op='finish'),request_id='cleanup'))
        proc.wait(timeout=15)
    (out/'responses.json').write_text(json.dumps(responses,indent=2)+'\n');(out/'stderr.txt').write_text(proc.stderr.read())
    files=[Path(__file__),HERE/'gated_checkpoint_entry.py',HERE/'gated_checkpoint_socket_entry.py',HERE/'effect_checkpoint.py',HERE/'interactive_v29.py',HERE/'event_socket_v14.py']
    (out/'sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2)+'\n')
