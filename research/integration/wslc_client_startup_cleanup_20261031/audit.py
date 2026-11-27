"""Audit real missing/valid Chromium startup and source custody."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json
p=Path(__file__).with_name('public.zip');assert hashlib.sha256(p.read_bytes()).hexdigest()=='db3de8fc7b6c7cd5f4143e205bb727c6c3e7c6202213c0bf1b7d87aee5eb14fc'
prior=p.parent.parent/'wslc_three_arm_main_configured_20261031'/'public.zip';assert hashlib.sha256(prior.read_bytes()).hexdigest()=='c1f664b9975d11b69e14759fe9a0bdb8a9d728889813c30fa951a20b33848a6a'
with ZipFile(p) as z,ZipFile(prior) as old:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
 m=j('manifest.json');assert set(z.namelist())==set(m['files'])|{'manifest.json'}
 for n,h in m['files'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
 f=j('frozen-manifest.json')
 for n,h in f.items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
 new=j('source-hashes.json');base=json.loads(old.read('source-hashes.json'));assert set(new)==set(base)
 changed=[n for n in new if new[n]!=base[n]];assert set(changed)=={'source/research/live_control/integrated_efficiency_client_v1.py','source/research/live_control/test_integrated_efficiency_client_v1.py'}
 for n in changed:assert hashlib.sha256(z.read('candidate/'+Path(n).name)).hexdigest()==new[n]
 v=j('verification.json');assert v['checked']==2092 and not v['source_mismatches'] and not v['frozen_mismatches'] and v['list_exit']==0 and not v['present']
 for ident,case in [('e04','missing'),('e05','valid')]:
  c=j(f'{ident}/conditions.json');l=j(f'{ident}/out/launcher.json');r=j(f'{ident}/out/receipt.json')
  assert c['allocation']==ident and c['case']==case and c['model_calls']==0 and c['frozen_manifest_sha256']==hashlib.sha256(z.read('frozen-manifest.json')).hexdigest()
  assert l['exit_code']==0 and l['timeout'] is False and r['case']==case and r['model_calls']==0
  if case=='missing':
   assert r['status']=='expected_failure' and r['error_type']=='RuntimeError' and 'runtime did not emit ready' in r['message']
   assert all(r[x] for x in ('child_exited','stderr_closed','temp_removed','stderr_has_missing'))
   assert b'FileNotFoundError' in z.read(f'{ident}/out/client/stderr.txt')
  else:assert r['status']=='ready' and r['app']=='chromium' and r['ready_event']=='ready'
 print(json.dumps({'status':'audited','missing':'explicit failure, owned child exited and resources cleaned','valid':'Chromium ready','model_calls':0,'source_files_checked':v['checked']},indent=2))
