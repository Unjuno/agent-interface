"""Audit stopped-server observations; original task failure remains failure."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json
p=Path(__file__).with_name('public.zip')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='a7783a39770def530f1da8c36c021ba43c23ed13532b766ec69a3ff329273db1'
with ZipFile(p) as z:
 m=json.loads(z.read('manifest.json'))
 assert set(z.namelist())==set(m['files'])|{'manifest.json'}
 for n,h in m['files'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
 summary={}
 for trial,exit_code,supervisor in [('b06',1,True),('b07',0,False)]:
  launch=json.loads(z.read(f'{trial}/out/launcher.json'));r=json.loads(z.read(f'{trial}/out/receipt.json'))
  assert launch['exit_code']==exit_code and launch['timeout'] is False
  assert r['conditions']['prestarted_cancel_supervisor'] is supervisor
  assert r['synthetic_task_oracle']['status']=='fail' and r['synthetic_task_oracle']['task_success'] is False
  assert r['cancel']['release_confirmed'] is False and r['cancel']['replay_allowed'] is False
  assert r['independent_readback_after_resume']['horizon_readback']=={'a':True,'b':False}
  assert r['independent_readback_after_close']['keys_down']=={'a':True,'b':False}
  rec=r['recovery'];assert rec['independent_task_oracle']['status']=='pass' and rec['independent_task_oracle']['task_success'] is True
  assert rec['independent_readback']['horizon_readback']=={'a':False,'b':False}
  assert r['final_cleanup']['keys_down']=={'a':False,'b':False}
  if supervisor:assert r['status']=='FAIL' and b"'fail' != 'pass'" in z.read(f'{trial}/out/stderr.bin')
  summary[trial]={'supervisor':supervisor,'overall_exit':exit_code,'old_task':'fail','fresh_task':'pass','fresh_recovery_ms':rec['elapsed_ms']}
 print(json.dumps({'status':'audited','results':summary},indent=2))
