"""Audit same-task actual self-use of combined preparation/send/wait CLI."""
import hashlib,json
from pathlib import Path
from PIL import Image
from session_v9 import Decoder
from prepare_program import prepare
HERE=Path(__file__).resolve().parent;root=HERE/'results/prepared-exchange-self-use-01'
for name,h in json.loads((root/'sources.json').read_text()).items():assert hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()==h
events=[json.loads(line) for line in (root/'events.jsonl').read_text().splitlines()]
delivered=[json.loads(line) for line in (root/'delivered.jsonl').read_text().splitlines()]
initial=json.loads((root/'read-initial.json').read_text())
exchange=root/'exchange';report=json.loads((exchange/'report.json').read_text())
reply=json.loads((exchange/'reply.json').read_text());request=json.loads((exchange/'request.json').read_text())
prepared=json.loads((exchange/'preparation.json').read_text())
assert prepare(initial,root,'submit',json.loads((root/'steps.json').read_text()),lease_ms=30000,finish_after=True)==prepared
assert request['command']==prepared['command']
assert request['read_request_id']==request['request_id']==report['request_id']
assert initial['records']+reply['records']==delivered[:reply['cursor']]
assert report['outcome']['task_success'] is True and report['outcome']['evidence']['actual']==(root/'submitted.txt').read_text()=='t991030'
accepted,=[r for r in events if r['event']=='accepted'];terminal,=[r for r in events if r['event']=='terminal']
assert terminal['status']=='completed' and terminal['release']['verified']
assert accepted['admitted_request']==terminal['admitted_request']==report['outcome']['evidence']['admitted_request']
assert accepted['accepted_ns']<request['command']['valid_until_ns']
assert not any(r['event'] in ('rejected','finalization_status') for r in events)
assert sum(r['event']=='command' and r['command'].get('id')=='submit' for r in events)==1
assert all(r['producer']=='assistant' for r in events if r['event']=='decision_evidence')
decoder=Decoder('live-control');count=0
for event in events:
    if event['event']!='observation':continue
    count+=1;frame=decoder.accept((root/f'{count:03d}.ait').read_bytes())
    with Image.open(root/Path(event['image']).name) as im:assert im.size==(frame.width,frame.height) and im.tobytes()==frame.pixels
previous=HERE/'results/prepared-self-use-01'
assert json.loads((previous/'steps.json').read_text())==prepared['command']['steps']
assert next(r for r in delivered if r['event']=='ready')['goal']==next(json.loads(line)['goal'] for line in (previous/'delivered.jsonl').read_text().splitlines() if json.loads(line)['event']=='ready')
observation=next(r for r in events if r['event']=='observation')
metrics=dict(actual='t991030',exact_frames=count,submit_commands=1,combined_exchange_calls=1,
    first_capture_to_socket_return_ms=(report['returned_ns']-observation['capture_ns'])/1e6,
    initial_socket_return_to_admission_ms=(accepted['accepted_ns']-initial['returned_ns'])/1e6,
    local_program_ms=(terminal['terminal_ns']-accepted['accepted_ns'])/1e6,
    exchange_ms=(report['returned_ns']-report['started_ns'])/1e6,
    limitation='same seed and steps, actual assistant, sequential one-run comparison; timings end at socket return before report/image processing, no causal speedup or token measurement')
(HERE/'results/prepared-exchange-self-use-audit.json').write_text(json.dumps(metrics,indent=2)+'\n')
(root/'client-sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),HERE/'prepared_exchange.py',HERE/'prepare_program.py',HERE/'receipt_image.py',HERE/'outcome_wait.py',HERE/'event_socket_v11.py',HERE/'event_cursor_v5.py',HERE/'request_boundary_v2.py')},indent=2)+'\n')
print(json.dumps(metrics,indent=2))
