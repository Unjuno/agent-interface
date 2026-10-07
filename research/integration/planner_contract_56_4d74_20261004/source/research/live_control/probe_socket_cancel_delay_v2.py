"""Live serial observation wait blocks a later cancel; disconnect retry evidence."""
import hashlib,json,socket,subprocess,sys,threading,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;out=HERE/'results/socket-cancel-delay-02';out.mkdir(exist_ok=False)
root=out/'runtime'
p=subprocess.Popen([sys.executable,'-u',str(HERE/'event_socket_v3.py'),'serve','--','--app','xterm','--seed','991024','--out',str(root),'--presentation','compact'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
address=json.loads(p.stdout.readline())['socket'];responses=[]
def request(after,events,timeout=5,command=None,identifier=None,disconnect=False):
    r=dict(after=after,events=events,timeout=timeout)
    if command is not None:r.update(command=command,request_id=identifier)
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
        s.settimeout(15);s.connect(address);started=time.perf_counter_ns();s.sendall((json.dumps(r)+'\n').encode())
        if disconnect:return dict(sent_ns=started,request=r)
        with s.makefile('rb') as f:reply=json.loads(f.readline())
    record=dict(request=r,started_ns=started,finished_ns=time.perf_counter_ns(),reply=reply);responses.append(record);return reply
try:
    initial=request(0,['observation']);obs=initial['records'][-1]
    clock=request(initial['cursor'],['clock'],command=dict(op='clock'),identifier='clock');now=clock['records'][-1]['runtime_ns']
    hold=dict(op='submit',id='hold',expected_sequence=obs['sequence'],valid_until_ns=now+8_000_000_000,
              decision_evidence=dict(delivery_id=obs['delivery_id'],observation_sequence=obs['sequence'],producer='scripted'),
              steps=[dict(op='hold',keys=['Right'],duration_ms=4000)])
    accepted=request(clock['cursor'],['accepted','rejected'],command=hold,identifier='hold')
    assert accepted['records'][-1]['event']=='accepted',accepted
    # A clock write proves the serial handler entered this long read before cancel.
    waiting=[]
    def blocked_read():waiting.append(request(accepted['cursor'],['never-emitted'],timeout=2,command=dict(op='clock'),identifier='blocker'))
    t=threading.Thread(target=blocked_read);t.start()
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        events=[json.loads(x) for x in (root/'events.jsonl').read_text().splitlines()]
        if sum(e['event']=='clock' for e in events)>=2:break
        time.sleep(.01)
    else:raise AssertionError('blocker not confirmed active')
    cancel=request(accepted['cursor'],['cancel_requested'],command=dict(op='cancel',id='hold'),identifier='cancel')
    t.join(5);assert not t.is_alive()
    terminal=request(cancel['cursor'],['terminal']);end=terminal['records'][-1]
    assert end['status']=='cancelled' and end['release']['verified'],end
    cancel_read=next(r for r in responses if r['request'].get('request_id')=='cancel')
    lag=(cancel_read['finished_ns']-cancel_read['started_ns'])/1e6
    assert lag<500,lag
    # Close without reading a clock response, then retry the identical request.
    dropped=request(terminal['cursor'],['clock'],command=dict(op='clock'),identifier='dropped',disconnect=True)
    retry=request(terminal['cursor'],['clock'],command=dict(op='clock'),identifier='dropped')
    assert retry['command_receipt']['replayed']
    done=request(retry['cursor'],['command'],command=dict(op='finish'),identifier='finish');p.wait(timeout=15);assert p.returncode==0
    events=[json.loads(x) for x in (root/'events.jsonl').read_text().splitlines()]
    assert sum(e['event']=='clock' for e in events)==3
    summary=dict(cancel_request_roundtrip_ms=lag,terminal=end['status'],release_verified=True,
                 long_read_status=waiting[0]['status'],disconnect_retry_replayed=True,total_runtime_clocks=3,
                 scope='scripted live xterm; bounded concurrent read permits cancel before timeout; no server restart')
    (out/'results.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
finally:
    if p.poll() is None:
        try:request(0,['command'],command=dict(op='finish'),identifier='cleanup');p.wait(timeout=15)
        except Exception:p.terminate();p.wait(timeout=5)
    (out/'responses.json').write_text(json.dumps(responses,indent=2)+'\n')
    (out/'stderr.txt').write_text(p.stderr.read())
    (out/'sources.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (Path(__file__),HERE/'event_socket_v3.py',HERE/'event_cursor.py',HERE/'command_once.py')},indent=2)+'\n')
