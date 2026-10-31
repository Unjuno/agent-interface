from pathlib import Path
from zipfile import ZipFile
from collections import Counter
from PIL import Image
import hashlib,io,json,subprocess,sys,tempfile
here=Path(__file__).resolve().parent;scorer_hash=None
for name in ('aa01','aa02','aa03'):
 with ZipFile(here/(name+'.zip')) as z:
  read=lambda p:json.loads(z.read(p));h=lambda b:hashlib.sha256(b).hexdigest();c=read('conditions.json');r=read('output/result.json')
  assert c['allocation']==name and c['runner_sha256']==h(z.read('runner.py')) and c['scorer_sha256']==h(z.read('score.py')) and z.read('container.exit').decode('utf-8-sig').strip()=='0'
  if scorer_hash is None:scorer_hash=c['scorer_sha256']
  else:assert c['scorer_sha256']==scorer_hash
  assert r['model_calls']==0 and r['task_success'] is None
  def released(action):
   xs=action['execution']['releases'];return bool(xs) and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in xs)
  assert all(a['status']=='completed' and released(a) for a in r['actions'])
  close=r.get('close',r.get('finally_close'));assert close['status']=='closed' and close['release']['verified'] and not close['release']['keys_down'] and not close['release']['buttons_down']
  if name=='aa02':
   assert r['status']=='error' and 'target alias' in r['error'] and len(r['actions'])==2 and len([p for p in z.namelist() if p.startswith('output/benchmark/frame-') and p.endswith('.png')])==5 and 'output/benchmark/frames.json' not in z.namelist();print(name,'alias error; five partial images, no benchmark score');continue
  assert r['status']=='completed' and r['benchmark_frames']==20 and not r['keys_down_after'] and len(r['actions'])==(2 if name=='aa01' else 3)
  if name=='aa03':assert r['actions'][2]['execution']['waits'][0]['requested_ms']==80
  meta=read('output/benchmark/frames.json');assert len(meta)==20 and [x['index'] for x in meta]==list(range(20)) and all(a['tic']<b['tic'] for a,b in zip(meta,meta[1:]))
  with tempfile.TemporaryDirectory() as t:
   tmp=Path(t);(tmp/'score.py').write_bytes(z.read('score.py'));folder=tmp/'benchmark';folder.mkdir();(folder/'frames.json').write_bytes(z.read('output/benchmark/frames.json'))
   for row in meta:
    path=f"output/benchmark/frame-{row['index']:02d}.png";blob=z.read(path);assert h(blob)==row['sha256'] and Image.open(io.BytesIO(blob)).size==(640,480);(folder/Path(path).name).write_bytes(blob)
   run=subprocess.run([sys.executable,str(tmp/'score.py'),str(folder)],capture_output=True,text=True,check=True);actual=json.loads(run.stdout);expected=read('score.json');assert actual==expected and actual['status']=='completed'
   seed=actual['seed'];selected=[q for q in meta[0]['labels'] if q['name']=='Zombieman' and q['id']==seed['id']];assert len(selected)==1
   summary={method:dict(Counter(row[method]['outcome'] for row in actual['rows'])) for method in ('fixed','wide')}
   if name=='aa01':assert summary['fixed']=={'inside_target_box':20} and summary['wide']=={'inside_target_box':20}
   else:
    assert summary['fixed']=={'inside_target_box':5,'abstained':15} and summary['wide']=={'inside_target_box':20}
    before=next(q for q in meta[4]['labels'] if q['name']=='Zombieman' and q['id']==seed['id']);after=next(q for q in meta[5]['labels'] if q['name']=='Zombieman' and q['id']==seed['id']);assert after['x']-before['x']==30
   mutated=json.loads(json.dumps(meta))
   for row in mutated[1:]:row['labels']=[q for q in row['labels'] if not(q['name']=='Zombieman' and q['id']==seed['id'])]
   (folder/'frames.json').write_text(json.dumps(mutated));altered=json.loads(subprocess.run([sys.executable,str(tmp/'score.py'),str(folder)],capture_output=True,text=True,check=True).stdout)
   for original,changed in zip(actual['rows'],altered['rows']):
    for method in ('fixed','wide'):assert original[method]['point']==changed[method]['point']
   assert altered['rows'][5]['wide']['outcome']=='target_not_labeled' and actual['rows'][5]['wide']['outcome']=='inside_target_box'
   print(name,'score',summary,'future-label mutation preserved candidate points')
print('PASS: frame hashes, same-state-label scoring, input release and scorer label-separation mutation; no live semantic safety claim')
