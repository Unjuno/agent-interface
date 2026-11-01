"""Verify archived evidence and re-audit each saved real-X comparison."""
import hashlib,json,pathlib,subprocess,sys,tempfile,zipfile
root=pathlib.Path(__file__).resolve().parent;expected=json.loads((root/'archive-manifest.json').read_text())
with zipfile.ZipFile(root/'raw.zip') as z:
 names=z.namelist()
 if len(names)!=len(set(names)) or set(names)!=set(expected):raise RuntimeError('archive entries')
 for name in names:
  p=pathlib.PurePosixPath(name)
  if p.is_absolute() or '..' in p.parts:raise RuntimeError('unsafe archive path')
  if hashlib.sha256(z.read(name)).hexdigest()!=expected[name]:raise RuntimeError('digest mismatch '+name)
 for folder,count in [('idle-retire-serial-r119',96),('idle-cancel-retire-r122',97),('idle-cancel-retire-r123',7)]:
  for mode in ('normal','optimized'):
   p=folder+'/tests-'+mode+'/'
   if json.loads(z.read(p+'result.json'))['returncode']!=0 or ('Ran %d tests'%count).encode() not in z.read(p+'stderr'):raise RuntimeError(folder+' '+mode)
 failed='idle-retire-serial-r118/tests-normal/'
 if json.loads(z.read(failed+'result.json'))['returncode']==0 or b'FAILED (errors=6)' not in z.read(failed+'stderr'):raise RuntimeError('missing initial failure')
 race=json.loads(z.read('idle-retire-wake-r116/close-race-result.json'))
 if not race['second_terminate_before_first_finished'] or race['terminate_calls']!=2:raise RuntimeError('missing race')
 with tempfile.TemporaryDirectory(prefix='idle-retirement-audit-') as directory:
  z.extractall(directory);base=pathlib.Path(directory)
  for folder in ('idle-retire-wake-realx-r117','idle-retire-serial-realx-r120','idle-cancel-retire-realx-r124'):
   proc=subprocess.run([sys.executable,'-B',str(base/folder/'audit.py')],capture_output=True,text=True)
   if proc.returncode or json.loads(proc.stdout)['status']!='pass':raise RuntimeError(folder+' audit failed: '+proc.stdout+proc.stderr)
print(json.dumps({'status':'pass','entries':len(expected),'real_x_comparisons':3,'failed_initial_run_retained':True,'regression_modes':6}))
