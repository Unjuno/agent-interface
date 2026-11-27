"""Audit early/late private-Xvfb resume and the preserved test regression."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json
p=Path(__file__).with_name('public.zip')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='1830ec548700105506c8b4e1f02680c34c595246db019f768959bd7880c482ef'
with ZipFile(p) as z:
 m=json.loads(z.read('manifest.json'))
 assert set(z.namelist())==set(m['files'])|{'manifest.json'}
 for n,h in m['files'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
 report={}
 for t,code,old,fresh in [('b08',1,'pass',None),('b09',0,'pass','pass'),('b10',1,'fail','pass')]:
  run=json.loads(z.read(f'{t}/out/launcher.json'));r=json.loads(z.read(f'{t}/out/receipt.json'))
  assert run['exit_code']==code and run['timeout'] is False
  assert r['conditions']['prestarted_cancel_supervisor'] is True
  assert r['synthetic_task_oracle']['status']==old
  assert r['independent_readback_after_close']['keys_down']['a'] is True
  assert r['cancel']['cleanup_status']=='UNKNOWN' and r['cancel']['replay_allowed'] is False
  assert r['final_cleanup']['keys_down']=={'a':False,'b':False}
  recovery=(r.get('recovery') or {}).get('independent_task_oracle')
  assert (None if recovery is None else recovery['status'])==fresh
  if t=='b08':
   assert r['independent_readback_after_resume']['horizon_readback']['a'] is False
   assert b"{'a': True, 'b': False} != {'a': False, 'b': False}" in z.read(f'{t}/out/stderr.bin')
  if t=='b09':
   result=r['cancellation_terminal']['result'];assert result['cleanup_status']=='UNKNOWN' and result['release_confirmed'] is False
   assert result['owner_release_attempt']['status']=='readback_verified'
  if t=='b10':assert b"'fail' != 'pass'" in z.read(f'{t}/out/stderr.bin')
  report[t]={'exit':code,'stop_ms':r['server_stop_ms'],'old_task':old,'fresh_task':fresh,'new_client_hold_survives_close':True}
 print(json.dumps({'status':'audited','trials':report},indent=2))
