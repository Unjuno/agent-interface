"""Post-controller audit of actual assistant replacement of visible draft text."""
import hashlib,json,urllib.parse
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
HERE=Path(__file__).resolve().parent;root=HERE/'results/prefilled-self-use-01'
for name,h in json.loads((root/'sources.json').read_text()).items():assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h
events=[json.loads(line) for line in (root/'events.jsonl').read_text().splitlines()]
delivered=[json.loads(line) for line in (root/'delivered.jsonl').read_text().splitlines()]
client=json.loads((root/'outcome.json').read_text());result=client['result']
assert result['state']=='evaluated' and result['task_success'] is True
assert len(client['transcript'])==1 and 'command' not in client['transcript'][0]['request']
assert urllib.parse.parse_qs((root/'submitted.txt').read_text())==result['evidence']['actual']=={'value':['t991029']}
accepted=[r for r in events if r['event']=='accepted'];terminals=[r for r in events if r['event']=='terminal']
assert len(accepted)==len(terminals)==2
assert all(t['status']=='completed' and t['release']['verified'] for t in terminals)
assert accepted[-1]['admitted_request']==terminals[-1]['admitted_request']==result['evidence']['admitted_request']
assert not any(r['event'] in ('rejected','finalization_status') for r in events)
commands=[r['command'] for r in events if r['event']=='command']
submit,=[c for c in commands if c.get('id')=='replace_submit']
assert submit['steps']==[dict(op='chord',modifier='Control_L',key='a'),dict(op='text',text='t991029'),dict(op='key',key='Return')]
assert submit['valid_until_ns']==terminals[0]['terminal_ns']+30_000_000_000
assert accepted[-1]['accepted_ns']<submit['valid_until_ns']
assert all(r['producer']=='assistant' for r in events if r['event']=='decision_evidence')
batches=[json.loads((root/f'read-{name}.json').read_text()) for name in ('initial','form','accepted')]
batch=client['transcript'][0]['reply']
assert [r for b in batches for r in b['records']]+batch['records']==delivered[:batch['cursor']]
flushed={json.loads(line)['delivery_id'] for line in (root/'delivery-flush.jsonl').read_text().splitlines()}
assert result['evidence']['delivery_id'] in flushed
decoder=Decoder('live-control');count=0
for event in events:
    if event['event']!='observation':continue
    count+=1;frame=decoder.accept((root/f'{count:03d}.ait').read_bytes())
    with Image.open(root/Path(event['image']).name) as im:assert im.size==(frame.width,frame.height) and im.tobytes()==frame.pixels
observation=next(r for r in events if r['event']=='observation')
report=dict(actual=result['evidence']['actual'],exact_frames=count,programs=2,submit_commands=1,outcome_exchange_calls=1,status_queries=0,
    first_capture_to_client_return_ms=(client['client_returned_ns']-observation['capture_ns'])/1e6,
    form_socket_return_to_replace_admission_ms=(accepted[-1]['accepted_ns']-batches[1]['returned_ns'])/1e6,
    local_program_ms=[(t['terminal_ns']-a['accepted_ns'])/1e6 for a,t in zip(accepted,terminals)],
    client_wait_ms=(client['client_returned_ns']-client['client_started_ns'])/1e6,
    final_terminal_to_evaluation_emit_ms=(result['evidence']['emit_started_ns']-terminals[-1]['terminal_ns'])/1e6,
    limitation='actual assistant self-use of planned pre-existing draft fixture; no unanticipated recovery, matched A/B, model receipt timestamps, human reference or token measurement')
(HERE/'results/prefilled-self-use-audit.json').write_text(json.dumps(report,indent=2)+'\n')
(root/'client-fixture-sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),HERE/'prefilled_browser_entry.py',HERE/'prefilled_socket_entry.py',HERE/'outcome_client.py',HERE/'outcome_fallback_v2.py',HERE/'outcome_wait.py',HERE/'receipt_image.py',HERE/'event_socket_v11.py',HERE/'event_cursor_v5.py',HERE/'request_boundary_v2.py')},indent=2)+'\n')
print(json.dumps(report,indent=2))
