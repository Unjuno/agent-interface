"""Check retained bytes and native discriminator data; do not replay input."""
from pathlib import Path
import json,hashlib,zipfile,io,re
p=Path(__file__).resolve().parent;m=json.loads((p/'manifest.json').read_text())
def need(x,msg):
 if not x:raise SystemExit('FAIL: '+msg)
raw=(p/m['archive']).read_bytes();need(hashlib.sha256(raw).hexdigest()==m['sha256'],'archive hash');z=zipfile.ZipFile(io.BytesIO(raw));names=z.namelist()
need(len(names)==len(set(names)) and set(names)=={f['path'] for f in m['files']},'archive closure')
for f in m['files']:
 b=z.read(f['path']);need(len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256'],'member '+f['path'])
load=lambda n:json.loads(z.read(n))
first=load('rows.json');second=load('grab-discriminator-01/rows.json');need(len(first)==21 and len(second)==3,'denominators')
need(load('PLAN.json')['cases']==['normal']*20+['withheld_release'],'first frozen cases')
need(load('grab-discriminator-01/PLAN.json')['cases']==['normal','synchronous_grab','withheld_release'],'second cases')
for rows,prefix in [(first,''),(second,'grab-discriminator-01/')]:
 for i,row in enumerate(rows):
  need(row['result']['status']=='execution_failed' and row['result']['execution']['failed_op']==2,'injected failure boundary')
  need(row['diagnostic_emissions']==0 and not row['effect_exists'],'read-only diagnostics/no saved task')
  need(not row['final_independent_mask'] & (1<<8) and not any(row['final_independent_keymap']),'final independent neutral')
  need(load(prefix+f'case-{i:02}-{row["mode"]}/cleanup.json')['app_exit'] is not None,'actual app exit')
  if row['mode']=='normal':
   need(row['result']['execution']['releases'][-1]['verified'] and all(not s['mask'] & (1<<8) for s in row['samples']),'ordinary neutral')
  else:
   need(not row['result']['execution']['releases'][-1]['verified'] and all(s['mask'] & (1<<8) for s in row['samples']),'held state observed')
   need(row['recovery_required_after_samples'] and row['blocked']['error']=='INPUT_RECOVERY_REQUIRED','block persists')
   rec=row['explicit_recovery'];need(rec['status']=='input_recovered' and rec['replay_allowed'] is False and rec['task_success'] is None,'explicit no-replay recovery')
 need(all(v is not None for v in load(prefix+'cleanup.json')['children']),'server child exit accounting')
grab=second[1];need(any(e['type']==4 and e['detail']==1 for e in grab['grab_events']),'actual passive-grab press')
need(not grab['after_allow_mask'] & (1<<8) and grab['emissions_after_allow']==0 and grab['recovery_required_after_allow'],'later neutral is not authority')
metrics=json.loads((p/'metrics.json').read_text());need(metrics['ordinary_unverified']==[] and metrics['grab_result']==grab['result'],'metrics agree')
final=load('live-regression-01/result.json');need(final['passed'] and final['tests']==55 and metrics['live_tests']==final,'live test count')
text=z.read('public-session-tests.txt').decode();need(re.search(r'Ran 66 tests',text) and '\nOK\n' in text,'public test count')
print(json.dumps({'status':'PASS_RETAINED_X11_GRAB_RECOVERY_DATA','files':len(names),'ordinary_count':20,'controlled_cases':3,'scope':'Exact bytes/data; no cause proof for historical intermittent failures, GUI replay or general performance claim.'}))
