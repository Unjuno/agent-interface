"""Audit actual GUI navigation and form submission, separate from input selection."""
import hashlib,json,urllib.parse
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
from receipt_image import select_image
HERE=Path(__file__).resolve().parent
root=HERE/'results/receipt-browser-self-use-01'
for name,h in json.loads((root/'sources.json').read_text()).items():
    assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h
events=[json.loads(line) for line in (root/'events.jsonl').read_text().splitlines()]
delivered=[json.loads(line) for line in (root/'delivered.jsonl').read_text().splitlines()]
batches=[json.loads((root/f'read-{name}.json').read_text()) for name in ('initial','form','final')]
assert [r for b in batches for r in b['records']]==delivered[:batches[-1]['cursor']]
assert len({r['delivery_id'] for b in batches for r in b['records']})==batches[-1]['cursor']
flushed={json.loads(line)['delivery_id'] for line in (root/'delivery-flush.jsonl').read_text().splitlines()}
evaluation,=[r for r in delivered if r['event']=='independent_evaluation']
assert evaluation['delivery_id'] in flushed and evaluation['success']
assert not any(r['event']=='effect_evidence' for r in delivered)
actual=urllib.parse.parse_qs((root/'submitted.txt').read_text())
assert actual==evaluation['actual']=={'value':['t991025']}
accepted=[r for r in events if r['event']=='accepted']
terminals=[r for r in events if r['event']=='terminal']
assert len(accepted)==len(terminals)==2
assert all(r['status']=='completed' and r['release']['verified'] for r in terminals)
assert not any(r['event']=='rejected' for r in events)
assert all(r['producer']=='assistant' for r in events if r['event']=='decision_evidence')
assert evaluation['admitted_request']==terminals[-1]['admitted_request']==accepted[-1]['admitted_request']
assert evaluation['admitted_request']['transport_request_id']=='submit'
state=json.loads((root/'finalization-status.json').read_text())
assert state['admission_closed'] and state['output_flushed'] and state['evaluation']['success']
commands=[r['command'] for r in events if r['event']=='command']
assert len([r for r in commands if r.get('id')=='submit_form'])==1
confirmation=next(r for r in commands if r.get('id')=='submit_form')
assert confirmation['valid_until_ns']==terminals[0]['terminal_ns']+30_000_000_000
assert accepted[-1]['accepted_ns']<confirmation['valid_until_ns']
decoder=Decoder('live-control');count=0
for event in events:
    if event['event']!='observation':continue
    count+=1;frame=decoder.accept((root/f'{count:03d}.ait').read_bytes())
    with Image.open(root/Path(event['image']).name) as im:
        assert im.size==(frame.width,frame.height) and im.tobytes()==frame.pixels
initial=next(r for r in events if r['event']=='observation')
report=dict(actual=actual,exact_frames=count,accepted_programs=len(accepted),rejections=0,
    clock_requests=sum(r['event']=='clock' for r in events),socket_calls_before_cleanup=len(batches),
    first_capture_to_evaluation_socket_return_ms=(batches[-1]['returned_ns']-initial['capture_ns'])/1e6,
    first_capture_to_evaluation_known_ms=(evaluation['known_ns']-initial['capture_ns'])/1e6,
    initial_socket_return_to_accept_ms=(accepted[0]['accepted_ns']-batches[0]['returned_ns'])/1e6,
    form_socket_return_to_accept_ms=(accepted[1]['accepted_ns']-batches[1]['returned_ns'])/1e6,
    final_terminal_to_evaluation_emit_ms=(evaluation['emit_started_ns']-terminals[-1]['terminal_ns'])/1e6,
    evaluation_emit_to_socket_return_ms=(batches[-1]['returned_ns']-evaluation['emit_started_ns'])/1e6,
    local_program_ms=[(t['terminal_ns']-a['accepted_ns'])/1e6 for a,t in zip(accepted,terminals)],
    selected_images={name:select_image(batch,root) for name,batch in zip(('initial','form','final'),batches)},
    early_effect_supported=False,model_receipt_timestamps=None,
    limitation='one simple local browser fixture, no matched A/B, human comparison, recovery trial or model token measurement')
(HERE/'results/receipt-browser-self-use-audit.json').write_text(json.dumps(report,indent=2)+'\n')
(root/'transport-sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),HERE/'receipt_image.py',HERE/'event_socket_v10.py',HERE/'event_cursor_v4.py',HERE/'request_boundary.py',HERE/'admitted_lineage.py')},indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='selected_images'},indent=2))
