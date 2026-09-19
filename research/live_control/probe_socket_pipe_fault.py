"""End-to-end socket replies for pre-write rejection, partial write and poison."""
import hashlib,json,socket,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;out=HERE/'results/socket-pipe-fault-01';out.mkdir(exist_ok=False)
root=out/'runtime';marker=out/'pause.txt';responses=[]
p=subprocess.Popen([sys.executable,'-u',str(HERE/'socket_pipe_fault_entry.py'),str(marker),'serve','--','--app','xterm','--seed','991024','--out',str(root),'--presentation','compact'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
info=json.loads(p.stdout.readline())
def request(after,events,command=None,identifier=None):
    r=dict(after=after,events=events,timeout=1)
    if command is not None:r.update(command=command,request_id=identifier)
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
        s.settimeout(5);s.connect(info['socket']);started=time.perf_counter_ns()
        s.sendall((json.dumps(r,ensure_ascii=False)+'\n').encode())
        with s.makefile('rb') as f:reply=json.loads(f.readline())
    # Store request shape, not repeated padding strings.
    if command and 'padding' in command:r['command']=dict(command,padding_length=len(command['padding']));r['command'].pop('padding')
    responses.append(dict(request=r,reply=reply,started_ns=started,finished_ns=time.perf_counter_ns()));return reply
try:
    initial=request(0,['observation']);deadline=time.monotonic()+20
    while initial['status']=='timeout' and p.poll() is None and time.monotonic()<deadline:initial=request(initial['cursor'],['observation'])
    assert initial['status']=='boundary';obs=initial['records'][-1]
    bad=request(initial['cursor'],['clock'],dict(op='clock',padding='日'*3000),'oversize')
    assert bad['status']=='rejected_before_write' and bad['command_receipt']['sent']==0
    clock=request(initial['cursor'],['clock'],dict(op='clock'),'clock');now=clock['records'][-1]['runtime_ns']
    assert clock['command_receipt']['state']=='stdin_flushed'
    hold=dict(op='submit',id='hold',expected_sequence=obs['sequence'],valid_until_ns=now+800_000_000,
              decision_evidence=dict(delivery_id=obs['delivery_id'],observation_sequence=obs['sequence'],producer='scripted'),
              steps=[dict(op='hold',keys=['Right'],duration_ms=4000)])
    accepted=request(clock['cursor'],['accepted','rejected'],hold,'hold');assert accepted['records'][-1]['event']=='accepted'
    deadline=time.monotonic()+1
    while not marker.exists() and time.monotonic()<deadline:time.sleep(.005)
    assert marker.exists()
    partial_command=dict(op='clock',padding='x'*8000)
    partial=request(accepted['cursor'],['clock'],partial_command,'partial')
    assert partial['status']=='write_uncertain' and partial['command_receipt']['sent']==4096
    retry=request(accepted['cursor'],['clock'],partial_command,'partial');assert retry['command_receipt']['replayed']
    unusable=request(accepted['cursor'],['cancel_requested'],dict(op='cancel',id='hold'),'cancel')
    assert unusable['status']=='channel_unusable' and unusable['command_receipt']['sent']==0
    # Read existing evidence without attempting another write on the poisoned pipe.
    terminal=request(accepted['cursor'],['terminal']);assert terminal['records'][-1]['status']=='expired'
    p.wait(timeout=8);assert p.returncode==0
    events=[json.loads(x) for x in (root/'events.jsonl').read_text().splitlines()]
    assert sum(e['event']=='clock' for e in events)==1
    assert not any(e['event']=='command' and e['command'].get('op')=='cancel' for e in events)
    end=next(e for e in events if e['event']=='terminal');assert end['release']['verified']
    record=next(r for r in responses if r['reply'].get('status')=='write_uncertain')
    report=dict(prewrite_rejected_without_poison=True,partial_bytes=4096,partial_total=partial['command_receipt']['total'],
                partial_reply_ms=(record['finished_ns']-record['started_ns'])/1e6,
                retry_did_not_write=True,later_cancel_not_forwarded=True,terminal='expired',release_verified=True,runtime_exit=0)
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
finally:
    if p.poll() is None:p.wait(timeout=10)
    (out/'responses.json').write_text(json.dumps(responses,indent=2)+'\n');(out/'stderr.txt').write_text(p.stderr.read())
    paths=[Path(__file__),HERE/'socket_pipe_fault_entry.py',HERE/'stdin_pause_entry.py',HERE/'event_socket_v6.py',HERE/'command_once_v2.py',HERE/'bounded_pipe_writer_v2.py']
    (out/'sources.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in paths},indent=2)+'\n')
