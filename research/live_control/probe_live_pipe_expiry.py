"""Actual runtime owner expiry while stdin is paused and a write is partial."""
import fcntl,hashlib,json,queue,subprocess,sys,threading,time
from pathlib import Path
from bounded_pipe_writer import BoundedPipeWriter,WriteUncertain
HERE=Path(__file__).resolve().parent;out=HERE/'results/live-pipe-expiry-01';out.mkdir(exist_ok=False)
root=out/'runtime';marker=out/'pause.txt';seen=[];messages=queue.Queue()
p=subprocess.Popen([sys.executable,'-u',str(HERE/'stdin_pause_entry.py'),str(marker),'--app','xterm','--seed','991024','--out',str(root),'--presentation','compact'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)
fcntl.fcntl(p.stdin.fileno(),fcntl.F_SETPIPE_SZ,4096);writer=BoundedPipeWriter(p.stdin.fileno())
def read():
    for line in p.stdout:
        r=json.loads(line);seen.append(r);messages.put(r)
t=threading.Thread(target=read,daemon=True);t.start()
def until(kind):
    deadline=time.monotonic()+30
    while time.monotonic()<deadline:
        r=messages.get(timeout=max(.01,deadline-time.monotonic()))
        if r['event']==kind:return r
    raise TimeoutError(kind)
try:
    obs=until('observation');writer(json.dumps(dict(op='clock'))+'\n');clock=until('clock')
    deadline=clock['runtime_ns']+800_000_000
    command=dict(op='submit',id='hold',expected_sequence=obs['sequence'],valid_until_ns=deadline,
                 decision_evidence=dict(delivery_id=obs['delivery_id'],observation_sequence=obs['sequence'],producer='scripted'),
                 steps=[dict(op='hold',keys=['Right'],duration_ms=4000)])
    writer(json.dumps(command)+'\n');until('accepted')
    stop=time.monotonic()+1
    while not marker.exists() and time.monotonic()<stop:time.sleep(.005)
    assert marker.exists()
    try:writer(json.dumps(dict(op='clock',padding='x'*8000))+'\n')
    except WriteUncertain as exc:assert 0<exc.sent<exc.total
    else:raise AssertionError('expected partial write')
    p.stdin.close();p.wait(timeout=10);t.join(2);assert p.returncode==0
    events=[json.loads(x) for x in (root/'events.jsonl').read_text().splitlines()]
    admissions=[e for e in events if e['event']=='input_admission'];assert admissions
    terminal=next(e for e in events if e['event']=='terminal');release=terminal['release'];assert release['verified']
    paused_ns=int(marker.read_text());assert admissions[0]['input_ack_ns']<release['verified_ns']<paused_ns+2_000_000_000
    assert sum(e['event']=='clock' for e in events)==1
    assert any(e['event']=='rejected' for e in events),'partial EOF record should be rejected'
    report=dict(terminal=terminal['status'],verified_release=True,release_during_stdin_pause=True,
                release_minus_lease_deadline_ms=(release['verified_ns']-deadline)/1e6,
                write=writer.records[-1],runtime_exit_code=p.returncode,partial_command_not_accepted=True)
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
finally:
    if p.poll() is None:
        if not p.stdin.closed:p.stdin.close()
        p.wait(timeout=10)
    (out/'stderr.txt').write_bytes(p.stderr.read())
    (out/'sources.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (Path(__file__),HERE/'stdin_pause_entry.py',HERE/'bounded_pipe_writer.py')},indent=2)+'\n')
