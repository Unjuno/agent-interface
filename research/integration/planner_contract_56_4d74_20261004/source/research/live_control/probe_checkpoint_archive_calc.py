"""Real Calc snapshots replay after runtime cleanup deleted the source workbook."""
import hashlib,json,socket,subprocess,sys,time
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
from effect_checkpoint import sample
from timing_clock import describe
HERE=Path(__file__).resolve().parent;out=HERE/'results/checkpoint-archive-calc-01';out.mkdir(exist_ok=False)
root=out/'runtime';responses=[];clock=describe()
proc=subprocess.Popen([sys.executable,'-u',str(HERE/'event_socket_v15.py'),'serve','--','--app','calc',
    '--seed','991031','--out',str(root),'--presentation','compact'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
address=json.loads(proc.stdout.readline())['socket']
def request(spec):
    start=time.perf_counter_ns()
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as c:
        c.settimeout(10);c.connect(address);c.sendall((json.dumps(spec)+'\n').encode())
        with c.makefile('rb') as stream:reply=json.loads(stream.readline())
    responses.append(dict(request=spec,reply=reply,clock=clock,started_ns=start,returned_ns=time.perf_counter_ns()))
    return reply
def cli(source,name,steps):
    stepfile=out/f'{name}-steps.json';stepfile.write_text(json.dumps(steps)+'\n')
    r=subprocess.run([sys.executable,str(HERE/'prepared_exchange_v6.py'),address,str(source),str(root),name,str(stepfile),
        '--lease-ms','30000','--boundary','terminal','--producer','scripted','--out',str(out/name)],capture_output=True,text=True,timeout=10)
    (out/f'{name}-stderr.txt').write_text(r.stderr);assert r.returncode==0,r.stderr
    return json.loads(r.stdout)
try:
    initial=request(dict(after=0,events=['clock'],timeout=5,command=dict(op='clock'),request_id='clock'))
    assert initial['status']=='boundary'
    source=out/'initial.json';source.write_text(json.dumps(initial,indent=2)+'\n')
    entry=cli(source,'enter',json.loads((HERE/'results/prepared-calc-self-use-01/enter-steps.json').read_text()))
    contract=dict(kind='saved_cells',expected=dict(A1=612,A2=129))
    def query(after,identifier):
        reply=request(dict(after=after,events=['effect_checkpoint'],timeout=5,
            command=dict(op='effect_checkpoint',contract=contract),request_id=identifier,read_request_id=identifier))
        assert reply['status']=='boundary' and reply['records'][-1]['transport_request_id']==identifier
        return reply
    before=query(entry['cursor'],'before');assert before['records'][-1]['evidence']['status']=='UNKNOWN'
    source=out/'confirm-source.json';source.write_text(json.dumps(dict(before,records=entry['records']+before['records']),indent=2)+'\n')
    confirm=cli(source,'confirm',[dict(op='key',key='Return')])
    after=query(confirm['cursor'],'after');assert after['records'][-1]['evidence']['status']=='VERIFIED'
    finish=request(dict(after=after['cursor'],events=['independent_evaluation'],timeout=5,command=dict(op='finish'),request_id='finish'))
    assert finish['records'][-1]['success'] is True
    proc.wait(timeout=10);assert proc.returncode==0
    runtime_clock=json.loads((root/'timing-clock.json').read_text());assert runtime_clock==clock==entry['clock']==confirm['clock']
    samples=[]
    for reply in (before,after):
        evidence=reply['records'][-1]['evidence'];path=Path(evidence['archive_path'])
        assert not Path(evidence['archive_source_path']).exists()
        assert path.is_relative_to(root/'checkpoint-artifacts')
        assert hashlib.sha256(path.read_bytes()).hexdigest()==evidence['artifact_sha256']
        replay=sample(path,contract);assert replay['status']==evidence['status'] and replay['actual']==evidence['actual']
        assert reply['records'][-1]['task_success'] is None
        samples.append(dict(status=evidence['status'],actual=evidence['actual'],bytes=evidence['archive_bytes'],
            archive_and_parse_ms=(evidence['finished_ns']-evidence['archive_started_ns'])/1e6))
    events=[json.loads(s) for s in (root/'events.jsonl').read_text().splitlines()]
    delivered=[json.loads(s) for s in (root/'delivered.jsonl').read_text().splitlines()]
    assert initial['records']+entry['records']+before['records']+confirm['records']+after['records']+finish['records']==delivered[:finish['cursor']]
    assert len([r for r in events if r['event']=='accepted'])==2
    assert not any(r['event']=='rejected' for r in events)
    assert all(r['release']['verified'] for r in events if r['event']=='terminal')
    assert all(r['producer']=='scripted' for r in events if r['event']=='decision_evidence')
    for name,h in json.loads((root/'sources.json').read_text()).items():assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h
    decoder=Decoder('live-control');frames=0
    for event in events:
        if event['event']!='observation':continue
        frames+=1;frame=decoder.accept((root/f'{frames:03d}.ait').read_bytes())
        with Image.open(root/Path(event['image']).name) as im:assert im.size==(frame.width,frame.height) and im.tobytes()==frame.pixels
    result=dict(samples=samples,replayed_after_source_deleted=True,exact_frames=frames,final_success=True,
        scope='One scripted Calc run; archive/parse wall time, no baseline or model performance claim')
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
finally:
    if proc.poll() is None:
        request(dict(after=0,events=['command'],timeout=0,command=dict(op='finish'),request_id='cleanup'));proc.wait(timeout=15)
    (out/'responses.json').write_text(json.dumps(responses,indent=2)+'\n');(out/'stderr.txt').write_text(proc.stderr.read())
    files=[Path(__file__),HERE/'effect_checkpoint_v2.py',HERE/'effect_checkpoint.py',HERE/'saved_effect.py',HERE/'event_socket_v15.py',HERE/'prepared_exchange_v6.py',HERE/'timing_clock.py']
    (out/'sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2)+'\n')
