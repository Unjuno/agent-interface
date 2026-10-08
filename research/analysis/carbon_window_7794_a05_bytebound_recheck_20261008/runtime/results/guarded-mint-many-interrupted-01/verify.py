"""Audit retained interrupted evidence; never infer six-task success."""
import base64,hashlib,json,tarfile
from pathlib import Path
root=Path(__file__).resolve().parent
prefix='results-local/guarded-mint-many-primary-01/'
def check(ok,message):
 if not ok:raise SystemExit(message)
def sha(data):return hashlib.sha256(data).hexdigest()
manifest=json.loads((root/'manifest.json').read_text());raw={}
with tarfile.open(root/'raw.tar.gz','r:gz') as archive:
 for member in archive.getmembers():
  check(member.isfile() and member.name in manifest and member.name not in raw,'unexpected archive member')
  data=archive.extractfile(member).read();expected=manifest[member.name]
  check(len(data)==expected['bytes'] and sha(data)==expected['sha256'],'archive identity mismatch')
  raw[member.name]=data
check(set(raw)==set(manifest),'missing archive member')
def read(name):return json.loads(raw[prefix+name])
def shown(n):return json.loads(read(f'transport-recovery/reply-{n}.json')['result']['content'][0]['text'])
check(read('allocation.json')['seed']==991334,'wrong allocation')
initial=read('transport/reply-2.json')
check(initial['status']=='refused' and initial['dispatched'] is False and initial['next_id']==2,'initial relay refusal')
check(read('transport/request-3.json')['id']==2 and read('transport/request-3.json')['tool']=='interface_close','refused ID should remain reusable')
check(read('transport/exit.json')['code']==0,'initial transport close')
for n in range(1,16):
 req=read(f'transport-recovery/request-{n}.json');rep=read(f'transport-recovery/reply-{n}.json')
 check(req['id']==rep['id']==n and req['tool']==rep['tool'],'request identity')
check(read('transport-recovery/request-1.json')['tool']=='interface_guarded_observe','fresh recovery observation')
batch=shown(2)
check(batch['status']=='minted' and batch['input_dispatched'] is False,'batch did not mint without input')
check([x['alias'] for x in batch['minted']]==['field_a','save_a','keyboard_context'],'batch reference order')
check(read('transport-recovery/request-2.json')['arguments']['source_sequence']==shown(1)['source']['sequence'],'batch source')
for n in (4,8,12):
 receipt=read(f'transport-recovery/review-{n}.json');reply=raw[prefix+f'transport-recovery/reply-{n}.json'];report=shown(n)
 check(receipt['phase']=='saved' and receipt['reply_sha256']==sha(reply),'saved receipt binding')
 check(receipt['call_id']==report['call_id'] and receipt['source_sequence']==report['source']['sequence'],'saved source binding')
 images=[x for x in json.loads(reply)['result']['content'] if x['type']=='image']
 check([sha(base64.b64decode(x['data'],validate=True)) for x in images]==[x['sha256'] for x in receipt['images']],'saved image binding')
last=shown(15)
check(last['status']=='refused' and last['result']['input_dispatched'] is False,'stale reference refusal')
check(last['result']['guard_checks'][0]['status']=='MISSING' and last['presentation']['returned']=='full','full refusal detail')
check(read('transport-recovery/exit.json')['code']==1,'interrupted transport')
for name in ('finish.json','evaluation.json','evaluation-at-close.json','submission-history.jsonl','cleanup.json','transport-recovery/request-16.json'):
 check(prefix+name not in raw,'unexpected terminal evidence: '+name)
print(json.dumps({'status':'PASS','files':len(raw),'scope':'interrupted evidence identity and receipt attribution','batch_registrations':1,'registered_references':3,'caller_saved_receipts':3,'six_task_success':'unproven','release_at_interruption':'unverified','actual_model_tokens':'not measured'},indent=2))
