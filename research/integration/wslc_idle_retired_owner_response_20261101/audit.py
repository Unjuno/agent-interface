"""Verify archived bytes and the saved real-owner comparison."""
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
 probe=json.loads(z.read('idle-retire-r111/probe-result.json'))
 if probe['state_after_retire']!='failed' or probe['state_after_late_response']!='open' or probe['process_alive'] is not False:raise RuntimeError('simulated predecessor probe')
 for mode in ('normal','optimized'):
  p='idle-retire-r111/tests-'+mode+'/'
  if json.loads(z.read(p+'result.json'))['returncode']!=0 or b'Ran 94 tests' not in z.read(p+'stderr'):raise RuntimeError('regression '+mode)
 with tempfile.TemporaryDirectory(prefix='retired-owner-audit-') as directory:
  z.extractall(directory)
  proc=subprocess.run([sys.executable,'-B',str(pathlib.Path(directory)/'idle-retire-realx-r113'/'audit.py')],capture_output=True,text=True)
  if proc.returncode:raise RuntimeError('saved report audit failed: '+proc.stdout+proc.stderr)
  result=json.loads(proc.stdout)
  if result['status']!='pass' or len(result['rows'])!=2:raise RuntimeError('unexpected real-owner audit')
print(json.dumps({'status':'pass','entries':len(expected),'real_owner_arms':2,'test_modes':2,'old_cleanup':'UNKNOWN'}))
