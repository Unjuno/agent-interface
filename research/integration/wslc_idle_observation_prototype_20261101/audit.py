"""Check retained trial, frozen source hashes and screenshot artifacts; no -O."""
import hashlib,json,zipfile
from pathlib import Path
H=lambda data:hashlib.sha256(data).hexdigest()
archive=Path(__file__).with_name('public.zip')
assert H(archive.read_bytes())=='1f19d9afbabdd1fd5f3ed50a2a238b92c9949bdac48f2a9c7963b0cbfae24df7'
with zipfile.ZipFile(archive) as z:
 j=lambda name:json.loads(z.read(name).decode('utf-8-sig'))
 m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
 for name,digest in m['files'].items():assert H(z.read(name))==digest,name
 frozen=j('trial/manifest.json');conditions=j('trial/conditions.json')
 assert H(z.read('trial/manifest.json'))==conditions['manifest_sha256']
 for name,digest in frozen.items():assert H(z.read(name))==digest,name
 assert conditions['base_main']=='46ff81d345de4b08cd62de1bb4fa4ff1b4f7ec0c'
 assert conditions['allocation']=='idle-real-x-a01-20261101'
 result=j('trial/output/result.json');assert result==j('trial/stdout')
 assert j('trial/launcher-result.json')['returncode']==0
 assert result['status']=='passed' and result['healthy']=={'sequence':1,'late_cancel':'not_active'}
 assert result['stopped_return']=='unavailable' and result['retired_before_resume'] and result['review_required']
 assert result['sequence_before_resume']==result['sequence_after_resume']==1
 assert result['worker_after_resume']['retired'] and not result['worker_after_resume']['thread_alive']
 assert result['input_neutral_before_after'] and result['server_exit']==0
 assert result['stopped_elapsed_ms']>=300
 for sequence in (1,2):
  obs=j(f'trial/output/bridge/isolated-observations/observation-{sequence}.json')
  assert obs['sequence']==sequence
  artifact=obs['native']['artifact']; path='trial/output/'+artifact['path'].removeprefix('/out/')
  assert H(z.read(path))==artifact['sha256']
 print(json.dumps({'status':'audited','elapsed_ms':result['stopped_elapsed_ms'],
                   'owner_sequence_after_resume':result['sequence_after_resume'],
                   'late_worker_artifact_sequence':2},indent=2))
