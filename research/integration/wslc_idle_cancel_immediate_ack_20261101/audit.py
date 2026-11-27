"""Verify archive bytes and independently cross-check key saved fields."""
import hashlib,json,pathlib,subprocess,sys,tempfile,zipfile
root=pathlib.Path(__file__).resolve().parent
expected=json.loads((root/'archive-manifest.json').read_text())
with zipfile.ZipFile(root/'raw.zip') as z:
 names=z.namelist()
 if len(names)!=len(set(names)) or set(names)!=set(expected):raise RuntimeError('archive entry mismatch')
 for name in names:
  path=pathlib.PurePosixPath(name)
  if path.is_absolute() or '..' in path.parts:raise RuntimeError('unsafe path')
  if hashlib.sha256(z.read(name)).hexdigest()!=expected[name]:raise RuntimeError('digest mismatch '+name)
 for ident,mode in [('r105-control','control'),('r105-overlap','overlap')]:
  p='idle-held-ack-r105/'+ident+'/';c=json.loads(z.read(p+'conditions.json'));w=json.loads(z.read(p+'output/wrapper-result.json'));r=json.loads(z.read(p+'output/report.json'))
  if c['mode']!=mode or w['test_returncode']!=0 or w['xvfb_exit']!=0:raise RuntimeError(ident+' launcher')
  if r['cancel_control_ack_withheld']['withheld_ack_s']!=0.0 or r['input_before_cancel']['keys_down']!={'a':True,'b':False}:raise RuntimeError(ident+' precondition')
  cancel=r['cancel']
  if cancel['status']!='cancel_requested' or cancel['cleanup_status']!='UNKNOWN' or cancel['late_server_request_possible'] is not True or cancel['release_confirmed'] is not False:raise RuntimeError(ident+' cancellation')
  if r['independent_release_readback']['keys_down']!={'a':False,'b':False} or any(r['late_request_horizon_readback']['keys_down'].values()):raise RuntimeError(ident+' release')
  if r['independent_task_oracle']['status']!='pass' or r['fresh_session_recovery']['effect_count_oracle']['status']!='pass':raise RuntimeError(ident+' effects')
  overlap=r['held_input_idle_overlap']
  if mode=='control' and overlap['result']!='control_not_requested':raise RuntimeError('control')
  if mode=='overlap' and (overlap['result']!='refused' or overlap['idle_reserved'] is not False):raise RuntimeError('overlap')
 with tempfile.TemporaryDirectory(prefix='idle-ack-audit-') as directory:
  z.extractall(directory)
  p=subprocess.run([sys.executable,'-B',str(pathlib.Path(directory)/'idle-held-ack-r105'/'audit.py')],capture_output=True,text=True)
  if p.returncode or json.loads(p.stdout)['status']!='pass':raise RuntimeError('source audit failed '+p.stdout+p.stderr)
print(json.dumps({'status':'pass','entries':len(expected),'arms':2,'runtime_cleanup':'UNKNOWN'}))
