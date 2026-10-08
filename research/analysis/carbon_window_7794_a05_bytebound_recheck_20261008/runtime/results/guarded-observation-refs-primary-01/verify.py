"""Read-only audit of a completed bounded-reference-registration trial."""
import base64,copy,hashlib,json,tarfile
from pathlib import Path
root=Path(__file__).resolve().parent
prefix='results-local/guarded-observation-refs-primary-01/'
def check(value,message):
 if not value: raise SystemExit(message)
def sha(data):return hashlib.sha256(data).hexdigest()
manifest=json.loads((root/'manifest.json').read_text());raw={}
with tarfile.open(root/'raw.tar.gz','r:gz') as archive:
 for m in archive.getmembers():
  check(m.isfile() and m.name in manifest and m.name not in raw,'unexpected member')
  data=archive.extractfile(m).read();expected=manifest[m.name]
  check(len(data)==expected['bytes'] and sha(data)==expected['sha256'],'file identity')
  raw[m.name]=data
check(set(raw)==set(manifest),'missing member')
def read(name):return json.loads(raw[prefix+name])
import types
refs=types.ModuleType('archived_references')
exec(compile(raw['runtime/cli_v1/receipt_references.py'],'archived_references.py','exec'),refs.__dict__)
def expand(value):return refs.expand_guarded_observation(value)

brief=full=before=after=0
for n in range(1,30):
 req=read(f'transport/request-{n}.json');rep=read(f'transport/reply-{n}.json')
 check(req['id']==rep['id']==n and req['tool']==rep['tool'],'request/reply identity')
 if req['tool']!='interface_guarded_input':continue
 check(req['arguments']['detail']=='brief','request detail')
 shown=json.loads(rep['result']['content'][0]['text']);original=read('server/'+shown['call_id']+'/report.json')
 restored=expand(shown);presentation=restored.pop('presentation')
 if presentation['returned']=='brief':
  brief+=1
  releases=shown['result']['execution']['releases']
  check(bool(releases) and all(r['verified'] is True and r['keys_down']==[] and r['buttons_down']==[] for r in releases),'normal release')
  summary=restored['result'].pop('guard_summary');guards=original['result']['guard_checks']
  check(summary['count']==len(guards),'guard count')
  check(summary['checks']==[{k:g[k] for k in ('stage','observation_sequence','handle','status')} for g in guards],'guard identity')
  check(all(g['status']=='VALID' and g['reason']=='exact_region_match' for g in guards),'normal guard')
  restored['result']['guard_checks']=guards
 else:
  full+=1;check(n == 15 and shown['result']['input_dispatched'] is False,'refusal control')
 check({k:restored[k] for k in original}==original,'raw report changed outside guard projection')
 check(set(restored)-set(original)=={'call_id','call_directory','image_status'},'unexpected presentation fields')
 images=[b for b in rep['result']['content'] if b['type']=='image'];check(len(images)==1,'image count')
 artifact=original['observation_report']['observation']['artifact']
 path=artifact['path'].split('/agent-interface-integrated-main/',1)[1]
 check(base64.b64decode(images[0]['data'],validate=True)==raw[path] and sha(raw[path])==artifact['sha256'],'image parity')
 before+=len(json.dumps(restored,allow_nan=False).encode());after+=len(rep['result']['content'][0]['text'].encode())
check(brief==22 and full==1,'input counts')
check(read('transport/exit.json')['code']==0,'transport exit')
evaluation=read('evaluation.json')
check(evaluation['success'] is True and evaluation['record_count']==6 and evaluation['exact_counts']=={f'task-{i}':1 for i in range(1,7)} and not evaluation['missing'] and not evaluation['duplicates'] and not evaluation['unexpected'],'independent oracle')
history=[json.loads(line) for line in raw[prefix+'submission-history.jsonl'].splitlines()]
check(len(history)==6 and all(row['submitted_values']==[f't991336-{i}'] and row['task_id']==f'task-{i}' for i,row in enumerate(history,1)),'independent values')
events=[json.loads(line) for line in raw[prefix+'transport/host-events.jsonl'].splitlines()]
check([e['sequence'] for e in events]==list(range(1,len(events)+1)),'event sequence')
check(all(events[i]['host_monotonic_ms']>=events[i-1]['host_monotonic_ms'] for i in range(1,len(events))),'host clock order')
def event(kind,n):
 rows=[e for e in events if e['kind']==kind and e.get('attempt')==n]
 check(len(rows)==1,'event missing/duplicate');return rows[0]
