from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
here=Path(__file__).resolve().parent
for name in ('k01','k02','k03'):
 with ZipFile(here/(name+'.zip')) as z:
  read=lambda p:json.loads(z.read(p));h=lambda b:hashlib.sha256(b).hexdigest();c=read('conditions.json');r=read('output/result.json')
  assert c['allocation']==name and c['runner_sha256']==h(z.read('runner.py')) and c['model_calls']==0 and c['threshold']==32
  assert z.read('container.exit').decode('utf-8-sig').strip()=='0' and r['status']=='completed' and r['model_calls']==0 and r['task_success'] is None
  assert len(r['actions'])==2
  def released(action):
   rows=action['execution']['releases'];return bool(rows) and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in rows)
  assert all(x['status']=='completed' and released(x) for x in r['actions'])
  assert r['close']['status']=='closed' and r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down'] and not r['keys_down_after']
  def obs(seq):
   names=[p for p in z.namelist() if '/owner/' in p and p.endswith(f'/observation-{seq}.json')];assert len(names)==1
   o=read(names[0]);a=o['native']['artifact'];assert a['path'].startswith('/out/');b=z.read('output/'+a['path'][5:]);assert h(b)==a['sha256'];return o,Image.open(io.BytesIO(b)).convert('RGB')
  source,image=obs(r['source_sequence']);x,y=r['point'];box=(x-4,y-4,x+4,y+4);initial=image.crop(box).tobytes();assert len(initial)==192
  checks=r['checks'];assert [q['label'] for q in checks]==['during-1','during-2','endpoint'];latched=False; rows=[]
  for q in checks:
   o,im=obs(q['sequence']);p=im.crop(box).tobytes();diff=sum(abs(a-b) for a,b in zip(initial,p))/len(initial);equal=o['pointer_binding']==source['pointer_binding'];bad=diff>32 or not equal;latched|=bad
   assert abs(diff-q['difference'])<1e-9 and q['binding_equal']==equal and q['bad']==bad and q['latched']==latched
   rows.append(round(diff,3))
  assert r['latched']==latched and r['latched_eligible']==(not latched) and r['endpoint_only_eligible']==(not checks[-1]['bad'])
  if name=='k01':assert r['dispatch']=='completed' and r['guarded_action']['status']=='completed' and released(r['guarded_action']) and r['endpoint_only_eligible'] and r['latched_eligible']
  else:
   assert r['overlay_mapped_ns']<checks[0]['t_ns']<checks[1]['t_ns']<r['overlay_removed_ns']<checks[2]['t_ns']
   assert r['dispatch']=='withheld' and 'guarded_action' not in r and not r['latched_eligible']
   if name=='k02':assert not r['endpoint_only_eligible']
   if name=='k03':assert r['endpoint_only_eligible'] and any(s['label']=='after-overlay-removal' for s in r['samples'])
  assert r['health_delta']==0 and r['kill_delta']==0
  print(name,'patch_MAD',rows,'endpoint_only',r['endpoint_only_eligible'],'latched',r['latched_eligible'],'dispatch',r['dispatch'],'health',r['health_delta'],'kills',r['kill_delta'])
print('PASS: images, sampled latch, bounded action and recorded releases; no semantic or continuous-coverage claim')
