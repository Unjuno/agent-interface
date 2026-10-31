from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
here=Path(__file__).resolve().parent
baseline=None
for n,mode in [('ad01','crash'),('ad02','inside'),('ad03','inside'),('ad04','crash')]:
 with ZipFile(here/(n+'.zip')) as z:
  r=json.loads(z.read('output/result.json'));src=tuple(z.read(p) for p in ('runner.py','worker_module.py','probe.py'));baseline=src if baseline is None else baseline
  assert src==baseline and z.read('exit.txt').decode('utf-8-sig').strip()=='0' and z.read('condition.txt').decode('utf-8-sig').strip()==mode
  assert r['mode']==mode and r['status']=='completed' and r['task_success'] is None and r.get('fallback_release') is not True and not r['down_after_cleanup'] and not r['down_after_late'] and not r['late_artifact']
  c=json.loads(z.read('output/custody.json'));down=json.loads(z.read('output/down.json'));assert c==r['custody'] and down==r['down']
  img=Image.open(io.BytesIO(z.read('output/baseline.png'))).convert('RGB');digest=hashlib.sha256(img.crop((32,408,90,450)).tobytes()).hexdigest();assert digest==r['ready']['baseline_hash']==down['crop_sha256']
  assert c['owner_pid']==r['ready']['owner_pid'] and c['owner_generation']['child_pid']==c['owner_pid'] and c['keys']['f']>0 and not c['buttons']
  assert r['ready']['before_input_ns']<down['grab_ns']<down['down_ns']<r['probe_start']['started_ns']<r['probe_done']['done_ns'] and r['probe_exit']==0
  if mode=='inside':assert down['ungrab_ns'] is None and r['probe_start']['started_ns']<r['owner_deadline_ns']<r['probe_done']['done_ns'] and r['probe_done']['done_ns']-r['probe_start']['started_ns']>500_000_000
  else:assert down['down_ns']<down['ungrab_ns']<r['probe_start']['started_ns']<r['probe_done']['done_ns']<r['owner_deadline_ns']
  outcome=r['owner_outcome'];clean=r['cleanup'];release=clean['owner_release_attempt']['release'];disconnect=clean['owner_client_disconnect'];assert outcome['worker_retired'] and outcome['status']=='unknown' and outcome['reason']=='transaction_deadline' and r['down_after_owner'] is True
  assert clean['status']=='completed' and clean['cleanup_status']=='UNKNOWN' and clean['release_confirmed'] is False and clean['task_success'] is None and clean['replay_allowed'] is False
  assert disconnect['status']=='disconnected' and disconnect['owner_process_retired'] and disconnect['expected_pid']==c['owner_pid'] and disconnect['resource_base']==c['resource_base']
  assert clean['owner_release_attempt']['status']=='readback_verified' and release['verified'] and not release['keys_down'] and not release['buttons_down'] and any(x['kind']=='KeyRelease' and x['code']==c['keys']['f'] for x in release['release_requests'])
  assert r['after_owner_ns']<release['release_started_monotonic_ns']<release['readback_monotonic_ns']<r['after_cleanup_ns']
  samples=r['samples'];assert [s['label'] for s in samples]==['before','after-cleanup','after-late'] and samples[0]['ammo']==50 and samples[-1]['host_ns']>down['scheduled_late_ns'] and all(a['tic']<b['tic'] for a,b in zip(samples,samples[1:]))
  print(n,mode,'probe_ms',round((r['probe_done']['done_ns']-r['probe_start']['started_ns'])/1e6,2),'ammo',*[s['ammo'] for s in samples])
print('four phase controls, bounded owner retirement, X11 probe and cleanup evidence verified')