for n in range(1,30):
 stages=[event(k,n) for k in ('send_requested','reply_available','presentation_started','presentation_callbacks_completed')]
 check([e['sequence'] for e in stages]==sorted(e['sequence'] for e in stages),'presentation order')
 for e in stages[1:]:check(e['reply_sha256']==sha(raw[prefix+f'transport/reply-{n}.json']),'event reply identity')
for entered,saved in zip((3,7,11,17,21,25),(4,8,12,18,22,26)):
 check(event('presentation_callbacks_completed',entered)['sequence']<event('review_recorded',entered)['sequence']<event('send_requested',saved)['sequence'],'review before Save')
 for n,phase in ((entered,'entered'),(saved,'saved')):
  note=read(f'transport/review-{n}.json');reply=read(f'transport/reply-{n}.json');report=json.loads(reply['result']['content'][0]['text'])
  check(note['phase']==phase and note['reply_sha256']==sha(raw[prefix+f'transport/reply-{n}.json']),'review identity')
  check(note['call_id']==report['call_id'] and note['source_sequence']==report['source']['sequence'],'review source')
  check(note['images'][0]['sha256']==sha(base64.b64decode(reply['result']['content'][1]['data'],validate=True)),'review image')
def report(n):return json.loads(read(f'transport/reply-{n}.json')['result']['content'][0]['text'])
close=report(28)
check(close['status']=='closed' and close['release']['verified'] is True and close['release']['keys_down']==[] and close['release']['buttons_down']==[],'close release')
check(all(type(p['returncode']) is int for p in read('cleanup.json')),'cleanup terminal')
check(events[-1]['kind']=='transport_closed' and events[-1]['code']==0,'host terminal')


for n in (27,29):
 retained=expand(report(n));original=read('server/'+retained['call_id']+'/report.json')
 check(retained['operation_invoked'] is False and retained['call_id']==report(26)['call_id'],'read-only final result')
 if n==29:
  check(retained.pop('presentation')['returned']=='brief','post-close brief')
  retained['result'].pop('guard_summary');retained['result']['guard_checks']=original['result']['guard_checks']
 check({k:retained[k] for k in original}==original,'retained reconstruction parity')
check('reference_schema' not in report(27) and report(27)['image_delivery']=='omitted_by_request','full unreferenced retrieval')
check(read('transport/reply-26.json')['result']['content'][1]==read('transport/reply-29.json')['result']['content'][1],'post-close identical image')
check('reference_schema' not in report(15),'refusal must remain literal')
first=expand(report(1));original=read('server/'+first['call_id']+'/report.json')
check({k:first[k] for k in original}==original,'observation reconstruction')
expanded_bytes=actual_bytes=reference_count=0
for n in range(1,30):
 row=report(n);expanded=expand(row)
 if 'reference_schema' in row:
  reference_count+=1
  check(row['observation_references']=={'/observation_report/observation':'/source/native'},'fixed local map')
  check(row['source']['native']==expanded['observation_report']['observation'],'canonical identity')
 actual_bytes+=len(read(f'transport/reply-{n}.json')['result']['content'][0]['text'].encode())
 expanded_bytes+=len(json.dumps(expanded,allow_nan=False).encode())
check(reference_count==24,'reference count')
check(close['session']['observation_sequence']==report(26)['source']['sequence']==93,'no capture on retrieval')
check(read('transport/request-1.json')['arguments']['observation_refs'] is True,'observe opt-in')
for n in range(3,27):
 if n==16:continue
 check(read(f'transport/request-{n}.json')['arguments']['observation_refs'] is True,'input opt-in')
checks=json.loads(raw['results-local/guarded-observation-refs-check-01/result.json'])
check(checks['status']=='PASS' and all(s['returncode']==0 for s in checks['suites']),'contract checks')
print(json.dumps({'status':'PASS','scope':'six-task referenced-response usability; same-record metadata only','files':len(raw),'mcp_calls':29,'reference_count':reference_count,'expanded_same_view_utf8_bytes':expanded_bytes,'actual_returned_utf8_bytes':actual_bytes,'reduction_percent':round((expanded_bytes-actual_bytes)/expanded_bytes*100,4),'brief_inputs':brief,'full_refusals':full,'six_task_success':True,'gui_child_returncodes':[p['returncode'] for p in read('cleanup.json')],'actual_model_tokens':'not measured'},indent=2))
