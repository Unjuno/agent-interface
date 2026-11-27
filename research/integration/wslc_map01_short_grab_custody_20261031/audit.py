from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
here=Path(__file__).resolve().parent
baseline=None
for n,mode in [('ac01','normal'),('ac02','crash'),('ac03','crash'),('ac04','normal')]:
 with ZipFile(here/(n+'.zip')) as z:
  r=json.loads(z.read('output/result.json'));src=tuple(z.read(p) for p in ('runner.py','worker_module.py'));baseline=src if baseline is None else baseline
  assert src==baseline and z.read('exit.txt').decode('utf-8-sig').strip()=='0' and z.read('condition.txt').decode('utf-8-sig').strip()==mode
  assert r['mode']==mode and r['status']=='completed' and r['task_success'] is None and r.get('fallback_release') is not True and not r['down_after_cleanup'] and not r['down_after_late'] and not r['late_artifact']
  c=json.loads(z.read('output/custody.json'));down=json.loads(z.read('output/down.json'));assert c==r['custody'] and down==r['down']
  img=Image.open(io.BytesIO(z.read('output/baseline.png'))).convert('RGB');digest=hashlib.sha256(img.crop((32,408,90,450)).tobytes()).hexdigest()
  assert digest==r['ready']['baseline_hash']==down['crop_sha256'] and c['owner_pid']==r['ready']['owner_pid'] and c['owner_generation']['child_pid']==c['owner_pid'] and c['keys']['f']>0 and not c['buttons']
  assert r['ready']['before_input_ns']<down['grab_ns']<down['down_ns']<down['ungrab_ns']<r['after_owner_ns']<=r['after_cleanup_ns']
  samples=r['samples'];assert [s['label'] for s in samples]==['before','after-cleanup','after-late'] and samples[0]['ammo']==50 and samples[-1]['host_ns']>down['scheduled_late_ns'] and all(a['tic']<b['tic'] for a,b in zip(samples,samples[1:]))
  outcome=r['owner_outcome'];assert outcome['worker_retired'] and outcome['session_id']==c['owner_generation']['session_id']
  if mode=='crash':
   clean=r['cleanup'];stage=clean['owner_release_attempt'];release=stage['release'];disconnect=clean['owner_client_disconnect']
   assert outcome['status']=='unknown' and outcome['reason']=='transaction_deadline' and r['down_after_owner'] is True
   assert clean['status']=='completed' and clean['cleanup_status']=='UNKNOWN' and clean['release_confirmed'] is False and clean['task_success'] is None and clean['replay_allowed'] is False
   assert disconnect['status']=='disconnected' and disconnect['owner_process_retired'] and disconnect['expected_pid']==c['owner_pid'] and disconnect['resource_base']==c['resource_base']
   assert stage['status']=='readback_verified' and release['verified'] and not release['keys_down'] and not release['buttons_down'] and any(x['kind']=='KeyRelease' and x['code']==c['keys']['f'] for x in release['release_requests'])
   assert r['after_owner_ns']<release['release_started_monotonic_ns']<release['readback_monotonic_ns']<r['after_cleanup_ns'] and samples[1]['ammo']==48 and samples[2]['ammo']==47
  else:assert outcome['status']=='completed' and r['down_after_owner'] is False and 'cleanup' not in r and samples[-1]['ammo']==49
  print(n,mode,'owner',outcome['status'],'key after cleanup',r['down_after_cleanup'],'ammo',*[s['ammo'] for s in samples])
print('all four custody, cleanup, late-observation and telemetry records verified')
