"""Audit three retained unsuccessful WSLc fixture attempts; no -O."""
import hashlib,json,zipfile
from pathlib import Path
H=lambda b:hashlib.sha256(b).hexdigest()
expected={'a03':'528552baf4632a5855cee892e41c07936c7d6880383f8afe054581719ecca3cc',
 'a04':'a944f60d68d9126200053c43093408576c1caf76678ee3c0927b674a28747a76',
 'a05':'9e96c8c5753aff37e5a66e7de86a50be85af15288246f6718a8cfd0f79d48543'}
summary=[]
for arm,digest in expected.items():
 path=Path(__file__).with_name(arm+'.zip');assert H(path.read_bytes())==digest
 with zipfile.ZipFile(path) as z:
  j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
  m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
  for n,h in m['files'].items():assert H(z.read(n))==h,n
  manifest=j('trial/manifest.json');c=j('trial/conditions.json')
  assert H(z.read('trial/manifest.json'))==c['manifest_sha256'] and c['allocation']=='idle-real-x-'+arm+'-20261101'
  for n,h in manifest.items():assert H(z.read(n))==h,n
  r=j('trial/output/result.json');assert r==j('trial/stdout') and r['status']=='failed'
  assert j('trial/launcher-result.json')['returncode']==1 and r['server_exit']==0
  assert 'trial/output/target-events.json' not in z.namelist()
  if arm in ('a03','a04'):
   assert r['capture']['status']=='unavailable' and r['state_before_resume']=='T'
   assert r['old_sequence_before_resume']==r['old_sequence_after_resume']==1 and r['old_review_required']
   assert r['worker_before_resume']['retired'] and not r['worker_after_resume']['thread_alive']
   assert r['target_exit']==0 and 'action' not in r
   assert ('target alias must match' if arm=='a03' else 'visually flat target region refused') in r['error']
  else:
   assert r['events']==[] and r['target_exit']==1
   assert "module 'Xlib.X' has no attribute 'Exposure'" in z.read('trial/output/target.stderr').decode()
  summary.append({'allocation':arm,'error':r['error'],'target_exit':r['target_exit']})
print(json.dumps(summary,indent=2))
