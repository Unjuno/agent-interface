"""Audit actual assistant CLI use of an explicit conditional completion policy."""
import hashlib,json
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
from effect_checkpoint import sample
HERE=Path(__file__).resolve().parent;root=HERE/'results/prepared-checkpoint-self-use-01'
read=lambda name:json.loads((root/name).read_text())
entry=read('enter/report.json');confirm=read('confirm/report.json');initial=read('read-initial.json')
clock=read('timing-clock.json')
assert entry['clock']==confirm['clock']==entry['program']['clock']==confirm['program']['clock']==clock
assert entry['state']=='needs_decision' and entry['task_success'] is None and not entry['policy']['finish_attempted']
assert confirm['state']=='evaluated' and confirm['task_success'] is True and confirm['policy']['finish_attempted']
assert (root/'enter/continuation-batch.json').exists() and not (root/'confirm/continuation-batch.json').exists()
records=list(initial['records']);samples=[]
for name,report in (('enter',entry),('confirm',confirm)):
    records+=report['program']['records']
    assert read(f'{name}/program/request.json')['command']['decision_evidence']['producer']=='assistant'
    for i,item in enumerate(report['policy']['exchanges'],1):
        assert read(f'{name}/policy-{i}-request.json')==item['request']
        assert read(f'{name}/policy-{i}-reply.json')==item['reply']
        records+=item['reply']['records']
    evidence=report['policy']['exchanges'][0]['reply']['records'][-1]['evidence']
    path=Path(evidence['archive_path']);assert not Path(evidence['archive_source_path']).exists()
    assert path.is_relative_to(root/'checkpoint-artifacts')
    assert hashlib.sha256(path.read_bytes()).hexdigest()==evidence['artifact_sha256']
    replay=sample(path,read('contract.json'));assert replay['status']==evidence['status'] and replay['actual']==evidence['actual']
    samples.append(evidence['status'])
assert samples==['UNKNOWN','VERIFIED']
score=confirm['policy']['evaluation'];assert score['actual']==[612,129]
assert score['evaluation_request']['transport_request_id']==confirm['policy']['exchanges'][-1]['request']['request_id']
assert hashlib.sha256((root/'sheet.xlsx').read_bytes()).hexdigest()==confirm['policy']['exchanges'][0]['reply']['records'][-1]['evidence']['artifact_sha256']
events=[json.loads(s) for s in (root/'events.jsonl').read_text().splitlines()]
delivered=[json.loads(s) for s in (root/'delivered.jsonl').read_text().splitlines()]
assert records==delivered and len(records)==27
assert not any(r['event']=='rejected' for r in events)
accepted=[r for r in events if r['event']=='accepted'];terminals=[r for r in events if r['event']=='terminal']
assert len(accepted)==len(terminals)==2
assert all(t['status']=='completed' and t['release']['verified'] and a['admitted_request']==t['admitted_request'] for a,t in zip(accepted,terminals))
decoder=Decoder('live-control');frames=0
for event in events:
    if event['event']!='observation':continue
    frames+=1;frame=decoder.accept((root/f'{frames:03d}.ait').read_bytes())
    with Image.open(root/Path(event['image']).name) as im:assert im.size==(frame.width,frame.height) and im.tobytes()==frame.pixels
for name,h in read('sources.json').items():assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h
result=dict(actual_assistant=True,exact_frames=frames,task_success=True,programs=2,outer_cli_calls=2,socket_calls_including_initial=6,
    verified_reply_to_finish_start_ms=(confirm['calls'][1]['started_ns']-confirm['calls'][0]['returned_ns'])/1e6,
    modal_report_ready_to_confirm_main_ms=(confirm['started_ns']-entry['processing_finished_ns'])/1e6,
    initial_capture_to_final_reply_ms=(confirm['calls'][-1]['returned_ns']-initial['records'][1]['capture_ns'])/1e6,
    initial_capture_to_wrapper_processing_end_ms=(confirm['processing_finished_ns']-initial['records'][1]['capture_ns'])/1e6,
    archived_states_replayed=samples,scope='Known Calc modal; no model receipt, actual tokens or matched causal speedup; setup after initial capture included')
(root/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
files=[Path(__file__),HERE/'prepared_checkpoint.py',HERE/'prepared_exchange_v6.py',HERE/'checkpoint_finish.py',HERE/'effect_checkpoint_v2.py',HERE/'event_socket_v16.py',HERE/'request_boundary_v4.py']
(root/'client-sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2)+'\n')
print(json.dumps(result,indent=2))
