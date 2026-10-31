"""Audit two isolated stopped-Xvfb receipts and their preserved failures."""
import hashlib,json
from pathlib import Path
from zipfile import ZipFile
p=Path(__file__).with_name('public.zip')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='3e6f87541df6ca1f623dedd3fe935dd689025c8e39a269c43caa34a2bd1544af'
with ZipFile(p) as z:
 m=json.loads(z.read('manifest.json'))
 assert set(z.namelist())==set(m['files'])|{'manifest.json'}
 for n,h in m['files'].items(): assert hashlib.sha256(z.read(n)).hexdigest()==h,n
 results={}
 for t,code,supervisor in [('b04',1,True),('b05',0,False)]:
  run=json.loads(z.read(f'{t}/out/launcher.json'));r=json.loads(z.read(f'{t}/out/receipt.json'))
  assert run['exit_code']==code and not run['timeout']
  assert r['conditions']['prestarted_cancel_supervisor'] is supervisor
  assert r['cancel']['release_confirmed'] is False and r['cancel']['replay_allowed'] is False
  assert r['synthetic_task_oracle']['status']=='fail'
  assert r['independent_readback_after_resume']['horizon_readback']=={'a':True,'b':False}
  assert r['final_cleanup']['keys_down']=={'a':False,'b':False}
  recovery=(r.get('recovery') or {}).get('independent_task_oracle')
  if supervisor:
   attempt=r['stopped_terminal']['cancellation']['result']['owner_release_attempt']
   assert attempt['status']=='unknown' and attempt['reason']=='transaction_deadline' and attempt['worker_retired'] is True
   assert recovery is None
   assert b"'fail' != 'pass'" in z.read(f'{t}/out/stderr.bin')
  else:
   assert recovery['status']=='pass' and recovery['task_success'] is True
  results[t]={'supervisor':supervisor,'exit_code':code,'old_task':'fail','fresh_task':None if recovery is None else recovery['status'],'cancel_seconds':r['cancel_elapsed_s']}
 print(json.dumps({'status':'audited','results':results},indent=2))
