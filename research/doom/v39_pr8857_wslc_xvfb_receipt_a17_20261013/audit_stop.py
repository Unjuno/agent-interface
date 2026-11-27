import hashlib,json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent
raw=json.loads((root/'results/a17-01/raw.json').read_text(encoding='utf-8'))
manifest=json.loads((root/'SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
checks={}
checks['schema']=raw.get('schema')=='pr8857-wslc-xvfb-receipt-a17-raw-v1'
checks['candidate_harness_error']=(raw.get('error') or {}).get('type')=='AttributeError' and "'NoneType' object has no attribute 'id'" in (raw.get('error') or {}).get('message','')
checks['failure_before_release']=raw.get('release_transition') is None and raw.get('keymap')=={}
checks['admission_observed']=raw.get('admission',{}).get('event')=='input_admission' and raw.get('admission',{}).get('key')=='w' and raw.get('keycode',0)>0
checks['xvfb_exited']=raw.get('xvfb',{}).get('exit')==0
checks['container_exit_zero']=int((root/'results/a17-01/container.exit').read_text().strip())==0
hashchecks={}
for f in manifest['files']:
 p=root/f['path']
 digest=hashlib.sha256(p.read_bytes()).hexdigest()
 hashchecks[f['path']]=digest==f['sha256']
 if f.get('git_blob'):
  rel=f['path'].removeprefix('INPUT/')
  blob=subprocess.check_output(['git','rev-parse',f"origin/pr/8857:{rel}"],cwd=root.parents[2],text=True).strip()
  hashchecks[f['path']+':git_blob']=blob==f['git_blob']
result={'schema':'pr8857-wslc-xvfb-receipt-a17-stop-audit-v1','checks':checks,'source_checks':hashchecks,'raw_sha256':hashlib.sha256((root/'results/a17-01/raw.json').read_bytes()).hexdigest(),'decision':'STOP_HARNESS_EVENT_FIELD' if all(checks.values()) and all(hashchecks.values()) else 'AUDIT_FAIL','finding':'The only candidate attempt obtained an input_admission for w, then the test harness raised before event observation or explicit up because the Python-Xlib event object has no event.id attribute. Candidate was not retried. No physical release measurement can be inferred.'}
(root/'results/a17-01/audit_stop.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2,sort_keys=True))
sys.exit(0 if result['decision']=='STOP_HARNESS_EVENT_FIELD' else 1)

