"""Read-only audit of an interrupted trial; does not claim task success."""
import base64,copy,hashlib,json,tarfile
from pathlib import Path
root=Path(__file__).resolve().parent
prefix='results-local/guarded-brief-primary-01/'
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
brief=full=before=after=0
for n in range(1,29):
 req=read(f'transport/request-{n}.json');rep=read(f'transport/reply-{n}.json')
 check(req['id']==rep['id']==n and req['tool']==rep['tool'],'request/reply identity')
 if req['tool']!='interface_guarded_input':continue
 check(req['arguments']['detail']=='brief','request detail')
 shown=json.loads(rep['result']['content'][0]['text']);original=read('server/'+shown['call_id']+'/report.json')
 restored=copy.deepcopy(shown);presentation=restored.pop('presentation')
 if presentation['returned']=='brief':
  brief+=1
  summary=restored['result'].pop('guard_summary');guards=original['result']['guard_checks']
  check(summary['count']==len(guards),'guard count')
  check(summary['checks']==[{k:g[k] for k in ('stage','observation_sequence','handle','status')} for g in guards],'guard identity')
  check(all(g['status']=='VALID' and g['reason']=='exact_region_match' for g in guards),'normal guard')
  restored['result']['guard_checks']=guards
 else:
  full+=1;check(n==17 and shown['result']['input_dispatched'] is False,'refusal control')
 check({k:restored[k] for k in original}==original,'raw report changed outside guard projection')
 check(set(restored)-set(original)=={'call_id','call_directory','image_status'},'unexpected presentation fields')
 images=[b for b in rep['result']['content'] if b['type']=='image'];check(len(images)==1,'image count')
 artifact=original['observation_report']['observation']['artifact']
 path=artifact['path'].split('/agent-interface-integrated-main/',1)[1]
 check(base64.b64decode(images[0]['data'],validate=True)==raw[path] and sha(raw[path])==artifact['sha256'],'image parity')
 before+=len(json.dumps(restored,allow_nan=False).encode());after+=len(rep['result']['content'][0]['text'].encode())
check(brief==21 and full==1,'input counts')
check(read('transport/exit.json')['code']==1,'interrupted transport')
check(prefix+'evaluation.json' not in raw and prefix+'cleanup.json' not in raw,'unexpected terminal evidence')
for n in (6,10,14,21,25):check(read(f'transport/review-{n}.json')['phase']=='saved','saved review missing')
check(prefix+'transport/request-29.json' not in raw,'unexpected sixth Save')
checks=json.loads(raw['results-local/guarded-brief-check-01/result.json'])
check(checks['status']=='PASS' and all(s['returncode']==0 for s in checks['suites']),'contract checks')
print(json.dumps({'status':'PASS','scope':'interrupted presentation evidence only','files':len(raw),'brief_inputs':brief,'full_refusals':full,'same_report_full_metadata_bytes':before,'actual_reply_metadata_bytes':after,'reduction_percent':round((before-after)/before*100,2),'six_task_success':'unproven','actual_model_tokens':'not measured'},indent=2))