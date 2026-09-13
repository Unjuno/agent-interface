"""Audit browser direct-final path with optional drain enabled but not attempted."""
import hashlib,json,urllib.parse
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
from prepare_program import prepare
HERE=Path(__file__).resolve().parent;root=HERE/'results/drain-browser-self-use-01'
for name,h in json.loads((root/'sources.json').read_text()).items():assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h
events=[json.loads(line) for line in (root/'events.jsonl').read_text().splitlines()]
delivered=[json.loads(line) for line in (root/'delivered.jsonl').read_text().splitlines()]
initial=json.loads((root/'read-initial.json').read_text());nav=json.loads((root/'navigate/report.json').read_text());submit=json.loads((root/'submit/report.json').read_text())
assert submit['drain']['attempted'] is False and submit['outcome']['task_success'] is True
assert not (root/'submit/drain-request.json').exists() and not (root/'submit/drain-reply.json').exists()
assert urllib.parse.parse_qs((root/'submitted.txt').read_text())==submit['outcome']['evidence']['actual']=={'value':['t991029']}
assert initial['records']+nav['records']+submit['records']==delivered[:22]
assert not any(r['event'] in ('rejected','effect_evidence','finalization_status') for r in events)
accepted=[r for r in events if r['event']=='accepted'];terminals=[r for r in events if r['event']=='terminal']
assert len(accepted)==len(terminals)==2 and all(t['status']=='completed' and t['release']['verified'] for t in terminals)
assert accepted[-1]['admitted_request']==terminals[-1]['admitted_request']==submit['outcome']['evidence']['admitted_request']
assert all(r['producer']=='assistant' for r in events if r['event']=='decision_evidence')
for name,batch,program,finished in (('navigate',initial,'navigate',False),('submit',json.loads((root/'navigate/reply.json').read_text()),'replace_submit',True)):
    prepared=json.loads((root/name/'preparation.json').read_text())
    assert prepared==prepare(batch,root,program,json.loads((root/f'{name}-steps.json').read_text()),lease_ms=30000,finish_after=finished)
    assert json.loads((root/name/'request.json').read_text())['command']==prepared['command']
decoder=Decoder('live-control');count=0
for event in events:
    if event['event']!='observation':continue
    count+=1;frame=decoder.accept((root/f'{count:03d}.ait').read_bytes())
    with Image.open(root/Path(event['image']).name) as im:assert im.size==(frame.width,frame.height) and im.tobytes()==frame.pixels
first=next(r for r in events if r['event']=='observation')
report=dict(actual={'value':['t991029']},exact_frames=count,programs=2,drain_attempted=False,socket_calls_before_cleanup=3,
    first_capture_to_processing_end_ms=(submit['processing_finished_ns']-first['capture_ns'])/1e6,
    form_socket_return_to_submission_admission_ms=(accepted[-1]['accepted_ns']-nav['returned_ns'])/1e6,
    local_program_ms=[(t['terminal_ns']-a['accepted_ns'])/1e6 for a,t in zip(accepted,terminals)],
    model_receipt_timestamps=None,limitation='actual assistant simple known draft fixture; no matched speedup or tokens measured')
(HERE/'results/drain-browser-self-use-audit.json').write_text(json.dumps(report,indent=2)+'\n')
(root/'client-fixture-sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),HERE/'prefilled_socket_entry.py',HERE/'prefilled_browser_entry.py',HERE/'prepared_exchange_v4.py',HERE/'prepare_program.py',HERE/'receipt_image.py',HERE/'outcome_wait.py',HERE/'drain_final.py',HERE/'unix_json_deadline.py',HERE/'event_socket_v11.py',HERE/'event_cursor_v5.py',HERE/'request_boundary_v2.py')},indent=2)+'\n')
print(json.dumps(report,indent=2))
