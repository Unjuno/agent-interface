"""Audit withheld-input cell and its relationship to a07; no -O."""
import hashlib,io,json,subprocess,zipfile
from pathlib import Path
H=lambda b:hashlib.sha256(b).hexdigest()
archive=Path(__file__).with_name('public.zip')
assert H(archive.read_bytes())=='6804d0d6cc3dbdc6467bfa406fd78d143f63fca3d7ecdf3f6b88c04ec43d102f'
prior=subprocess.check_output(['git','show','e78ad4102de590f3ad267f6429ae672ec22b3ddf:research/integration/wslc_idle_recovery_preflight_race_20261101/a07.zip'])
assert H(prior)=='28dd02eacad4a627530b09b58e4480ec5fdd74f3d752e34bbd9adf377e0de128'
with zipfile.ZipFile(io.BytesIO(prior)) as prev,zipfile.ZipFile(archive) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
 m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
 for n,h in m['files'].items():assert H(z.read(n))==h,n
 frozen=j('trial/manifest.json');previous=json.loads(prev.read('trial/manifest.json'));c=j('trial/conditions.json')
 assert H(z.read('trial/manifest.json'))==c['manifest_sha256'] and c['allocation']=='idle-real-x-a08-20261101'
 assert c['base_main']=='e78ad4102de590f3ad267f6429ae672ec22b3ddf'
 for n,h in frozen.items():assert H(z.read(n))==h,n
 source=[n for n in frozen if n.startswith('src/')]+['target.py']
 assert set(source)=={n for n in previous if n.startswith('src/')}|{'target.py'}
 assert all(frozen[n]==previous[n] and H(prev.read(n))==frozen[n] for n in source)
 r=j('trial/output/result.json');assert r==j('trial/stdout') and j('trial/launcher-result.json')['returncode']==0
 assert r['status']=='passed' and r['capture']['status']=='unavailable' and r['state_before_resume']=='T'
 assert r['initial_sequence']==r['old_sequence_before_resume']==r['old_sequence_after_resume']==1 and r['old_review_required']
 assert r['worker_before_resume']['retired'] and not r['worker_after_resume']['thread_alive']
 assert r['action_withheld'] and r['target_event_file_absent'] and 'action' not in r
 assert 'trial/output/target-events.json' not in z.namelist()
 assert r['input_neutral_before_after'] and r['target_exit']==r['server_exit']==0
 e={row['name']:row['ns'] for row in r['events']};deadline=r['deadline_ns']
 assert e['stop_sent']<=e['stop_observed']<=e['capture_started']<=e['pending_while_stopped']<deadline<=e['capture_returned']<=e['resumed']<=e['old_closed']<=e['withhold_started']<e['withhold_completed']<=e['fresh_closed']
 assert e['withhold_completed']-e['withhold_started']>=2_000_000_000
 prior_result=json.loads(prev.read('trial/output/result.json'));target=json.loads(prev.read('trial/output/target-events.json'))
 assert prior_result['status']=='passed' and prior_result['action']['status']=='completed' and prior_result['action']['execution']['releases'][-1]['verified']
 assert target['value']=='a' and [(v['type'],v['key']) for v in target['events']]==[('press','a'),('release','a')]
 print(json.dumps({'status':'audited','control':'withheld, no recorded target key event',
  'control_duration_ms':(e['withhold_completed']-e['withhold_started'])/1e6,
  'a07':'sent a; target recorded press, release, value a'},indent=2))
