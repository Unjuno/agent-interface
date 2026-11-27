"""Audit retained source, recorded process/capture ordering and artifacts; no -O."""
import hashlib,io,json,subprocess,zipfile
from pathlib import Path
H=lambda b:hashlib.sha256(b).hexdigest()
archive=Path(__file__).with_name('public.zip')
assert H(archive.read_bytes())=='1ca2f8069c6c788c3c39a553264f674c31a256b766be2f31e149f247cd85f5ed'
prior=subprocess.check_output(['git','show','b07be4f1bc3ee2c023381522c633a792ad732d08:research/integration/wslc_idle_observation_prototype_20261101/public.zip'])
assert H(prior)=='1f19d9afbabdd1fd5f3ed50a2a238b92c9949bdac48f2a9c7963b0cbfae24df7'
with zipfile.ZipFile(io.BytesIO(prior)) as prev,zipfile.ZipFile(archive) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
 m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
 for n,h in m['files'].items():assert H(z.read(n))==h,n
 frozen=j('trial/manifest.json'); c=j('trial/conditions.json')
 assert H(z.read('trial/manifest.json'))==c['manifest_sha256'] and c['base_main']=='b07be4f1bc3ee2c023381522c633a792ad732d08'
 assert c['allocation']=='idle-real-x-a02-20261101'
 for n,h in frozen.items():assert H(z.read(n))==h,n
 previous=json.loads(prev.read('trial/manifest.json'))
 src=[n for n in frozen if n.startswith('src/')]
 assert src and set(src)=={n for n in previous if n.startswith('src/')}
 assert all(frozen[n]==previous[n] and H(prev.read(n))==frozen[n] for n in src)
 result=j('trial/output/result.json');assert result==j('trial/stdout') and j('trial/launcher-result.json')['returncode']==0
 assert result['status']=='passed' and result['healthy']=={'sequence':1,'late_cancel':'not_active'}
 rows=result['events'];names=[r['name'] for r in rows]
 assert names==['stop_sent','server_stop_observed','capture_started','pending_while_stopped','capture_returned','before_resume','resume_sent','worker_observed_after_resume']
 t={r['name']:r['monotonic_ns'] for r in rows};deadline=result['deadline_ns']
 assert t['stop_sent']<=t['server_stop_observed']<=t['capture_started']<=t['pending_while_stopped']<deadline<=t['capture_returned']<=t['before_resume']<=t['resume_sent']<=t['worker_observed_after_resume']
 assert rows[1]['state']==rows[3]['state']==result['server_state_after_return']=='T'
 assert rows[4]['status']==result['capture']['status']=='unavailable'
 assert result['worker_before_resume']['retired'] and result['worker_before_resume']['pending'] and result['worker_before_resume']['thread_alive']
 assert result['worker_after_resume']['retired'] and not result['worker_after_resume']['thread_alive'] and not result['worker_after_resume']['pending']
 assert result['sequence_before_resume']==result['sequence_after_resume']==1 and result['review_required'] and result['input_neutral_before_after'] and result['server_exit']==0
 for seq in (1,2):
  observation=j(f'trial/output/bridge/isolated-observations/observation-{seq}.json');assert observation['sequence']==seq
  a=observation['native']['artifact'];assert H(z.read('trial/output/'+a['path'].removeprefix('/out/')))==a['sha256']
 print(json.dumps({'status':'audited','capture_ms':(t['capture_returned']-t['capture_started'])/1e6,
  'deadline_overrun_ms':(t['capture_returned']-deadline)/1e6,'worker_wait_channel':rows[3]['wchan'],
  'owner_sequence_after_resume':result['sequence_after_resume']},indent=2))
