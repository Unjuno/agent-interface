"""Audit preflight, failed scoring race and successor records; no -O."""
import hashlib,io,json,zipfile
from pathlib import Path
from PIL import Image
H=lambda b:hashlib.sha256(b).hexdigest()
expected={'preflight':'9ee718018c81f60a2c45101a08bcfd40e44cc8728c377d48d9476951794d57ae',
 'a06':'5ea55d46a52b449c6a149eb057bcd414d50554b9f1de555fd54995e1f6cb7373',
 'a07':'28dd02eacad4a627530b09b58e4480ec5fdd74f3d752e34bbd9adf377e0de128'}
data={}; manifests={}; sources={}
for ident,digest in expected.items():
 p=Path(__file__).with_name(ident+'.zip');assert H(p.read_bytes())==digest
 with zipfile.ZipFile(p) as z:
  j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
  m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
  for n,h in m['files'].items():assert H(z.read(n))==h,n
  manifest=j('trial/manifest.json');c=j('trial/conditions.json')
  assert H(z.read('trial/manifest.json'))==c['manifest_sha256']
  for n,h in manifest.items():assert H(z.read(n))==h,n
  r=j('trial/output/result.json');assert r==j('trial/stdout')
  data[ident]={'result':r,'conditions':c,'launch':j('trial/launcher-result.json'),
               'target':j('trial/output/target-events.json')}
  manifests[ident]=manifest;sources[ident]=z.read('real_x_trial.py').decode()
  if ident=='preflight':
   image=Image.open(io.BytesIO(z.read('trial/output/target-crop.png'))).convert('RGB')
   assert len(set(image.getdata()))==r['crop_colors']==2
   preflight_manifest=z.read('trial/manifest.json');preflight_result=z.read('trial/output/result.json')
runtime=[n for n in manifests['preflight'] if n.startswith('src/')]+['target.py']
assert runtime and all(manifests['preflight'][n]==manifests['a06'][n]==manifests['a07'][n] for n in runtime)
for ident in ('a06','a07'):
 c=data[ident]['conditions'];assert c['preflight_manifest_sha256']==H(preflight_manifest) and c['preflight_result_sha256']==H(preflight_result)
needle="   target_result=json.loads((out/'target-events.json').read_text())"
replacement="   try:target_result=json.loads((out/'target-events.json').read_text())\n   except json.JSONDecodeError:\n    time.sleep(.01);continue"
assert sources['a06'].count(needle)==1 and sources['a07']==sources['a06'].replace(needle,replacement)
for ident in expected:
 row=data[ident];r=row['result'];a=r['action'];target=row['target']
 assert a['status']=='completed' and a['execution']['releases'][-1]['verified']
 assert not a['execution']['releases'][-1]['keys_down'] and not a['execution']['releases'][-1]['buttons_down']
 assert target['value']=='a' and [(e['type'],e['key']) for e in target['events']]==[('press','a'),('release','a')]
 assert r['target_exit']==r['server_exit']==0
 if ident=='preflight':
  assert r['status']=='passed' and row['launch']['returncode']==0 and r['target_result']==target and r['input_neutral_before_after']
 else:
  e={v['name']:v['ns'] for v in r['events']}; deadline=r['deadline_ns']
  assert e['stop_sent']<=e['stop_observed']<=e['capture_started']<=e['pending_while_stopped']<deadline<=e['capture_returned']<=e['resumed']<=e['old_closed']<=e['action_returned']
  assert r['state_before_resume']=='T' and r['capture']['status']=='unavailable'
  assert r['old_sequence_before_resume']==r['old_sequence_after_resume']==1 and r['old_review_required']
  assert r['worker_before_resume']['retired'] and not r['worker_after_resume']['thread_alive']
  assert e['resumed']<target['events'][0]['host_ns']<=target['events'][1]['host_ns']
  if ident=='a06':
   assert r['status']=='failed' and row['launch']['returncode']==1 and 'JSONDecodeError' in r['error']
   assert 'target_result' not in r and 'input_neutral_before_after' not in r
  else:
   assert r['status']=='passed' and row['launch']['returncode']==0 and r['target_result']==target and r['input_neutral_before_after']
print(json.dumps({'status':'audited','preflight':'passed','a06':'failed: scoring read raced a write',
                  'a07':'passed synthetic fresh-session key task; neutral input recorded'},indent=2))
