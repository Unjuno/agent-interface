"""Integrated CLI returns early before releasing a real evaluator gate."""
import hashlib,json,socket,subprocess,sys,time
from pathlib import Path
from PIL import Image
from openpyxl import load_workbook
from session_v9 import Decoder
HERE=Path(__file__).resolve().parent;out=HERE/'results/live-drain-delay-02';out.mkdir(exist_ok=False)
root=out/'runtime';gate=out/'release.gate';responses=[]
process=subprocess.Popen([sys.executable,'-u',str(HERE/'gated_socket_entry_v2.py'),str(gate),'serve','--','--app','calc','--seed','991031','--out',str(root),'--presentation','compact'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
address=json.loads(process.stdout.readline())['socket']
def request(spec):
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
        connection.settimeout(8);connection.connect(address);connection.sendall((json.dumps(spec)+'\n').encode())
        with connection.makefile('rb') as stream:reply=json.loads(stream.readline())
    responses.append(dict(request=spec,reply=reply));return reply
def cli(source,name,boundary,steps):
    stepfile=out/f'{name}-steps.json';stepfile.write_text(json.dumps(steps))
    args=[sys.executable,str(HERE/'prepared_exchange_v4.py'),address,str(source),str(root),name,str(stepfile),
          '--lease-ms','30000','--boundary',boundary,'--producer','scripted','--out',str(out/name)]
    if boundary=='outcome':args+=['--drain-final']
    result=subprocess.run(args,capture_output=True,text=True,timeout=8)
    (out/f'{name}-stderr.txt').write_text(result.stderr)
    assert result.returncode==0,result.stderr
    return json.loads(result.stdout)
try:
    initial=request(dict(after=0,events=['observation'],timeout=5));limit=time.monotonic()+20
    collected=list(initial['records'])
    while initial['status']=='timeout' and process.poll() is None and time.monotonic()<limit:
        initial=request(dict(after=initial['cursor'],events=['observation'],timeout=5));collected+=initial['records']
    assert initial['status']=='boundary'
    clock=request(dict(after=initial['cursor'],events=['clock'],timeout=5,command=dict(op='clock'),request_id='clock'))
    # Preserve the received observation and newer clock in one evidence batch.
    source=dict(clock,records=collected+clock['records'])
    sourcefile=out/'initial.json';sourcefile.write_text(json.dumps(source,indent=2)+'\n')
    steps=json.loads((HERE/'results/prepared-calc-self-use-01/enter-steps.json').read_text())
    entry=cli(sourcefile,'entry','terminal',steps)
    assert entry['status']=='boundary' and entry['records'][-1]['status']=='completed'
    confirmation=cli(out/'entry/reply.json','confirm','outcome',[dict(op='key',key='Return')])
    assert confirmation['outcome']['state']=='effect_observed' and confirmation['outcome']['task_success'] is None
    assert confirmation['drain']['drain_state']=='pending' and confirmation['drain']['request']['timeout']==0
    assert confirmation['drain']['reply']['status']=='timeout'
    assert gate.with_suffix('.waiting').exists() and not gate.exists() and process.poll() is None
    assert not any(json.loads(line)['event']=='independent_evaluation' for line in (root/'events.jsonl').read_text().splitlines())
    released_ns=time.perf_counter_ns();gate.write_text('release after CLI returned early')
    final=request(confirmation['outcome']['continuation'])
    assert final['status']=='boundary' and final['records'][-1]['success'] is True
    score=final['records'][-1];early=confirmation['outcome']['evidence']
    assert score['effect']==early['effect'] and score['admitted_request']==early['admitted_request']
    request(dict(after=final['cursor'],events=['command'],timeout=5,command=dict(op='finish'),request_id='finish'))
    process.wait(timeout=10);assert process.returncode==0 and not Path(address).exists()
    events=[json.loads(line) for line in (root/'events.jsonl').read_text().splitlines()]
    assert all(r['producer']=='scripted' for r in events if r['event']=='decision_evidence')
    assert sum(r['event']=='accepted' for r in events)==2 and not any(r['event']=='rejected' for r in events)
    terminals=[r for r in events if r['event']=='terminal'];assert all(r['status']=='completed' and r['release']['verified'] for r in terminals)
    wb=load_workbook(root/'sheet.xlsx');assert [wb.active['A1'].value,wb.active['A2'].value]==[612,129];wb.close()
    assert hashlib.sha256((root/'sheet.xlsx').read_bytes()).hexdigest()==score['effect']['artifact_sha256']
    delivered=[json.loads(line) for line in (root/'delivered.jsonl').read_text().splitlines()]
    assert source['records']+entry['records']+confirmation['records']+final['records']==delivered[:final['cursor']]
    for name,h in json.loads((root/'sources.json').read_text()).items():assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h
    decoder=Decoder('live-control');count=0
    for event in events:
        if event['event']!='observation':continue
        count+=1;frame=decoder.accept((root/f'{count:03d}.ait').read_bytes())
        with Image.open(root/Path(event['image']).name) as im:assert im.size==(frame.width,frame.height) and im.tobytes()==frame.pixels
    summary=dict(early_return_before_gate_release=True,early_task_success=None,final_success=True,exact_frames=count,accepted_programs=2,
        drain_server_timeout=0,early_socket_return_to_processing_end_ms=(confirmation['processing_finished_ns']-confirmation['returned_ns'])/1e6,
        processing_end_to_gate_release_ms=(released_ns-confirmation['processing_finished_ns'])/1e6,
        limitation='scripted integrated CLI test, not model latency; no delayed-network or permanent-hang bound')
    (out/'results.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
finally:
    gate.touch(exist_ok=True)
    if process.poll() is None:
        request(dict(after=0,events=['command'],timeout=0,command=dict(op='finish'),request_id='cleanup'));process.wait(timeout=15)
    (out/'responses.json').write_text(json.dumps(responses,indent=2)+'\n');(out/'stderr.txt').write_text(process.stderr.read())
    files=[Path(__file__),HERE/'prepared_exchange_v4.py',HERE/'drain_final.py',HERE/'unix_json_deadline.py',HERE/'prepare_program.py',HERE/'outcome_wait.py',HERE/'gated_socket_entry_v2.py',HERE/'gated_evaluation_entry_v2.py',HERE/'event_socket_v11.py',HERE/'event_cursor_v5.py',HERE/'request_boundary_v2.py']
    (out/'sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2)+'\n')
