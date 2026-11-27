"""Verify archived bytes and inspect saved held-input reports."""
import hashlib,json,pathlib,subprocess,sys,tempfile,zipfile
root=pathlib.Path(__file__).resolve().parent
expected=json.loads((root/'archive-manifest.json').read_text())
with zipfile.ZipFile(root/'raw.zip') as archive:
 names=archive.namelist()
 if len(names)!=len(set(names)) or set(names)!=set(expected):raise RuntimeError('archive entry mismatch')
 for name in names:
  p=pathlib.PurePosixPath(name)
  if p.is_absolute() or '..' in p.parts:raise RuntimeError('unsafe path')
  if hashlib.sha256(archive.read(name)).hexdigest()!=expected[name]:raise RuntimeError('digest mismatch '+name)
 with tempfile.TemporaryDirectory(prefix='rpc-evidence-audit-') as directory:
  archive.extractall(directory);base=pathlib.Path(directory)
  proc=subprocess.run([sys.executable,'-B',str(base/'idle-held-cancel-r103'/'audit.py')],capture_output=True,text=True)
  if proc.returncode:raise RuntimeError('saved report audit failed: '+proc.stdout+proc.stderr)
  result=json.loads(proc.stdout)
  if result['status']!='pass' or len(result['rows'])!=2:raise RuntimeError('unexpected held-input audit')
  for mode in ('normal','optimized'):
   p=base/'idle-rpc-overlap-r100'/('tests-'+mode)
   if json.loads((p/'result.json').read_text())['returncode']!=0 or 'Ran 90 tests' not in (p/'stderr').read_text():raise RuntimeError('regression '+mode)
  stress=json.loads((base/'idle-rpc-overlap-r100'/'stress-results.json').read_text())
  if stress['status']!='pass' or stress['iterations']!=200:raise RuntimeError('stress result')
  for mode in ('ordinary','idle'):
   r=json.loads((base/'idle-rpc-realx-r101'/('r101-'+mode)/'output'/'result.json').read_text())
   if r['status']!='passed' or not r['input_neutral'] or not r['release_verified']:raise RuntimeError('real owner '+mode)
print(json.dumps({'status':'pass','entries':len(expected),'held_input_arms':2,'real_owner_arms':2,'stress_iterations':200,'test_modes':2}))
