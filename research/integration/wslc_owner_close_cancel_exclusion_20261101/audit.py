"""Verify archive bytes and re-audit close/cancel trials."""
import hashlib,json,pathlib,subprocess,sys,tempfile,zipfile
root=pathlib.Path(__file__).resolve().parent;expected=json.loads((root/'archive-manifest.json').read_text())
with zipfile.ZipFile(root/'raw.zip') as z:
 names=z.namelist()
 if len(names)!=len(set(names)) or set(names)!=set(expected):raise RuntimeError('archive entries')
 for name in names:
  p=pathlib.PurePosixPath(name)
  if p.is_absolute() or '..' in p.parts:raise RuntimeError('unsafe archive path')
  if hashlib.sha256(z.read(name)).hexdigest()!=expected[name]:raise RuntimeError('digest mismatch '+name)
 for mode in ('normal','optimized'):
  p='idle-close-cancel-r126/tests-'+mode+'/'
  if json.loads(z.read(p+'result.json'))['returncode']!=0 or b'Ran 99 tests' not in z.read(p+'stderr'):raise RuntimeError('regression '+mode)
 with tempfile.TemporaryDirectory(prefix='close-cancel-audit-') as directory:
  z.extractall(directory)
  proc=subprocess.run([sys.executable,'-B',str(pathlib.Path(directory)/'idle-close-cancel-realx-r127'/'audit.py')],capture_output=True,text=True)
  if proc.returncode:raise RuntimeError('saved report audit failed '+proc.stdout+proc.stderr)
  result=json.loads(proc.stdout)
  if result['status']!='pass' or len(result['rows'])!=2:raise RuntimeError('unexpected report audit')
print(json.dumps({'status':'pass','entries':len(expected),'real_owner_arms':2,'regression_modes':2}))
