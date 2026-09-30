from pathlib import Path
import hashlib,json,tarfile,io
from PIL import Image
root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text())
with tarfile.open(root/'raw.tar.gz','r:gz') as tar:
 members={m.name:m for m in tar.getmembers()}
 assert set(members)==set(manifest['files'])
 def read(n): return tar.extractfile(members[n]).read()
 def data(n): return json.loads(read(n))
 for n,d in manifest['files'].items(): assert hashlib.sha256(read(n)).hexdigest()==d,n
 prefix='results-local/calc-png-live-pair-01/'
 freeze=data(prefix+'freeze.json')
 for n,h in freeze['files'].items(): assert hashlib.sha256(read(prefix+n)).hexdigest()==h
 for arm in ('baseline','candidate'):
  a=prefix+arm+'/'
  assert data(a+'loaded-sink.json')['sha256']==freeze['files'][arm+'/sink.py']
  e=data(a+'allocation/run/evaluation.json');assert e['success'] and e['actual']==[497,220]
  assert data(a+'action-4-metadata.json')['allocation']['returncode']==0
  names=[n for n in members if n.startswith(a+'allocation/run/bridge/public-dispatch-')]
  assert len(names)==2
  for n in names:
   r=data(n)['result'];assert r['status']=='completed'
   assert r['execution']['releases']
   assert all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in r['execution']['releases'])
 for label,expected in [('initial',True),('action-1',True),('action-2',False)]:
  with Image.open(io.BytesIO(read(prefix+'baseline/'+label+'.png'))) as a, Image.open(io.BytesIO(read(prefix+'candidate/'+label+'.png'))) as b:
   assert (a.size==b.size and a.convert('RGB').tobytes()==b.convert('RGB').tobytes())==expected
 print('PASS:',len(members),'files; both live outcomes, release and pixel comparisons retained')
