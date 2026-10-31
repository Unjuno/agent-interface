"""Audit failed close criterion and corrected fresh cancellation cells; no -O."""
import hashlib,json,subprocess,zipfile
from pathlib import Path
H=lambda b:hashlib.sha256(b).hexdigest()
root=Path(__file__).parent
assert H((root/'failure.zip').read_bytes())=='e3d68f0d9284f212dfc34f75428af59f543e4e0eb35382822a3715780f165ebf'
assert H((root/'successor.zip').read_bytes())=='01cb5f4d5f48e310986b2b24f3d4d129214ce6c450897e9c9175120fbef4f24c'
with zipfile.ZipFile(root/'failure.zip') as old,zipfile.ZipFile(root/'successor.zip') as z:
 def audit(z):
  j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
  m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
  for n,h in m['files'].items():assert H(z.read(n))==h,n
  frozen=j('manifest.json')
  for n,h in frozen.items():assert H(z.read(n))==h,n
  return j,frozen
 jo,mo=audit(old);j,m=audit(z)
 source=[n for n in m if n.startswith('src/')]+['target.py','run.py']
 assert all(m[n]==mo[n] and H(old.read(n))==m[n] for n in source)
 tree=subprocess.check_output(['git','ls-tree','-r','--full-tree','ade6624badddf0eb2d9941bd9918381b67725d9c','runtime'],text=True).splitlines()
 blobs={r.split('\t',1)[1]:r.split()[2] for r in tree};mismatches=[]
 for n in source:
  if n.startswith('src/'):
   data=z.read(n).replace(b'\r\n',b'\n');path=n.removeprefix('src/')
   digest=hashlib.sha1(b'blob '+str(len(data)).encode()+bytes([0])+data).hexdigest()
   if digest!=blobs.get(path):mismatches.append(path)
 assert mismatches==['runtime/host_v1/test_primary_caller.mjs']
 before=old.read('trial.py').decode();after=z.read('trial.py').decode()
 needle="  assert r['old_close']['status']=='closed' and r['old_close']['verified'] and r['old_close']['release_confirmed']"
 replacement="  assert r['old_close']['status']=='closed' and r['old_close']['verified'] and not r['old_close']['release_attempted'] and r['old_close']['release_confirmed'] is None"
 assert before.count(needle)==1 and after==before.replace(needle,replacement)
 fail=jo('cancel-a01/output/result.json');assert fail==jo('cancel-a01/stdout') and fail['status']=='failed'
 assert jo('cancel-a01/launcher-result.json')['returncode']==1 and 'AssertionError' in fail['error']
 assert fail['cancel']['status']=='cancel_requested' and fail['down_before'] and fail['down_after'] and not fail['down_after_release']
 assert fail['old_close']['status']=='closed' and fail['old_close']['verified'] and not fail['old_close']['release_attempted'] and fail['old_close']['release_confirmed'] is None
 assert fail['target_exit']==fail['server_exit']==0
 assert jo('cancel-a02/conditions.json')['mode']=='withhold_close' and not any(n.startswith('cancel-a02/output/') for n in old.namelist())
 summaries=[]
 for arm,mode in [('cancel-b01','close_old'),('cancel-b02','withhold_close')]:
  c=j(f'{arm}/conditions.json');r=j(f'{arm}/output/result.json');launch=j(f'{arm}/launcher-result.json')
  assert c['allocation']=='idle-owned-'+arm+'-20261101' and c['mode']==mode
  assert c['order']==['cancel-b01:close_old','cancel-b02:withhold_close'] and c['manifest_sha256']==H(z.read('manifest.json'))
  assert r==j(f'{arm}/stdout') and launch['returncode']==0 and r['status']=='passed'
  assert r['initial_sequence']==1 and r['cancel']['status']=='cancel_requested' and r['capture']['status']=='unavailable' and r['state_before_resume']=='T'
  assert r['review_after_late_reply'] and r['down_before'] and r['down_after'] and not r['down_after_release']
  close=r['old_close'];assert close['status']=='closed' and close['verified'] and not close['release_attempted'] and close['release_confirmed'] is None
  assert not r.get('fallback_release_attempted',False) and r['target_exit']==r['server_exit']==0
  target=j(f'{arm}/output/target-events.json');assert target==r['target_result'] and target['value']=='a'
  assert [(x['type'],x['key']) for x in target['events']]==[('press','a'),('release','a')]
  e={x['name']:x['ns'] for x in r['events']};deadline=r['deadline_ns']
  assert e['stop_sent']<=e['stop_observed']<=e['capture_started']<=e['rpc_pending']<=e['cancel_started']<=e['cancel_returned']<deadline
  assert e['cancel_started']<=e['capture_returned']<deadline and e['capture_returned']<=e['resumed']<=e['fresh_press']<=e['hold_observed']<=e['fixture_release']
  if mode=='close_old':assert e['fresh_press']<=e['old_close']<=e['hold_observed']
  else:assert e['fixture_release']<=e['old_close']
  assert e['hold_observed']-e['fresh_press']>=350_000_000
  summaries.append({'arm':arm,'mode':mode,'cancel_to_capture_return_ms':(e['capture_returned']-e['cancel_started'])/1e6,
                    'hold_ms':(e['hold_observed']-e['fresh_press'])/1e6,'close_release_attempted':False})
 print(json.dumps({'failed_predecessor':'a01 retained','successor':summaries},indent=2))
