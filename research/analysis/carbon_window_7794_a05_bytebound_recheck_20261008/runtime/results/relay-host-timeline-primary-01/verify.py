"""Read-only host event and independent single-form evidence audit."""
import base64,hashlib,json,tarfile
from pathlib import Path
root=Path(__file__).resolve().parent
prefix='results-local/relay-timeline-primary-01/'
def check(ok,message):
 if not ok:raise SystemExit(message)
def sha(data):return hashlib.sha256(data).hexdigest()
manifest=json.loads((root/'manifest.json').read_text());raw={}
with tarfile.open(root/'raw.tar.gz','r:gz') as archive:
 members=archive.getmembers();check(len(members)==len(manifest),'member count')
 for member in members:
  check(member.isfile() and member.name in manifest and member.name not in raw,'unexpected member')
  data=archive.extractfile(member).read();wanted=manifest[member.name]
  check(len(data)==wanted['bytes'] and sha(data)==wanted['sha256'],'hash mismatch '+member.name)
  raw[member.name]=data
def read(name):return json.loads(raw[prefix+name])
events=[json.loads(line) for line in raw[prefix+'transport/host-events.jsonl'].splitlines()]
check(len(events)==28 and [e['sequence'] for e in events]==list(range(1,29)),'event sequence')
check(all(events[i]['host_monotonic_ms']>=events[i-1]['host_monotonic_ms'] for i in range(1,len(events))),'host clock order')
def event(kind,attempt):
 rows=[e for e in events if e['kind']==kind and e.get('attempt')==attempt]
 check(len(rows)==1,'missing or duplicate event');return rows[0]
reports={}
for i in range(1,7):
 request=read(f'transport/request-{i}.json');reply=read(f'transport/reply-{i}.json')
 check(request['id']==i and reply['id']==i and request['tool']==reply['tool'] and reply['status']=='returned','transport identity')
 report=json.loads(reply['result']['content'][0]['text']);reports[i]=report
 stages=[event(kind,i) for kind in ['send_requested','reply_available','presentation_started','presentation_callbacks_completed']]
 check([e['sequence'] for e in stages]==sorted(e['sequence'] for e in stages),'presentation order')
 for row in stages[1:]:check(row['reply_sha256']==sha(raw[prefix+f'transport/reply-{i}.json']),'event reply identity')
 if i in (1,4,5):
  note=read(f'transport/review-{i}.json');review=event('review_recorded',i)
  check(stages[-1]['sequence']<review['sequence'],'review before callback boundary')
  check(note['reply_sha256']==review['reply_sha256']==stages[1]['reply_sha256'],'review reply identity')
  check(note['call_id']==review['call_id']==report['call_id'] and note['source_sequence']==review['source_sequence']==report['source']['sequence'],'review source')
  image=reply['result']['content'][1]
  check(note['images'][0]['sha256']==sha(base64.b64decode(image['data'],validate=True)),'review image')
 if i in (4,5):
  result=report['result'];check(result['status']=='completed' and result['recovery_required'] is False,'input result')
  check(bool(result['execution']['releases']) and all(r['verified'] is True and r['keys_down']==[] and r['buttons_down']==[] for r in result['execution']['releases']),'input release')
check(event('review_recorded',4)['sequence']==18 and event('send_requested',5)['sequence']==19,'review must precede Save')
history=[json.loads(s) for s in raw[prefix+'submission-history.jsonl'].splitlines()]
check(len(history)==1 and history[0]['task_id']=='task-1' and history[0]['submitted_values']==['t991330-1'],'independent single save')
check(read('scope.json')['planned_tasks']==['task-1'] and read('scope.json')['full_six_task_benchmark'] is False,'scope changed')
check(read('evaluation.json')['success'] is False and read('evaluation.json')['missing']==[f'task-{i}' for i in range(2,7)],'full fixture result must remain incomplete')
check(reports[6]['status']=='closed' and reports[6]['release']['verified'] is True and reports[6]['release']['keys_down']==[] and reports[6]['release']['buttons_down']==[],'close release')
check(read('transport/exit.json')['code']==0 and events[-1]['kind']=='transport_closed' and events[-1]['code']==0,'transport exit')
check(all(type(p['returncode']) is int for p in read('cleanup.json')),'child not terminal')
print(f'PASS: {len(raw)} files, 28 ordered events, review 18 before Save 19, one exact save; full six-task result remains incomplete.')