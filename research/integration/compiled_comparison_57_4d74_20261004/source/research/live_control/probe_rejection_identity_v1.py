"""Refusal controls using actual rejection and earlier successful terminal records."""
import copy,hashlib,json
from pathlib import Path
from durable_submit_v2 import reconcile
from rejection_identity_v1 import rejected
from stopped_scope_v2 import boundary
HERE=Path(__file__).resolve().parent
r=HERE/'results/durable-rejection-02'
p=json.loads((r/'after-crash.json').read_text())['pending']
a=json.loads((r/'recover-0-reply.json').read_text())['records']
assert len(a)==2
controls={}
for field,value in [('id','other'),('transport_request_id','other'),('admission','unknown'),('op','cancel')]:
 events=copy.deepcopy(a);events[-1][field]=value
 remaining,resolution=reconcile(p,events)
 assert remaining is not None and resolution is None
 controls['wrong_'+field]='unresolved'
for name,events in [('missing_echo',[a[-1]]),('already_accepted',[a[0],{'event':'accepted','id':p['request']['command']['id']},a[-1]])]:
 remaining,resolution=reconcile(p,events);assert remaining is not None and resolution is None
 controls[name]='unresolved'
command=a[0]['command']
assert rejected(command,{command['id']},ValueError('duplicate'))['admission']=='unknown'
assert rejected(None,set(),ValueError('bad JSON'))=={'event':'rejected','reason':'bad JSON','admission':'unknown'}
assert rejected({'op':'submit','id':'x'},set(),ValueError('missing transport'))['admission']=='unknown'
controls['used_id_malformed_and_missing_identity']='unknown'
assert boundary(a[-1],['terminal'],command['id'])=='boundary'
assert boundary(a[-1],['terminal'],'other') is None
assert boundary({'event':'rejected'},['terminal'],command['id'])=='unattributed_rejection'
controls['scoped_boundary']='matching only; legacy unknown'
old=HERE/'results/durable-inkscape-01'
oldp=json.loads((old/'after-crash.json').read_text())['pending']
oldrecords=json.loads((old/'recover-0-reply.json').read_text())['records']
remaining,resolution=reconcile(oldp,oldrecords)
assert remaining is None and resolution==json.loads((old/'recovered.json').read_text())['last_resolution']
controls['previous_real_completed_terminal']='resolution unchanged'
report={'controls':controls,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'offline negative controls plus archived successful terminal compatibility'}
(r/'identity-controls.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
