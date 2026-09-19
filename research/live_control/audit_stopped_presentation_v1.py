"""Reconcile fallback payloads against actual socket slices and tracked states."""
import hashlib
import json
from pathlib import Path
from stopped_client_v1 import PendingAction

HERE=Path(__file__).resolve().parent;root=HERE/'results/stopped-presentation-01'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,digest in read(root/'plan.json')['sources'].items():assert sha(HERE/name)==digest
calls=read(root/'calls.json');raw=[json.loads(x) for x in (root/'events.jsonl').read_text().splitlines()]
covered=[];tracker=PendingAction('fault',calls[0]['reply']['cursor']);views=[]
for i,c in enumerate(calls):
    a=c['request']['after'];b=c['reply']['cursor']
    assert c['reply']['records']==raw[a:b];covered.extend(range(a,b))
    if 1<=i<=4:views.append(tracker.ingest(a,c['reply']))
assert covered==list(range(len(raw)))
assert views==read(root/'client-states.json')
assert sum(e['event']=='command' and e['command'].get('op')=='submit' for e in raw)==1
assert sum(e['event']=='accepted' for e in raw)==1
assert [e['step'] for e in raw if e['event']=='step_started']==[0]
for stage,index,view in [('pending-presentation',1,views[0]),('terminal-presentation',4,views[-1])]:
    folder=root/stage;payload=read(folder/'received.bin');receipt=read(folder/'emission/receipt.json')
    assert payload['format']=='presentation-fallback-v1'
    assert payload['result']['lifecycle']==view and payload['result']['last_received_reply']==calls[index]['reply']
    assert payload['presentation_error']['type']=='RuntimeError'
    assert sha(folder/'received.bin')==sha(folder/'emission/payload.bin')==receipt['payload_sha256']
    assert receipt['status']=='locally_flushed' and receipt['model_received_ns'] is None
assert views[0]['terminal'] is None and views[-1]['terminal']['status']=='needs_decision'
assert views[-1]['terminal']['decision_reason']=='focus_changed'
assert read(root/'report.json')['exit_code']==0
report=dict(audit_passed=True,events=len(raw),calls=len(calls),presentations=2,
    audit_sha256=sha(Path(__file__)),scope='Real socket and subprocess, synthetic backend; output captured in memory, not a model-delivery test.')
with (root/'audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps(report))
