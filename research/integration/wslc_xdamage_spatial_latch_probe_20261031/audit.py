from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
here=Path(__file__).resolve().parent
for name,mode in [('r01','clean'),('r02','draw'),('r03','overlay'),('r04','unrelated')]:
 with ZipFile(here/(name+'.zip')) as z:
  read=lambda p:json.loads(z.read(p));h=lambda b:hashlib.sha256(b).hexdigest();c=read('conditions.json');r=read('output/result.json')
  assert c['allocation']==name and c['mode']==mode and c['runner_sha256']==h(z.read('runner.py')) and c['model_calls']==0
  assert z.read('container.exit').decode('utf-8-sig').strip()=='0' and r['status']=='completed' and r['model_calls']==0
  witness=Image.open(io.BytesIO(z.read('output/witness.png'))).convert('RGB');assert witness.size==(8,8)
  if mode=='clean':assert (255,0,255) not in set(witness.getdata())
  else:assert set(witness.getdata())=={(255,0,255)}
  def obs(seq):
   names=[p for p in z.namelist() if '/owner/' in p and p.endswith(f'/observation-{seq}.json')];assert len(names)==1
   o=read(names[0]);a=o['native']['artifact'];assert a['path'].startswith('/out/');b=z.read('output/'+a['path'][5:]);assert h(b)==a['sha256'];return o,Image.open(io.BytesIO(b)).convert('RGB')
  source,image=obs(r['source_sequence']);x,y=r['point'];box=(x-4,y-4,x+4,y+4);old=image.crop(box).tobytes();assert len(old)==192
  assert r['change_started_ns']<=r['witness_ns']<=r['change_ended_ns'];checks=r['checks'];assert [q['label'] for q in checks]==['before','middle','endpoint']
  for q in checks:
   o,im=obs(q['sequence']);b=im.crop(box).tobytes();diff=sum(abs(a-b) for a,b in zip(old,b))/len(old);assert abs(diff-q['difference'])<1e-9 and diff==0 and q['binding_equal'] and not q['latched']
   if q['label']=='middle':assert o['capture_ns']>r['change_ended_ns']
  def intersects(e):
   ex,ey,ew,eh=e['area'];return e['damage']==r['damage_ids']['root'] and ex<box[2] and ex+ew>box[0] and ey<box[3] and ey+eh>box[1]
  events=r['damage_events'];relevant=[e for e in events if intersects(e)];assert relevant==r['relevant_damage'] and r['damage_latched']==bool(relevant) and r['eligible']==(not relevant) and not r['latched']
  if mode in ('clean','unrelated'):
   if mode=='clean':assert not events
   else:assert events and not relevant and any(e['stage']=='change' and e['damage']==r['damage_ids']['root'] for e in events)
   assert r['dispatch']=='completed' and [e['type'] for e in r['events']]==['press','release'] and all(e['keycode']==r['target_keycode'] for e in r['events'])
   rel=r['action']['execution']['releases'];assert rel and all(q['verified'] and not q['keys_down'] and not q['buttons_down'] for q in rel);assert r['close']['release']['verified']
  else:
   assert any(e['stage']=='change' for e in relevant) and r['dispatch']=='withheld' and r['events']==[] and 'action' not in r
  assert r['close']['status']=='closed' and not r['f_down_after']
  print(name,mode,'damage',len(events),'intersecting root rectangles',len(relevant),'dispatch',r['dispatch'])
print('PASS: retained witness, screen hashes, rectangle intersection, target events and release')
