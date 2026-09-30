"""Audit incomplete GUI trial and retained host callback failure."""
import hashlib,json,tarfile
from pathlib import Path
root=Path(__file__).resolve().parent;prefix='results-local/guarded-brief-primary-02/'
def check(ok,message):
 if not ok:raise SystemExit(message)
manifest=json.loads((root/'manifest.json').read_text());raw={}
with tarfile.open(root/'raw.tar.gz') as archive:
 for m in archive.getmembers():
  check(m.isfile() and m.name in manifest and m.name not in raw,'unexpected member')
  data=archive.extractfile(m).read();expected=manifest[m.name]
  check(len(data)==expected['bytes'] and hashlib.sha256(data).hexdigest()==expected['sha256'],'hash mismatch')
  raw[m.name]=data
check(set(raw)==set(manifest),'missing member')
def read(name):return json.loads(raw[prefix+name])
request=read('transport/request-7.json');reply=read('transport/reply-7.json')
check('offset' not in request['arguments'],'missing offset reproduction')
check(reply['result']['isError'] is True and 'offset\n  Field required' in reply['result']['content'][0]['text'],'validation error')
events=[json.loads(line) for line in raw[prefix+'transport/host-events.jsonl'].splitlines()]
check([e['sequence'] for e in events]==list(range(1,32)),'event sequence')
check([e['kind'] for e in events if e.get('attempt')==7]==['send_requested','reply_available','presentation_started'],'callback failure boundary')
check(events[-1]['kind']=='transport_closed' and events[-1]['code']==0,'transport cleanup')
evaluation=read('evaluation.json')
check(evaluation['success'] is False and evaluation['record_count']==1 and evaluation['exact_counts']['task-1']==1 and evaluation['missing']==['task-2','task-3','task-4','task-5','task-6'],'incomplete oracle')
check(read('finish.json')['primary_review_complete'] is False,'scope')
closes=[json.loads(v) for k,v in raw.items() if k.startswith(prefix+'server/session-') and k.endswith('-close.json')]
check(len(closes)==1 and closes[0]['status']=='closed' and closes[0]['release']['verified'] is True and closes[0]['release']['keys_down']==[] and closes[0]['release']['buttons_down']==[],'owner close')
check(all(type(p['returncode']) is int for p in read('cleanup.json')),'live child')
print(f'PASS: {len(raw)} files; validation refusal, callback failure, one exact task, five missing, verified owner release; NOT six-task success.')