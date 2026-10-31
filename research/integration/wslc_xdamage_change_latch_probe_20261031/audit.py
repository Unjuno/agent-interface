from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
here=Path(__file__).resolve().parent
for name,mode in [('p01','clean'),('p02','draw'),('p03','overlay'),('p04','unrelated')]:
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
  events=r['damage_events'];assert r['damage_latched']==bool(events) and r['eligible']==(not events) and not r['latched']
  if mode=='clean':
   assert not events and r['dispatch']=='completed' and [e['type'] for e in r['events']]==['press','release'] and all(e['keycode']==r['target_keycode'] for e in r['events'])
   rel=r['action']['execution']['releases'];assert rel and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in rel);assert r['close']['release']['verified']
  else:
   assert events and r['dispatch']=='withheld' and r['events']==[] and 'action' not in r
   changed=[e for e in events if e['stage']=='change'];assert changed
   if mode=='draw':assert {r['damage_ids']['root'],r['damage_ids']['target']} <= {e['damage'] for e in changed}
   if mode=='overlay':assert r['damage_ids']['root'] in {e['damage'] for e in changed}
   if mode=='unrelated':
    root=[e for e in changed if e['damage']==r['damage_ids']['root']];assert root
    for e in root:
     ex,ey,ew,eh=e['area'];assert ex+ew<=box[0] or ex>=box[2] or ey+eh<=box[1] or ey>=box[3]
  assert r['close']['status']=='closed' and not r['f_down_after']
  print(name,mode,'change-stage notifications',sum(e['stage']=='change' for e in events),'all notifications',len(events),'dispatch',r['dispatch'])
print('PASS: witnesses, observation hashes, retained event records, latch, target input and release')
