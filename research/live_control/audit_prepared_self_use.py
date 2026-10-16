"""Actual assistant input through the bounded outcome CLI; post-run audit."""
import hashlib,json
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
from prepare_program import prepare
HERE=Path(__file__).resolve().parent;root=HERE/'results/prepared-self-use-01'
for name,h in json.loads((root/'sources.json').read_text()).items():assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h
events=[json.loads(line) for line in (root/'events.jsonl').read_text().splitlines()]
delivered=[json.loads(line) for line in (root/'delivered.jsonl').read_text().splitlines()]
client=json.loads((root/'outcome.json').read_text());result=client['result']
assert result['state']=='evaluated' and result['task_success'] is True
assert len(client['transcript'])==1 and 'command' not in client['transcript'][0]['request']
assert result['evidence']['actual']==(root/'submitted.txt').read_text()=='t991030'
accepted,=[r for r in events if r['event']=='accepted'];terminal,=[r for r in events if r['event']=='terminal']
assert terminal['status']=='completed' and terminal['release']['verified']
assert accepted['admitted_request']==terminal['admitted_request']==result['evidence']['admitted_request']
assert not any(r['event'] in ('rejected','finalization_status') for r in events)
assert sum(r['event']=='command' and r['command'].get('id')=='submit' for r in events)==1
assert all(r['producer']=='assistant' for r in events if r['event']=='decision_evidence')
initial=json.loads((root/'read-initial.json').read_text())
preparation=json.loads((root/'preparation.json').read_text())
command=json.loads((root/'submit.json').read_text())
assert prepare(initial,root,'submit',json.loads((root/'steps.json').read_text()),lease_ms=30000,finish_after=True)==preparation
assert preparation['command']==command
assert accepted['accepted_ns']<command['valid_until_ns']
admission=json.loads((root/'read-accepted.json').read_text())
batch=client['transcript'][0]['reply']
assert initial['records']+admission['records']+batch['records']==delivered[:batch['cursor']]
flushed={json.loads(line)['delivery_id'] for line in (root/'delivery-flush.jsonl').read_text().splitlines()}
assert result['evidence']['delivery_id'] in flushed
state=json.loads((root/'finalization-status.json').read_text())
assert state['admission_closed'] and state['output_flushed'] and state['evaluation']['success']
decoder=Decoder('live-control');count=0
for event in events:
    if event['event']!='observation':continue
    count+=1;frame=decoder.accept((root/f'{count:03d}.ait').read_bytes())
    with Image.open(root/Path(event['image']).name) as im:assert im.size==(frame.width,frame.height) and im.tobytes()==frame.pixels
observation=next(r for r in events if r['event']=='observation')
report=dict(actual='t991030',exact_frames=count,submit_commands=1,outcome_exchange_calls=1,status_queries=0,
    first_capture_to_client_return_ms=(client['client_returned_ns']-observation['capture_ns'])/1e6,
    initial_socket_return_to_admission_ms=(accepted['accepted_ns']-initial['returned_ns'])/1e6,
    local_program_ms=(terminal['terminal_ns']-accepted['accepted_ns'])/1e6,
    client_wait_ms=(client['client_returned_ns']-client['client_started_ns'])/1e6,
    final_terminal_to_evaluation_emit_ms=(result['evidence']['emit_started_ns']-terminal['terminal_ns'])/1e6,
    limitation='actual assistant self-use, simple familiar fixture; no A/B, fallback invocation, model receipt timestamps, human reference or token measurement')
(HERE/'results/prepared-self-use-audit.json').write_text(json.dumps(report,indent=2)+'\n')
(root/'client-sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),HERE/'outcome_client.py',HERE/'prepare_program.py',HERE/'outcome_fallback_v2.py',HERE/'outcome_wait.py',HERE/'receipt_image.py',HERE/'event_socket_v11.py',HERE/'event_cursor_v5.py',HERE/'request_boundary_v2.py')},indent=2)+'\n')
print(json.dumps(report,indent=2))
