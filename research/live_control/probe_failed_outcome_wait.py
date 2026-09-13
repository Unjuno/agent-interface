"""Live evaluator exception: pending outcome then retained status, no resubmit."""
import hashlib,json,socket,subprocess,sys,time
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
from outcome_wait import wait_request,interpret
HERE=Path(__file__).resolve().parent
out=HERE/'results/failed-outcome-wait-01';out.mkdir(exist_ok=False)
root=out/'runtime';responses=[]
process=subprocess.Popen([sys.executable,'-u',str(HERE/'failed_socket_entry.py'),str(out/'fault.json'),'serve','--','--app','xterm','--seed','991027','--out',str(root),'--presentation','compact'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
address=json.loads(process.stdout.readline())['socket']
def request(spec):
    started=time.perf_counter_ns()
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
        connection.settimeout(8);connection.connect(address);connection.sendall((json.dumps(spec)+'\n').encode())
        with connection.makefile('rb') as stream:reply=json.loads(stream.readline())
    responses.append(dict(request=spec,reply=reply,started_ns=started,returned_ns=time.perf_counter_ns()))
    return reply
try:
    initial=request(dict(after=0,events=['observation'],timeout=5));limit=time.monotonic()+20
    while initial['status']=='timeout' and process.poll() is None and time.monotonic()<limit:
        initial=request(dict(after=initial['cursor'],events=['observation'],timeout=5))
    assert initial['status']=='boundary';obs=initial['records'][-1]
    clock=request(dict(after=initial['cursor'],events=['clock'],timeout=5,command=dict(op='clock'),request_id='clock'))
    command=dict(op='submit',id='submit',finish_after=True,expected_sequence=obs['sequence'],valid_until_ns=clock['records'][-1]['runtime_ns']+10_000_000_000,
        decision_evidence=dict(delivery_id=obs['delivery_id'],observation_sequence=obs['sequence'],producer='scripted'),
        steps=[dict(op='text',text='t991027'),dict(op='key',key='Return')])
    terminal=request(dict(after=clock['cursor'],events=['terminal'],timeout=5,command=command,request_id='submit',read_request_id='submit'))
    assert terminal['status']=='boundary' and terminal['records'][-1]['status']=='completed'
    pending_batch=request(wait_request('submit',terminal['cursor'],timeout=.2))
    pending=interpret(pending_batch,'submit');assert pending['state']=='pending' and pending['task_success'] is None
    # Current status event is unscoped. One session/final program and sequential
    # queries are deliberate restrictions of this test, not a generic correlation.
    status=request(dict(after=pending_batch['cursor'],events=['finalization_status'],timeout=5,command=dict(op='finalization_status'),request_id='status1'))
    record=status['records'][-1];assert record['event']=='finalization_status' and record['state']=='available'
    outcome=record['outcome']
    assert outcome['final_program']=='submit' and outcome['status']=='finalization_error'
    assert outcome['failure_stage']=='evaluate' and outcome['evaluation'] is None
    assert outcome['error']['type']=='RuntimeError' and outcome['admission_closed'] and not outcome['output_flushed']
    again=request(dict(after=status['cursor'],events=['finalization_status'],timeout=5,command=dict(op='finalization_status'),request_id='status2'))
    assert again['records'][-1]['outcome']==outcome
    request(dict(after=again['cursor'],events=['command'],timeout=5,command=dict(op='finish'),request_id='finish'))
    process.wait(timeout=10);assert process.returncode==0 and not Path(address).exists()
    events=[json.loads(line) for line in (root/'events.jsonl').read_text().splitlines()]
    delivered=[json.loads(line) for line in (root/'delivered.jsonl').read_text().splitlines()]
    assert not any(r['event'] in ('independent_evaluation','effect_evidence','rejected') for r in events)
    assert sum(r['event']=='command' and r['command'].get('id')=='submit' for r in events)==1
    assert sum(r['event']=='accepted' for r in events)==1
    assert terminal['records'][-1]['release']['verified']
    assert [r for response in responses for r in response['reply']['records']]==delivered[:responses[-1]['reply']['cursor']]
    assert json.loads((root/'finalization-status.json').read_text())==outcome
    assert (root/'submitted.txt').read_text()=='t991027'
    for name,h in json.loads((root/'sources.json').read_text()).items():assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h
    decoder=Decoder('live-control');count=0
    for event in events:
        if event['event']!='observation':continue
        count+=1;frame=decoder.accept((root/f'{count:03d}.ait').read_bytes())
        with Image.open(root/Path(event['image']).name) as im:assert im.size==(frame.width,frame.height) and im.tobytes()==frame.pixels
    report=dict(wait_state=pending['state'],task_success=None,retained_status=outcome['status'],failure_stage=outcome['failure_stage'],
        exact_frames=count,submit_commands=1,repeated_status_unchanged=True,
        terminal_to_error_retained_ms=(outcome['finished_ns']-terminal['records'][-1]['terminal_ns'])/1e6,
        terminal_to_status_socket_return_ms=(status['returned_ns']-terminal['records'][-1]['terminal_ns'])/1e6,
        limitation='scripted fault injection; status event unscoped, sequential single-final-program only; saved token audit is not a runtime evaluation')
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
finally:
    if process.poll() is None:
        request(dict(after=0,events=['command'],timeout=0,command=dict(op='finish'),request_id='cleanup'));process.wait(timeout=15)
    (out/'responses.json').write_text(json.dumps(responses,indent=2)+'\n');(out/'stderr.txt').write_text(process.stderr.read())
    sources=[Path(__file__),HERE/'failed_evaluation_entry.py',HERE/'failed_socket_entry.py',HERE/'outcome_wait.py',HERE/'event_socket_v10.py',HERE/'event_cursor_v4.py',HERE/'request_boundary.py',HERE/'finalization_v3.py']
    (out/'sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},indent=2)+'\n')
